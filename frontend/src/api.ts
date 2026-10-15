import type {
  CalibrationPair,
  DetectResponse,
  Detection,
  PassType,
  Point2D,
  SimulationParameters,
  SimulationResult,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? `เกิดข้อผิดพลาด (${response.status})`;
  } catch {
    return `เกิดข้อผิดพลาด (${response.status})`;
  }
}

export async function detectImage(file: File): Promise<DetectResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_URL}/detect`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as DetectResponse;
}

export async function calibrateImage(
  image: DetectResponse["image"],
  detections: Detection[],
  pairs: CalibrationPair[],
): Promise<{ calibration: DetectResponse["calibration"]; detections: Detection[] }> {
  const response = await fetch(`${API_URL}/calibrate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_width: image.width,
      image_height: image.height,
      correspondences: pairs.map(({ image: source, field }) => ({ image: source, field })),
      detections,
    }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as {
    calibration: DetectResponse["calibration"];
    detections: Detection[];
  };
}

export async function simulatePass(input: {
  detections: Detection[];
  carrierId: string;
  passType: PassType;
  target: { type: "receiver" | "space"; position: Point2D; receiver_id?: string };
  parameters: SimulationParameters;
}): Promise<SimulationResult> {
  const players = input.detections
    .filter(
      (item) =>
        (item.class_name === "player" || item.class_name === "goalkeeper") &&
        item.team_id !== null &&
        item.field_position !== null,
    )
    .map((item) => ({
      id: item.id,
      team_id: item.team_id,
      class_name: item.class_name,
      position: item.field_position,
    }));
  const response = await fetch(`${API_URL}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      players,
      ball_carrier_id: input.carrierId,
      pass_type: input.passType,
      target: input.target,
      parameters: input.parameters,
    }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as SimulationResult;
}

export { API_URL };

