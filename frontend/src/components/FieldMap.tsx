import type { Detection } from "../types";

interface FieldMapProps {
  detections: Detection[];
  carrierId: string | null;
  candidateCarrierId: string | null;
}

const markerColors = {
  team_a: "#50d9ff",
  team_b: "#ff7d87",
  unassigned: "#f8d66d",
} as const;

export function FieldMap({ detections, carrierId, candidateCarrierId }: FieldMapProps) {
  const mappedPlayers = detections.filter(
    (item) =>
      item.field_position !== null &&
      item.class_name !== "referee" &&
      Number.isFinite(item.field_position.x) &&
      Number.isFinite(item.field_position.y) &&
      item.field_position.x >= 0 &&
      item.field_position.x <= 105 &&
      item.field_position.y >= 0 &&
      item.field_position.y <= 68,
  );

  return (
    <section className="field-map" aria-label="แผนที่ตำแหน่งผู้เล่นหลัง Calibration">
      <div className="field-map-heading">
        <div>
          <strong>2D POINT MAPPING</strong>
          <span>พิกัดสนาม 105 × 68 เมตร</span>
        </div>
        <small>{mappedPlayers.length}/{detections.length} จุดอยู่ในสนาม</small>
      </div>
      <div className="field-map-pitch">
        <span className="field-halfway" />
        <span className="field-center-circle" />
        <span className="field-box field-box-left" />
        <span className="field-box field-box-right" />
        <span className="field-reference-center" title="P12 · จุดกึ่งกลางสนาม">P12</span>
        {mappedPlayers.map((detection) => {
          const position = detection.field_position!;
          const selected = detection.id === carrierId || detection.id === candidateCarrierId;
          const color = detection.class_name === "ball"
            ? "#ffffff"
            : markerColors[detection.team_id ?? "unassigned"];
          return (
            <span
              className={`field-player-marker ${selected ? "selected" : ""}`}
              key={detection.id}
              style={{
                left: `${(position.x / 105) * 100}%`,
                top: `${(position.y / 68) * 100}%`,
                borderColor: color,
                backgroundColor: selected ? color : "#071512",
              }}
              title={`${detection.id}: ${position.x.toFixed(1)}, ${position.y.toFixed(1)} m`}
            >
              {detection.id.toUpperCase()}
            </span>
          );
        })}
      </div>
      <p>จุด P12 ต้องอยู่กึ่งกลางสนามเสมอ ใช้ตรวจว่าทิศและตำแหน่งของ Marker ตรงกับภาพต้นฉบับก่อนวิเคราะห์</p>
    </section>
  );
}
