from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import numpy as np


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


MIN_BEAM_LENGTH = 0.01
MIN_SECTION_DIMENSION = 0.001
MIN_ELASTIC_MODULUS = 1e6
MIN_SHEAR_MODULUS = 1e5
MIN_DISPLACEMENT_UM = -10000.0
MAX_DISPLACEMENT_UM = 10000.0
MIN_THRESHOLD = 1e-3


def validate_finite_positive(value: float, field_name: str, min_value: float) -> float:
    if not np.isfinite(value):
        raise ValueError(f"{field_name} must be finite, got {value}")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    if value < min_value:
        raise ValueError(
            f"{field_name} {value} is below minimum allowed value {min_value}"
        )
    return value


def validate_finite(value: float, field_name: str) -> float:
    if not np.isfinite(value):
        raise ValueError(f"{field_name} must be finite, got {value}")
    return value


class TenonNodeBase(BaseModel):
    id: str
    name: str
    x: float = Field(description="X coordinate in topology space")
    y: float = Field(description="Y coordinate in topology space")
    beam_length: float = Field(description="Beam length in meters")
    section_width: float = Field(description="Section width in meters")
    section_height: float = Field(description="Section height in meters")
    elastic_modulus: float = Field(description="Elastic modulus in Pascals")
    shear_modulus: float = Field(description="Shear modulus in Pascals")

    @field_validator("x", "y")
    @classmethod
    def validate_coordinates(cls, v: float, info) -> float:
        return validate_finite(v, info.field_name or "coordinate")

    @field_validator("beam_length")
    @classmethod
    def validate_beam_length(cls, v: float) -> float:
        return validate_finite_positive(v, "beam_length", MIN_BEAM_LENGTH)

    @field_validator("section_width", "section_height")
    @classmethod
    def validate_section_dimensions(cls, v: float, info) -> float:
        return validate_finite_positive(
            v, info.field_name or "section_dimension", MIN_SECTION_DIMENSION
        )

    @field_validator("elastic_modulus")
    @classmethod
    def validate_elastic_modulus(cls, v: float) -> float:
        return validate_finite_positive(v, "elastic_modulus", MIN_ELASTIC_MODULUS)

    @field_validator("shear_modulus")
    @classmethod
    def validate_shear_modulus(cls, v: float) -> float:
        return validate_finite_positive(v, "shear_modulus", MIN_SHEAR_MODULUS)


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

    @field_validator("displacement_um")
    @classmethod
    def validate_displacement(cls, v: float) -> float:
        if not np.isfinite(v):
            raise ValueError(f"displacement_um must be finite, got {v}")
        if v < MIN_DISPLACEMENT_UM or v > MAX_DISPLACEMENT_UM:
            raise ValueError(
                f"displacement_um {v}μm is outside valid range "
                f"[{MIN_DISPLACEMENT_UM}, {MAX_DISPLACEMENT_UM}]μm"
            )
        return v

    @model_validator(mode="after")
    def check_node_id_not_empty(self) -> "SensorData":
        if not self.node_id or not self.node_id.strip():
            raise ValueError("node_id cannot be empty")
        return self


class BatchSensorData(BaseModel):
    data: List[SensorData]

    @field_validator("data")
    @classmethod
    def check_data_not_empty(cls, v: List[SensorData]) -> List[SensorData]:
        if len(v) == 0:
            raise ValueError("Sensor data batch cannot be empty")
        if len(v) > 1000:
            raise ValueError(f"Batch size {len(v)} exceeds maximum of 1000")
        return v


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

    @field_validator("displacement_threshold", "shear_threshold", "moment_threshold")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        if not np.isfinite(v):
            raise ValueError(f"{info.field_name} must be finite, got {v}")
        if v < MIN_THRESHOLD:
            raise ValueError(
                f"{info.field_name} {v} is below minimum {MIN_THRESHOLD}"
            )
        if v > 1e9:
            raise ValueError(
                f"{info.field_name} {v} is above maximum 1e9"
            )
        return v

    @model_validator(mode="after")
    def check_threshold_ratios(self) -> "AlertRule":
        if self.displacement_threshold <= 0:
            raise ValueError("displacement_threshold must be positive")
        if self.shear_threshold <= 0:
            raise ValueError("shear_threshold must be positive")
        if self.moment_threshold <= 0:
            raise ValueError("moment_threshold must be positive")
        return self


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


class ErrorResponse(BaseModel):
    error: str
    error_type: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)
