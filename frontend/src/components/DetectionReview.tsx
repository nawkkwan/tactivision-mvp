import type { Detection, PlayerClass, TeamId } from "../types";

interface DetectionReviewProps {
  detections: Detection[];
  onUpdate: (id: string, patch: Partial<Detection>) => void;
  onRemove: (id: string) => void;
}

const teamLabels: Record<TeamId, string> = {
  team_a: "Team A",
  team_b: "Team B",
  unassigned: "ยังไม่กำหนด",
};

export function DetectionReview({ detections, onUpdate, onRemove }: DetectionReviewProps) {
  const players = detections.filter((item) => item.class_name !== "ball");
  const balls = detections.filter((item) => item.class_name === "ball");
  return (
    <>
      <section className="ball-review" aria-label="ลูกบอลที่ตรวจพบ">
        <h3>ลูกบอลที่ตรวจพบ ({balls.length})</h3>
        {balls.map((item) => (
          <article key={item.id} className="detection-row ball-detection-row">
            <div>
              <strong>{item.id}</strong>
              <small>ความมั่นใจ {Math.round(item.confidence * 100)}%</small>
            </div>
            <span>ลูกบอล</span>
            <button
              className="text-button danger"
              type="button"
              aria-label={`ลบลูกบอล ${item.id}`}
              onClick={() => onRemove(item.id)}
            >
              ลบ
            </button>
          </article>
        ))}
        {balls.length === 0 ? <p className="muted">ไม่มีลูกบอลที่ตรวจพบ สามารถเลือกคนครองบอลเองได้</p> : null}
      </section>
      <div className="detection-list">
        {players.map((item) => (
          <article key={item.id} className="detection-row">
            <div>
              <strong>{item.id}</strong>
              <small>ความมั่นใจ {Math.round(item.confidence * 100)}%</small>
            </div>
            <label>
              <span className="sr-only">คลาสของ {item.id}</span>
              <select
                value={item.class_name}
                onChange={(event) =>
                  onUpdate(item.id, { class_name: event.target.value as PlayerClass })
                }
              >
                <option value="player">Player</option>
                <option value="goalkeeper">Goalkeeper</option>
                <option value="referee">Referee</option>
              </select>
            </label>
            <label>
              <span className="sr-only">ทีมของ {item.id}</span>
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
              ลบ
            </button>
          </article>
        ))}
        {players.length === 0 ? <p className="muted">ยังไม่พบผู้เล่นในภาพ</p> : null}
      </div>
    </>
  );
}

