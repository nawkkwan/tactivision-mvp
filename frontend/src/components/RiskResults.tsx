import type { Comparison } from "../types";

interface RiskResultsProps {
  comparisons: Comparison[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onClear: () => void;
}

const riskLabels = { low: "LOW", medium: "MEDIUM", high: "HIGH" } as const;

export function RiskResults({ comparisons, activeId, onSelect, onClear }: RiskResultsProps) {
  return (
    <section className="results-section" aria-labelledby="results-title">
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">PASS OPTIONS</span>
          <h2 id="results-title">เปรียบเทียบทางเลือก</h2>
        </div>
        {comparisons.length > 0 ? (
          <button type="button" className="text-button" onClick={onClear}>ล้างผล</button>
        ) : null}
      </div>
      <div className="result-grid">
        {[0, 1, 2].map((slot) => {
          const comparison = comparisons[slot];
          if (!comparison) {
            return (
              <div className="result-card empty-result" key={slot}>
                <span>{String.fromCharCode(65 + slot)}</span>
                <p>เลือกผู้รับหรือพื้นที่ว่าง</p>
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
                <span>{String.fromCharCode(65 + slot)}</span>
                <strong>{riskLabels[comparison.result.risk]}</strong>
              </div>
              <h3>{comparison.targetLabel}</h3>
              <dl>
                <div><dt>ระยะ</dt><dd>{comparison.result.pass_distance.toFixed(1)} m</dd></div>
                <div><dt>เวลาบอล</dt><dd>{comparison.result.ball_time.toFixed(2)} s</dd></div>
              </dl>
              <p>{comparison.result.explanation}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

