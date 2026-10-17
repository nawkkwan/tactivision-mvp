import type { Detection } from "../types";

interface FieldMapProps {
  detections: Detection[];
  carrierId: string | null;
  candidateCarrierId: string | null;
}

const markerColors = {
  team_a: "#50d9ff",
  team_b: "#ff5c67",
  unassigned: "#eaaf37",
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
    <section className="field-map" aria-label="แผนผังตำแหน่งผู้เล่นบนสนามจริง 2 มิติ">
      <div className="field-map-heading">
        <div>
          <strong>แผนผังพิกัดสนามจริง (2D)</strong>
          <span>ขนาดมาตรฐาน 105 × 68 เมตร</span>
        </div>
        <small>{mappedPlayers.length}/{detections.length} ตำแหน่งอยู่ในสนาม</small>
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
                backgroundColor: selected ? color : "#060d18",
              }}
              title={`${detection.id}: ${position.x.toFixed(1)}, ${position.y.toFixed(1)} ม.`}
            >
              {detection.id.toUpperCase()}
            </span>
          );
        })}
      </div>
      <p>จุด P12 ต้องอยู่กึ่งกลางสนามเสมอ เพื่อตรวจสอบว่าตำแหน่งของนักเตะสอดคล้องกับภาพการแข่งขันจริง</p>
    </section>
  );
}
