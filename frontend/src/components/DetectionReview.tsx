import type { Detection, PlayerClass, TeamId } from "../types";

interface DetectionReviewProps {
  detections: Detection[];
  onUpdate: (id: string, patch: Partial<Detection>) => void;
  onRemove: (id: string) => void;
}

const teamLabels: Record<TeamId, string> = {
  team_a: "ทีม A (สีฟ้า)",
  team_b: "ทีม B (สีแดง)",
  unassigned: "ยังไม่ระบุทีม",
};

export function DetectionReview({ detections, onUpdate, onRemove }: DetectionReviewProps) {
  const players = detections.filter((item) => item.class_name !== "ball");
  const balls = detections.filter((item) => item.class_name === "ball");
  return (
    <>
      <section className="ball-review" aria-label="ลูกบอลที่ตรวจพบ">
        <h3>ลูกบอลที่ตรวจพบ ({balls.length} ลูก)</h3>
        {balls.map((item) => (
          <article key={item.id} className="detection-row ball-detection-row">
            <div>
              <strong>{item.id.toUpperCase()}</strong>
              <small>ความมั่นใจ AI {Math.round(item.confidence * 100)}%</small>
            </div>
            <span>ลูกบอล</span>
            <button
              className="text-button danger"
              type="button"
              aria-label={`ลบลูกบอล ${item.id}`}
              onClick={() => onRemove(item.id)}
            >
              ลบออก
            </button>
          </article>
        ))}
        {balls.length === 0 ? <p className="muted">ไม่พบลููกบอลในภาพ — สามารถคลิกเลือกผู้เล่นครองบอลได้เองในขั้นตอนถัดไป</p> : null}
      </section>
      <div className="detection-list">
        {players.map((item) => (
          <article key={item.id} className="detection-row">
            <div>
              <strong>{item.id.toUpperCase()}</strong>
              <small>ความมั่นใจ AI {Math.round(item.confidence * 100)}%</small>
            </div>
            <label>
              <span className="sr-only">บทบาทของ {item.id}</span>
              <select
                value={item.class_name}
                onChange={(event) =>
                  onUpdate(item.id, { class_name: event.target.value as PlayerClass })
                }
              >
                <option value="player">ผู้เล่นทั่วไป</option>
                <option value="goalkeeper">ผู้รักษาประตู</option>
                <option value="referee">ผู้ตัดสิน</option>
              </select>
            </label>
            <label>
              <span className="sr-only">สังกัดทีมของ {item.id}</span>
              <select
                value={item.team_id ?? "unassigned"}
                disabled={item.class_name === "referee"}
                onChange={(event) =>
                  onUpdate(item.id, { team_id: event.target.value as TeamId })
                }
              >
                {Object.entries(teamLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>
            <button className="text-button danger" type="button" onClick={() => onRemove(item.id)}>
              ลบออก
            </button>
          </article>
        ))}
        {players.length === 0 ? <p className="muted">ยังไม่พบผู้เล่นในภาพ</p> : null}
      </div>
    </>
  );
}

