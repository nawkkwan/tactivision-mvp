export type TeamId = "team_a" | "team_b" | "unassigned";
export type PlayerClass = "player" | "goalkeeper" | "referee" | "ball";

export interface Point2D {
  x: number;
  y: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Detection {
  id: string;
  class_name: PlayerClass;
  confidence: number;
  bbox: BoundingBox;
  foot_pixel: Point2D;
  team_id: TeamId | null;
  team_confidence: number | null;
  field_position: Point2D | null;
}

export interface CalibrationResult {
  status: "success" | "needs_manual";
  method: "auto" | "manual" | "preset";
  confidence: number;
  reprojection_error: number | null;
  matrix: number[][] | null;
  message: string;
}

export interface DetectResponse {
  image: { width: number; height: number; fingerprint: string };
  detector: { model: string; mode: "generic" | "fine_tuned" };
  detections: Detection[];
  calibration: CalibrationResult;
}

export interface CalibrationPair {
  label: string;
  image: Point2D;
  field: Point2D;
}

export interface SimulationParameters {
  ball_speed: number;
  defender_speed: number;
  reaction_time: number;
  reach_radius: number;
  sample_step: number;
}

export interface SimulationResult {
  risk: "low" | "medium" | "high";
  risk_percent: number;
  pass_distance: number;
  ball_time: number;
  interceptor_id: string | null;
  intercept_point: Point2D | null;
  minimum_margin: number | null;
  interceptors: Array<{
    player_id: string;
    intercept_point: Point2D;
    time_margin: number;
    path_progress_ratio: number;
  }>;
  explanation: string;
  disclaimer: string;
}

export interface Comparison {
  id: string;
  targetLabel: string;
  targetPixel: Point2D;
  interceptPixel: Point2D | null;
  result: SimulationResult;
}

