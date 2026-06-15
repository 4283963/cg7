from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import uuid
import math

from .database import get_db
from .models import (
    TenonNode, SensorData, StressResult, HistoryPoint,
    AlertRule, AlertRecord, TopologyData, AlertLevel, AlertType, StressLevel
)
from .castigliano import CastiglianoEngine


class NodeService:
    @staticmethod
    def get_all_nodes() -> List[TenonNode]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenon_nodes ORDER BY y DESC, x")
        rows = cursor.fetchall()
        conn.close()
        return [TenonNode(**dict(row)) for row in rows]

    @staticmethod
    def get_node(node_id: str) -> Optional[TenonNode]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenon_nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return TenonNode(**dict(row))
        return None

    @staticmethod
    def get_node_history(
        node_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[HistoryPoint]:
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, displacement_um, shear_force_n, bending_moment_nm
            FROM displacement_records
            WHERE node_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (node_id, start_time.isoformat(), end_time.isoformat(), limit))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in reversed(rows):
            results.append(HistoryPoint(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                displacement_um=row["displacement_um"],
                shear_force_n=row["shear_force_n"],
                bending_moment_nm=row["bending_moment_nm"],
            ))
        return results

    @staticmethod
    def get_topology() -> TopologyData:
        nodes = NodeService.get_all_nodes()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connections")
        rows = cursor.fetchall()
        conn.close()
        connections = [dict(row) for row in rows]
        return TopologyData(nodes=nodes, connections=connections)


class StressCalculationService:
    @staticmethod
    def calculate_stress(
        node: TenonNode,
        displacement_um: float,
    ) -> Tuple[float, float, str]:
        shear_force, bending_moment = CastiglianoEngine.force_from_displacement(
            displacement_um=displacement_um,
            beam_length=node.beam_length,
            section_width=node.section_width,
            section_height=node.section_height,
            elastic_modulus=node.elastic_modulus,
            shear_modulus=node.shear_modulus,
        )

        rule = AlertService.get_rule(node.id)
        stress_level = CastiglianoEngine.calculate_stress_level(
            displacement_um=displacement_um,
            shear_force=shear_force,
            bending_moment=bending_moment,
            displacement_warning=rule.displacement_threshold * 0.6,
            displacement_danger=rule.displacement_threshold,
            shear_warning=rule.shear_threshold * 0.6,
            shear_danger=rule.shear_threshold,
            moment_warning=rule.moment_threshold * 0.6,
            moment_danger=rule.moment_threshold,
        )

        return shear_force, bending_moment, stress_level


class DataIngestionService:
    @staticmethod
    def ingest_sensor_data(data: SensorData) -> Optional[StressResult]:
        node = NodeService.get_node(data.node_id)
        if not node:
            return None

        timestamp = data.timestamp or datetime.now()
        shear_force, bending_moment, stress_level = StressCalculationService.calculate_stress(
            node, data.displacement_um
        )

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tenon_nodes
            SET displacement = ?, shear_force = ?, bending_moment = ?,
                stress_level = ?, last_update = ?
            WHERE id = ?
        """, (
            data.displacement_um, shear_force, bending_moment,
            stress_level, timestamp.isoformat(), data.node_id
        ))

        cursor.execute("""
            INSERT INTO displacement_records
            (node_id, displacement_um, shear_force_n, bending_moment_nm, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.node_id, data.displacement_um,
            shear_force, bending_moment, timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

        result = StressResult(
            node_id=data.node_id,
            displacement_um=data.displacement_um,
            shear_force_n=shear_force,
            bending_moment_nm=bending_moment,
            stress_level=stress_level,
            timestamp=timestamp,
        )

        AlertService.check_and_create_alerts(node.id, data.displacement_um, shear_force, bending_moment)

        return result

    @staticmethod
    def ingest_batch(data_list: List[SensorData]) -> List[StressResult]:
        results = []
        for data in data_list:
            result = DataIngestionService.ingest_sensor_data(data)
            if result:
                results.append(result)
        return results


class AlertService:
    @staticmethod
    def get_rule(node_id: str) -> AlertRule:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alert_rules WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return AlertRule(**dict(row))
        return AlertRule(node_id=node_id)

    @staticmethod
    def get_all_rules() -> List[AlertRule]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alert_rules")
        rows = cursor.fetchall()
        conn.close()
        return [AlertRule(**dict(row)) for row in rows]

    @staticmethod
    def update_rule(node_id: str, rule: AlertRule) -> Optional[AlertRule]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alert_rules
            SET displacement_threshold = ?, shear_threshold = ?,
                moment_threshold = ?, updated_at = ?
            WHERE node_id = ?
        """, (
            rule.displacement_threshold, rule.shear_threshold,
            rule.moment_threshold, datetime.now().isoformat(), node_id
        ))
        conn.commit()

        cursor.execute("SELECT * FROM alert_rules WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return AlertRule(**dict(row))
        return None

    @staticmethod
    def check_and_create_alerts(
        node_id: str,
        displacement_um: float,
        shear_force: float,
        bending_moment: float,
    ) -> List[AlertRecord]:
        node = NodeService.get_node(node_id)
        if not node:
            return []

        rule = AlertService.get_rule(node_id)
        alerts = []

        if abs(displacement_um) >= rule.displacement_threshold:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.DANGER, AlertType.DISPLACEMENT,
                abs(displacement_um), rule.displacement_threshold
            )
            alerts.append(alert)
        elif abs(displacement_um) >= rule.displacement_threshold * 0.6:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.WARNING, AlertType.DISPLACEMENT,
                abs(displacement_um), rule.displacement_threshold * 0.6
            )
            alerts.append(alert)

        if abs(shear_force) >= rule.shear_threshold:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.DANGER, AlertType.SHEAR,
                abs(shear_force), rule.shear_threshold
            )
            alerts.append(alert)
        elif abs(shear_force) >= rule.shear_threshold * 0.6:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.WARNING, AlertType.SHEAR,
                abs(shear_force), rule.shear_threshold * 0.6
            )
            alerts.append(alert)

        if abs(bending_moment) >= rule.moment_threshold:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.DANGER, AlertType.MOMENT,
                abs(bending_moment), rule.moment_threshold
            )
            alerts.append(alert)
        elif abs(bending_moment) >= rule.moment_threshold * 0.6:
            alert = AlertService._create_alert(
                node_id, node.name, AlertLevel.WARNING, AlertType.MOMENT,
                abs(bending_moment), rule.moment_threshold * 0.6
            )
            alerts.append(alert)

        return alerts

    @staticmethod
    def _create_alert(
        node_id: str, node_name: str, level: AlertLevel,
        alert_type: AlertType, value: float, threshold: float,
    ) -> AlertRecord:
        alert_id = str(uuid.uuid4())
        now = datetime.now()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alert_records
            (id, node_id, node_name, level, alert_type, value, threshold, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id, node_id, node_name, level.value,
            alert_type.value, value, threshold, now.isoformat()
        ))
        conn.commit()
        conn.close()

        return AlertRecord(
            id=alert_id,
            node_id=node_id,
            node_name=node_name,
            level=level,
            alert_type=alert_type,
            value=value,
            threshold=threshold,
            timestamp=now,
            acknowledged=False,
        )

    @staticmethod
    def get_alerts(
        limit: int = 50,
        level: Optional[str] = None,
        acknowledged: Optional[bool] = None,
    ) -> List[AlertRecord]:
        conn = get_db()
        cursor = conn.cursor()

        query = "SELECT * FROM alert_records WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)
        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(1 if acknowledged else 0)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [AlertRecord(**dict(row)) for row in rows]

    @staticmethod
    def acknowledge_alert(alert_id: str) -> Optional[AlertRecord]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alert_records SET acknowledged = 1 WHERE id = ?
        """, (alert_id,))
        conn.commit()

        cursor.execute("SELECT * FROM alert_records WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return AlertRecord(**dict(row))
        return None
