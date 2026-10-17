import type { Comparison } from "../types";

interface RiskResultsProps {
  comparisons: Comparison[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onClear: () => void;
}

const riskLabels = {
  low: "ความเสี่ยงต่ำ",
  medium: "ความเสี่ยงปานกลาง",
  high: "ความเสี่ยงสูง",
} as const;

const targetLabels = {
  receiver: "ส่งเข้าเท้าเพื่อน",
  space: "จ่ายเข้าพื้นที่ว่าง",
  through_ball: "แทงทะลุช่อง",
} as const;

const passTypeLabels = {
  ground: "ลูกเรียด",
  chip: "ลูกชิพ",
  long_ball: "ลูกเปิดยาว",
} as const;

export function RiskResults({ comparisons, activeId, onSelect, onClear }: RiskResultsProps) {
  return (
    <section className="results-section" aria-labelledby="results-title">
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">แผงเปรียบเทียบทางเลือกการจ่ายบอล</span>
          <h2 id="results-title">ผลลัพธ์การจำลองความเสี่ยง (เปรียบเทียบสูงสุด 3 ทางเลือก)</h2>
        </div>
        {comparisons.length > 0 ? (
          <button type="button" className="text-button" onClick={onClear}>ล้างทางเลือกทั้งหมด</button>
        ) : null}
      </div>
      <div className="result-grid">
        {[0, 1, 2].map((slot) => {
          const comparison = comparisons[slot];
          if (!comparison) {
            return (
              <div className="result-card empty-result" key={slot}>
                <span>ทางเลือก {String.fromCharCode(65 + slot)}</span>
                <p>เลือกผู้รับบอลหรือคลิกพื้นที่ว่างบนสนาม เพื่อสร้างการเปรียบเทียบ</p>
              </div>
            );
          }
          return (
            <button
              type="button"
              key={comparison.id}
              className={`result-card risk-${comparison.result.risk} ${activeId === comparison.id ? "result-active" : ""}`}
              onClick={() => onSelect(comparison.id)}
            >
              <div className="result-topline">
                <span className="result-slot-badge">ทางเลือก {String.fromCharCode(65 + slot)}</span>
                <div className="result-risk-badge">
                  <small>ความเสี่ยงถูกตัดบอล</small>
                  <strong>{comparison.result.risk_percent}%</strong>
                </div>
              </div>
              <h3>{comparison.targetLabel}</h3>
              <dl>
                <div><dt>รูปแบบการส่ง</dt><dd>{passTypeLabels[comparison.result.pass_type] ?? comparison.result.pass_type}</dd></div>
                <div><dt>เป้าหมาย</dt><dd>{targetLabels[comparison.target.type]}</dd></div>
                <div><dt>ระดับความเสี่ยง</dt><dd>{riskLabels[comparison.result.risk]}</dd></div>
                <div><dt>ระยะทาง</dt><dd>{comparison.result.pass_distance.toFixed(1)} ม.</dd></div>
                <div><dt>เวลาบอลเดินทาง</dt><dd>{comparison.result.ball_time.toFixed(2)} วินาที</dd></div>
                <div><dt>ผู้รับบอล</dt><dd>{comparison.result.receiver_id ? comparison.result.receiver_id.toUpperCase() : "พื้นที่ว่าง"}</dd></div>
              </dl>
              <p className="result-explanation">{comparison.result.explanation}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

