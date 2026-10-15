from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TeamId(str, Enum):
    TEAM_A = "team_a"
    TEAM_B = "team_b"
    UNASSIGNED = "unassigned"


class Point2D(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class Detection(BaseModel):
    id: str
    class_name: Literal["player", "goalkeeper", "referee", "ball"]
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox
    foot_pixel: Point2D
    team_id: TeamId | None = None
    team_confidence: float | None = Field(default=None, ge=0, le=1)
    field_position: Point2D | None = None


class CalibrationResult(BaseModel):
    status: Literal["success", "needs_manual"]
    method: Literal["auto", "manual", "preset"]
    confidence: float = Field(ge=0, le=1)
    reprojection_error: float | None = None
    matrix: list[list[float]] | None = None
    message: str


class ImageMetadata(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fingerprint: str


class DetectorMetadata(BaseModel):
    model: str
    mode: Literal["generic", "fine_tuned"]


class DetectResponse(BaseModel):
    image: ImageMetadata
    detector: DetectorMetadata
    detections: list[Detection]
    calibration: CalibrationResult


class CalibrationPair(BaseModel):
    image: Point2D
    field: Point2D


class CalibrateRequest(BaseModel):
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    correspondences: list[CalibrationPair] = Field(min_length=4)
    detections: list[Detection]


class CalibrateResponse(BaseModel):
    calibration: CalibrationResult
    detections: list[Detection]


class SimulationPlayer(BaseModel):
    id: str
    team_id: TeamId
    class_name: Literal["player", "goalkeeper"] = "player"
    position: Point2D


class SimulationTarget(BaseModel):
    type: Literal["receiver", "space", "through_ball"]
    position: Point2D
    receiver_id: str | None = None

    @model_validator(mode="after")
    def player_target_requires_id(self) -> "SimulationTarget":
        if self.type in {"receiver", "through_ball"} and not self.receiver_id:
            raise ValueError("receiver and through_ball targets require receiver_id")
        return self


class SimulationParameters(BaseModel):
    ball_speed: float = Field(default=18, gt=0, le=60)
    chip_speed: float = Field(default=14, gt=0, le=40)
    chip_apex_height: float = Field(default=3, ge=1, le=8)
    long_ball_speed: float = Field(default=15.8, gt=0, le=40)
    long_ball_apex_height: float = Field(default=3.8, ge=1, le=10)
    defender_speed: float = Field(default=7, gt=0, le=15)
    attacker_speed: float = Field(default=7, gt=0, le=15)
    reaction_time: float = Field(default=0.3, ge=0, le=3)
    reach_radius: float = Field(default=1, ge=0, le=3)
    sample_step: float = Field(default=0.5, gt=0.05, le=5)


class SimulateRequest(BaseModel):
    players: list[SimulationPlayer] = Field(min_length=2)
    ball_carrier_id: str
    pass_type: Literal["ground", "chip", "long_ball"] = "ground"
    target: SimulationTarget
    parameters: SimulationParameters = Field(default_factory=SimulationParameters)


class SimulationInterceptor(BaseModel):
    player_id: str
    intercept_point: Point2D
    time_margin: float
    path_progress_ratio: float = Field(ge=0, le=1)
    ball_height: float = Field(ge=0)
    ball_time: float = Field(ge=0)
    defender_time: float = Field(ge=0)
    teammate_id: str | None = None
    teammate_time: float | None = Field(default=None, ge=0)
    ball_time_margin: float
    teammate_time_margin: float | None = None


class SimulateResponse(BaseModel):
    pass_type: Literal["ground", "chip", "long_ball"]
    risk: Literal["low", "medium", "high"]
    risk_percent: int = Field(ge=0, le=100)
    pass_distance: float
    ball_time: float
    interceptor_id: str | None
    intercept_point: Point2D | None
    minimum_margin: float | None
    receiver_id: str | None = None
    receiver_arrival_time: float | None = Field(default=None, ge=0)
    receiver_ball_margin: float | None = None
    interceptors: list[SimulationInterceptor] = Field(default_factory=list)
    explanation: str
    disclaimer: str = (
        "เปอร์เซ็นต์นี้เป็นดัชนีความเสี่ยงจากแบบจำลองตามสมมติฐาน "
        "ไม่ใช่ความน่าจะเป็นที่วัดจากข้อมูลการแข่งขันจริง; แทงทะลุช่องสมมติว่าผู้รับวิ่งตรงไปยังจุดที่ผู้ใช้เลือก "
        "และลูกเปิดยาวใช้ความเร็วคงที่กับวิถีพาราโบลาประมาณการ ไม่จำลองแรงต้านอากาศหรือสปิน"
    )

