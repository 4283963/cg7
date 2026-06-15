from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class StressLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    DANGER = "danger"


class AlertType(str, Enum):
    DISPLACEMENT = "displacement"
    SHEAR = "shear"
    MOMENT = "moment"


class AlertLevel(str, Enum):
    WARNING = "warning"
    DANGER = "danger"


class TenonNodeBase(BaseModel):
    id: str
    name: str
    x: float
    y: float
    beam_length: float = Field(description="Beam length in meters")
    section_width: float = Field(description="Section width in meters")
    section_height: float = Field(description="Section height in meters")
    elastic_modulus: float = Field(description="Elastic modulus in Pascals")
    shear_modulus: float = Field(description="Shear modulus in Pascals")


class TenonNode(TenonNodeBase):
    displacement: float = 0.0
    shear_force: float = 0.0
    bending_moment: float = 0.0
    stress_level: StressLevel = StressLevel.NORMAL
    last_update: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class SensorData(BaseModel):
    node_id: str
    displacement_um: float = Field(description="Relative displacement in micrometers")
    timestamp: Optional[datetime] = None


class BatchSensorData(BaseModel):
    data: List[SensorData]


class StressResult(BaseModel):
    node_id: str
    displacement_um: float
    shear_force_n: float
    bending_moment_nm: float
    stress_level: StressLevel
    timestamp: datetime


class HistoryPoint(BaseModel):
    timestamp: datetime
    displacement_um: float
    shear_force_n: float
    bending_moment_nm: float


class AlertRule(BaseModel):
    node_id: str
    displacement_threshold: float = 500.0
    shear_threshold: float = 5000.0
    moment_threshold: float = 2000.0


class AlertRecord(BaseModel):
    id: str
    node_id: str
    node_name: str
    level: AlertLevel
    alert_type: AlertType
    value: float
    threshold: float
    timestamp: datetime
    acknowledged: bool = False


class TopologyData(BaseModel):
    nodes: List[TenonNode]
    connections: List[dict]


class RealtimeUpdate(BaseModel):
    type: str = "realtime_update"
    nodes: List[TenonNode]
    alerts: List[AlertRecord] = []
