import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from contextlib import contextmanager
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "monitoring.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenon_nodes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        beam_length REAL NOT NULL,
        section_width REAL NOT NULL,
        section_height REAL NOT NULL,
        elastic_modulus REAL NOT NULL,
        shear_modulus REAL NOT NULL,
        displacement REAL DEFAULT 0,
        shear_force REAL DEFAULT 0,
        bending_moment REAL DEFAULT 0,
        stress_level TEXT DEFAULT 'normal',
        last_update TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS displacement_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT NOT NULL,
        displacement_um REAL NOT NULL,
        shear_force_n REAL NOT NULL,
        bending_moment_nm REAL NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (node_id) REFERENCES tenon_nodes(id)
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_displacement_node_time 
    ON displacement_records(node_id, timestamp)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_records (
        id TEXT PRIMARY KEY,
        node_id TEXT NOT NULL,
        node_name TEXT NOT NULL,
        level TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        value REAL NOT NULL,
        threshold REAL NOT NULL,
        timestamp TEXT NOT NULL,
        acknowledged INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_rules (
        node_id TEXT PRIMARY KEY,
        displacement_threshold REAL DEFAULT 500,
        shear_threshold REAL DEFAULT 5000,
        moment_threshold REAL DEFAULT 2000,
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_node TEXT NOT NULL,
        to_node TEXT NOT NULL,
        connection_type TEXT DEFAULT 'beam'
    )
    """)

    _seed_initial_data(cursor)
    conn.commit()
    conn.close()


def _seed_initial_data(cursor):
    cursor.execute("SELECT COUNT(*) FROM tenon_nodes")
    count = cursor.fetchone()[0]
    if count > 0:
        return

    nodes = [
        {
            "id": "node-base-left",
            "name": "左基座榫卯",
            "x": 120, "y": 420,
            "beam_length": 2.5,
            "section_width": 0.35,
            "section_height": 0.40,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-base-right",
            "name": "右基座榫卯",
            "x": 480, "y": 420,
            "beam_length": 2.5,
            "section_width": 0.35,
            "section_height": 0.40,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-col-left-bottom",
            "name": "左柱底榫卯",
            "x": 180, "y": 360,
            "beam_length": 3.0,
            "section_width": 0.30,
            "section_height": 0.30,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-col-right-bottom",
            "name": "右柱底榫卯",
            "x": 420, "y": 360,
            "beam_length": 3.0,
            "section_width": 0.30,
            "section_height": 0.30,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-col-left-top",
            "name": "左柱顶榫卯",
            "x": 180, "y": 200,
            "beam_length": 2.0,
            "section_width": 0.28,
            "section_height": 0.32,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-col-right-top",
            "name": "右柱顶榫卯",
            "x": 420, "y": 200,
            "beam_length": 2.0,
            "section_width": 0.28,
            "section_height": 0.32,
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
        },
        {
            "id": "node-beam-center",
            "name": "大梁中榫卯",
            "x": 300, "y": 160,
            "beam_length": 3.5,
            "section_width": 0.32,
            "section_height": 0.45,
            "elastic_modulus": 12.0e9,
            "shear_modulus": 0.75e9,
        },
        {
            "id": "node-roof-left",
            "name": "左檐角榫卯",
            "x": 100, "y": 100,
            "beam_length": 1.8,
            "section_width": 0.22,
            "section_height": 0.28,
            "elastic_modulus": 10.0e9,
            "shear_modulus": 0.62e9,
        },
        {
            "id": "node-roof-right",
            "name": "右檐角榫卯",
            "x": 500, "y": 100,
            "beam_length": 1.8,
            "section_width": 0.22,
            "section_height": 0.28,
            "elastic_modulus": 10.0e9,
            "shear_modulus": 0.62e9,
        },
        {
            "id": "node-tower-top",
            "name": "楼顶宝顶榫卯",
            "x": 300, "y": 40,
            "beam_length": 1.5,
            "section_width": 0.20,
            "section_height": 0.24,
            "elastic_modulus": 12.0e9,
            "shear_modulus": 0.75e9,
        },
    ]

    now = datetime.now().isoformat()
    for node in nodes:
        cursor.execute("""
        INSERT INTO tenon_nodes 
        (id, name, x, y, beam_length, section_width, section_height,
         elastic_modulus, shear_modulus, displacement, shear_force,
         bending_moment, stress_level, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node["id"], node["name"], node["x"], node["y"],
            node["beam_length"], node["section_width"], node["section_height"],
            node["elastic_modulus"], node["shear_modulus"],
            0.0, 0.0, 0.0, "normal", now
        ))

        cursor.execute("""
        INSERT INTO alert_rules (node_id, displacement_threshold, shear_threshold, moment_threshold)
        VALUES (?, ?, ?, ?)
        """, (node["id"], 500.0, 5000.0, 2000.0))

    connections = [
        ("node-base-left", "node-col-left-bottom", "column-base"),
        ("node-base-right", "node-col-right-bottom", "column-base"),
        ("node-col-left-bottom", "node-col-left-top", "column"),
        ("node-col-right-bottom", "node-col-right-top", "column"),
        ("node-col-left-top", "node-beam-center", "beam"),
        ("node-col-right-top", "node-beam-center", "beam"),
        ("node-col-left-top", "node-roof-left", "eave"),
        ("node-col-right-top", "node-roof-right", "eave"),
        ("node-roof-left", "node-tower-top", "roof-ridge"),
        ("node-roof-right", "node-tower-top", "roof-ridge"),
    ]

    for conn_data in connections:
        cursor.execute("""
        INSERT INTO connections (from_node, to_node, connection_type)
        VALUES (?, ?, ?)
        """, conn_data)

    base_time = datetime.now() - timedelta(hours=24)
    for node in nodes:
        for i in range(288):
            timestamp = base_time + timedelta(minutes=5 * i)
            import math
            import random
            base_disp = 50 + 30 * math.sin(i / 20.0)
            noise = random.gauss(0, 10)
            if node["id"] == "node-beam-center":
                base_disp += 100
            elif node["id"] == "node-tower-top":
                base_disp += 60

            disp = base_disp + noise

            bending_coeff = (node["beam_length"] ** 3) / (3 * node["elastic_modulus"] * (node["section_width"] * node["section_height"] ** 3) / 12)
            shear_coeff = (6.0 / 5.0) * node["beam_length"] / (node["shear_modulus"] * node["section_width"] * node["section_height"])
            displacement_m = disp * 1e-6
            force = displacement_m / (bending_coeff + shear_coeff)
            moment = force * node["beam_length"]

            cursor.execute("""
            INSERT INTO displacement_records 
            (node_id, displacement_um, shear_force_n, bending_moment_nm, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (
                node["id"], disp, force, moment,
                timestamp.isoformat()
            ))
