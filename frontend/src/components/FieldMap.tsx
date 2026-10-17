import type { CSSProperties, MouseEvent } from "react";
import type { Comparison, Detection, Point2D, TargetMode } from "../types";

interface FieldMapProps {
  detections: Detection[];
  carrierId: string | null;
  candidateCarrierId: string | null;
  stage: number;
  targetMode: TargetMode;
  comparisons?: Comparison[];
  activeId?: string | null;
  onDetectionClick: (detection: Detection) => void;
  onFieldClick: (point: Point2D) => void;
}

const markerColors = {
  team_a: "#50d9ff",
  team_b: "#ff5c67",
  unassigned: "#eaaf37",
} as const;

const routeColors = ["#50d9ff", "#eaaf37", "#c084fc"] as const;

export function FieldMap({
  detections,
  carrierId,
  candidateCarrierId,
  stage,
  targetMode,
  comparisons = [],
  activeId = null,
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
  const activeComparison = comparisons.find((item) => item.id === activeId) ?? null;
  const canPickFieldPoint = stage === 5;
  const canPickPlayer = stage === 4 || stage === 5;

  function handlePitchClick(event: MouseEvent<HTMLDivElement>) {
    if (!canPickFieldPoint) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    onFieldClick({
      x: Math.min(105, Math.max(0, ((event.clientX - bounds.left) / bounds.width) * 105)),
      y: Math.min(68, Math.max(0, ((event.clientY - bounds.top) / bounds.height) * 68)),
    });
  }

  const flightStyle = carrier?.field_position && activeComparison
    ? ({
        left: `${(carrier.field_position.x / 105) * 100}%`,
        top: `${(carrier.field_position.y / 68) * 100}%`,
        "--target-left": `${(activeComparison.target.position.x / 105) * 100}%`,
        "--target-top": `${(activeComparison.target.position.y / 68) * 100}%`,
        "--route-color": routeColors[Math.max(0, comparisons.indexOf(activeComparison))] ?? routeColors[0],
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
        aria-label={canPickFieldPoint ? "คลิกผู้เล่นหรือพื้นที่ว่างเพื่อสร้างทางเลือกการส่งบอล" : undefined}
      >
        <span className="field-halfway" />
        <span className="field-center-circle" />
        <span className="field-box field-box-left" />
        <span className="field-box field-box-right" />
        <span className="field-reference-center" title="P12 · จุดกึ่งกลางสนาม">P12</span>

        {carrier?.field_position && comparisons.length > 0 ? (
          <svg className="field-pass-overlay" viewBox="0 0 105 68" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              {comparisons.map((comparison, index) => (
                <marker id={`field-pass-arrow-${comparison.id}`} key={comparison.id} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
                  <path d="M0,0 L5,2.5 L0,5 Z" fill={routeColors[index]} />
                </marker>
              ))}
            </defs>
            {comparisons.map((comparison, index) => (
              <line
                className={`field-pass-line pass-${comparison.result.pass_type} ${activeId === comparison.id ? "active" : ""}`}
                key={comparison.id}
                x1={carrier.field_position!.x}
                y1={carrier.field_position!.y}
                x2={comparison.target.position.x}
                y2={comparison.target.position.y}
                stroke={routeColors[index]}
                markerEnd={`url(#field-pass-arrow-${comparison.id})`}
              />
            ))}
          </svg>
        ) : null}

        {comparisons.map((comparison, index) => {
          const color = routeColors[index];
          const positionStyle = {
            left: `${(comparison.target.position.x / 105) * 100}%`,
            top: `${(comparison.target.position.y / 68) * 100}%`,
            "--route-color": color,
          } as CSSProperties;
          return (
            <span key={`route-${comparison.id}`}>
              <span className={`field-pass-target route-${index}`} style={positionStyle} />
              <span className="field-route-label" style={positionStyle}>{String.fromCharCode(65 + index)}</span>
              {comparison.result.intercept_point ? (
                <span
                  className="field-intercept-point"
                  style={{ left: `${(comparison.result.intercept_point.x / 105) * 100}%`, top: `${(comparison.result.intercept_point.y / 68) * 100}%`, color }}
                  title={`จุดเสี่ยงถูกสกัดของทางเลือก ${String.fromCharCode(65 + index)}`}
                >×</span>
              ) : null}
            </span>
          );
        })}

        {flightStyle ? <span className="field-flight-ball" style={flightStyle} aria-hidden="true" /> : null}

        {mappedDetections.map((detection) => {
          const position = detection.field_position!;
          const selected = detection.id === carrierId || detection.id === candidateCarrierId;
          const isGoalkeeper = detection.class_name === "goalkeeper";
          const color = detection.class_name === "ball" ? "#ffffff" : markerColors[detection.team_id ?? "unassigned"];
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
              onClick={(event) => { event.stopPropagation(); onDetectionClick(detection); }}
              style={{ left: `${(position.x / 105) * 100}%`, top: `${(position.y / 68) * 100}%`, borderColor: color, backgroundColor: selected ? color : "#060d18" }}
              title={`${detection.id} · ${isGoalkeeper ? "ผู้รักษาประตู" : "ผู้เล่น"}: ${position.x.toFixed(1)}, ${position.y.toFixed(1)} ม.`}
            >
              {detection.id.toUpperCase()}{isGoalkeeper ? " GK" : ""}
            </button>
          );
        })}
      </div>
      <p>{stage === 5
        ? targetMode === "through_ball"
          ? "เลือกผู้วิ่งในตั้งค่าขั้นสูง แล้วคลิกจุดที่ต้องการให้วิ่งไปรับบอล"
          : "คลิกเพื่อนร่วมทีมเพื่อส่งเข้าเท้า หรือคลิกพื้นที่ว่างเพื่อสร้างทางเลือกใหม่"
        : "จุด P12 ต้องอยู่กึ่งกลางสนามเสมอ เพื่อตรวจสอบว่าตำแหน่งของนักเตะสอดคล้องกับภาพการแข่งขันจริง"}</p>
    </section>
  );
}
