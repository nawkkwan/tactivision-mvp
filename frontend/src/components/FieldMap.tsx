import type { CSSProperties, MouseEvent } from "react";
import type { Detection, PassType, Point2D, TargetMode } from "../types";

interface FieldMapProps {
  detections: Detection[];
  carrierId: string | null;
  candidateCarrierId: string | null;
  stage: number;
  targetMode: TargetMode;
  passType: PassType;
  targetPosition: Point2D | null;
  interceptPosition: Point2D | null;
  onDetectionClick: (detection: Detection) => void;
  onFieldClick: (point: Point2D) => void;
}

const markerColors = {
  team_a: "#50d9ff",
  team_b: "#ff5c67",
  unassigned: "#eaaf37",
} as const;

export function FieldMap({
  detections,
  carrierId,
  candidateCarrierId,
  stage,
  targetMode,
  passType,
  targetPosition,
  interceptPosition,
  onDetectionClick,
  onFieldClick,
}: FieldMapProps) {
  const mappedDetections = detections.filter(
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
  const carrier = mappedDetections.find((item) => item.id === carrierId && item.field_position);
  const canPickFieldPoint = stage === 5 && targetMode !== "receiver";
  const canPickPlayer = stage === 4 || (stage === 5 && targetMode === "receiver");

  function handlePitchClick(event: MouseEvent<HTMLDivElement>) {
    if (!canPickFieldPoint) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    onFieldClick({
      x: Math.min(105, Math.max(0, ((event.clientX - bounds.left) / bounds.width) * 105)),
      y: Math.min(68, Math.max(0, ((event.clientY - bounds.top) / bounds.height) * 68)),
    });
  }

  const flightStyle = carrier?.field_position && targetPosition
    ? ({
        left: `${(carrier.field_position.x / 105) * 100}%`,
        top: `${(carrier.field_position.y / 68) * 100}%`,
        "--target-left": `${(targetPosition.x / 105) * 100}%`,
        "--target-top": `${(targetPosition.y / 68) * 100}%`,
      } as CSSProperties)
    : undefined;

  return (
    <section className="field-map" aria-label="แผนผังตำแหน่งผู้เล่นบนสนามจริง 2 มิติ">
      <div className="field-map-heading">
        <div>
          <strong>แผนผังพิกัดสนามจริง (2D)</strong>
          <span>ขนาดมาตรฐาน 105 × 68 เมตร</span>
        </div>
        <small>{mappedDetections.length}/{detections.length} ตำแหน่งอยู่ในสนาม</small>
      </div>
      <div
        className={`field-map-pitch ${canPickFieldPoint ? "interactive" : ""}`}
        onClick={handlePitchClick}
        aria-label={canPickFieldPoint ? "คลิกเพื่อเลือกจุดส่งบอลบนแผนผังสนาม 2 มิติ" : undefined}
      >
        <span className="field-halfway" />
        <span className="field-center-circle" />
        <span className="field-box field-box-left" />
        <span className="field-box field-box-right" />
        <span className="field-reference-center" title="P12 · จุดกึ่งกลางสนาม">P12</span>
        {carrier?.field_position && targetPosition ? (
          <svg className="field-pass-overlay" viewBox="0 0 105 68" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <marker id="field-pass-arrow-ground" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
                <path d="M0,0 L5,2.5 L0,5 Z" fill="#10b981" />
              </marker>
              <marker id="field-pass-arrow-air" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
                <path d="M0,0 L5,2.5 L0,5 Z" fill="#eaaf37" />
              </marker>
            </defs>
            <line
              className={`field-pass-line pass-${passType}`}
              x1={carrier.field_position.x}
              y1={carrier.field_position.y}
              x2={targetPosition.x}
              y2={targetPosition.y}
              markerEnd={passType === "ground" ? "url(#field-pass-arrow-ground)" : "url(#field-pass-arrow-air)"}
            />
          </svg>
        ) : null}
        {flightStyle ? <span className="field-flight-ball" style={flightStyle} aria-hidden="true" /> : null}
        {targetPosition ? (
          <span
            className="field-pass-target"
            style={{ left: `${(targetPosition.x / 105) * 100}%`, top: `${(targetPosition.y / 68) * 100}%` }}
            title={`จุดรับบอล ${targetPosition.x.toFixed(1)}, ${targetPosition.y.toFixed(1)} ม.`}
          />
        ) : null}
        {interceptPosition ? (
          <span
            className="field-intercept-point"
            style={{ left: `${(interceptPosition.x / 105) * 100}%`, top: `${(interceptPosition.y / 68) * 100}%` }}
            title={`จุดเสี่ยงถูกสกัด ${interceptPosition.x.toFixed(1)}, ${interceptPosition.y.toFixed(1)} ม.`}
          >×</span>
        ) : null}
        {mappedDetections.map((detection) => {
          const position = detection.field_position!;
          const selected = detection.id === carrierId || detection.id === candidateCarrierId;
          const isGoalkeeper = detection.class_name === "goalkeeper";
          const color = detection.class_name === "ball"
            ? "#ffffff"
            : markerColors[detection.team_id ?? "unassigned"];
          if (detection.class_name === "ball") {
            return (
              <span
                className="field-detected-ball"
                key={detection.id}
                style={{ left: `${(position.x / 105) * 100}%`, top: `${(position.y / 68) * 100}%` }}
                title={`ตำแหน่งลูกบอล ${position.x.toFixed(1)}, ${position.y.toFixed(1)} ม.`}
              />
            );
          }
          return (
            <button
              type="button"
              className={`field-player-marker ${isGoalkeeper ? "goalkeeper" : ""} ${selected ? "selected" : ""}`}
              key={detection.id}
              disabled={!canPickPlayer}
              onClick={(event) => {
                event.stopPropagation();
                onDetectionClick(detection);
              }}
              style={{
                left: `${(position.x / 105) * 100}%`,
                top: `${(position.y / 68) * 100}%`,
                borderColor: color,
                backgroundColor: selected ? color : "#060d18",
              }}
              title={`${detection.id} · ${isGoalkeeper ? "ผู้รักษาประตู" : "ผู้เล่น"}: ${position.x.toFixed(1)}, ${position.y.toFixed(1)} ม.`}
            >
              {detection.id.toUpperCase()}{isGoalkeeper ? " GK" : ""}
            </button>
          );
        })}
      </div>
      <p>{targetMode === "space" && canPickFieldPoint
        ? "คลิกพื้นที่ว่างบนแผนผัง 2D เพื่อกำหนดจุดส่งบอล"
        : targetMode === "through_ball" && canPickFieldPoint
          ? "เลือกผู้วิ่งจากแผงด้านขวา แล้วคลิกจุดที่ต้องการให้วิ่งไปรับบอลบนแผนผัง 2D"
          : "จุด P12 ต้องอยู่กึ่งกลางสนามเสมอ เพื่อตรวจสอบว่าตำแหน่งของนักเตะสอดคล้องกับภาพการแข่งขันจริง"}</p>
    </section>
  );
}
