import type { DetectResponse, Detection } from "./types";

const matrix = [
  [105 / 1080, 0, -(60 * 105) / 1080],
  [0, 68 / 600, -(50 * 68) / 600],
  [0, 0, 1],
];

function player(
  id: string,
  x: number,
  y: number,
  team: "team_a" | "team_b",
): Detection {
  const foot = { x: x + 19, y: y + 70 };
  return {
    id,
    class_name: "player",
    confidence: 0.96,
    bbox: { x, y, width: 38, height: 70 },
    foot_pixel: foot,
    team_id: team,
    team_confidence: 0.92,
    field_position: {
      x: Number(((foot.x - 60) * (105 / 1080)).toFixed(3)),
      y: Number(((foot.y - 50) * (68 / 600)).toFixed(3)),
    },
  };
}

export const demoAnalysis: DetectResponse = {
  image: { width: 1200, height: 700, fingerprint: "sample-scene" },
  detector: { model: "sample-fixture.json", mode: "generic" },
  detections: [
    player("p1", 255, 285, "team_a"),
    player("p2", 420, 210, "team_a"),
    player("p3", 510, 415, "team_a"),
    player("p4", 725, 250, "team_a"),
    player("p5", 890, 390, "team_a"),
    player("p6", 380, 355, "team_b"),
    player("p7", 565, 270, "team_b"),
    player("p8", 660, 370, "team_b"),
    player("p9", 810, 185, "team_b"),
    player("p10", 960, 300, "team_b"),
    {
      id: "b1",
      class_name: "ball",
      confidence: 1,
      bbox: { x: 284, y: 337, width: 16, height: 16 },
      foot_pixel: { x: 292, y: 345 },
      team_id: null,
      team_confidence: null,
      field_position: { x: 22.556, y: 33.433 },
    },
  ],
  calibration: {
    status: "success",
    method: "preset",
    confidence: 1,
    reprojection_error: 0,
    matrix,
    message: "ใช้ Calibration ที่ตรวจสอบแล้วสำหรับฉากตัวอย่าง",
  },
};

