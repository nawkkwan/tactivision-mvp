interface TelemetryFrameProps {
  analyzed?: boolean;
  compact?: boolean;
  label?: string;
}

export function TelemetryFrame({ analyzed = false, compact = false, label }: TelemetryFrameProps) {
  return (
    <figure className={`telemetry-frame ${compact ? "compact" : ""}`}>
      <div className="telemetry-caption">
        <span>{label ?? (analyzed ? "หลังวิเคราะห์เส้นทาง" : "ภาพการแข่งขัน")}</span>
        <span>สนาม 105 × 68 ม.</span>
      </div>
      <div className="telemetry-image">
        <img src="/demo-pitch.svg" alt={analyzed ? "ตัวอย่างภาพฟุตบอลพร้อมเส้นทางวิเคราะห์" : "ตัวอย่างภาพการแข่งขันฟุตบอล"} />
        {analyzed ? (
          <svg className="telemetry-overlay" viewBox="0 0 1200 700" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <marker id="route-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" /></marker>
            </defs>
            <path d="M292 345Q480 260 720 320" className="route route-a" markerEnd="url(#route-arrow)" />
            <path d="M292 345Q520 390 890 460" className="route route-b" markerEnd="url(#route-arrow)" />
            <path d="M292 345Q600 155 975 230" className="route route-c" markerEnd="url(#route-arrow)" />
            <circle cx="292" cy="345" r="11" className="route-origin" />
            <g className="route-label label-a"><rect x="532" y="260" width="80" height="28" /><text x="545" y="279">A · 34/100</text></g>
            <g className="route-label label-b"><rect x="645" y="399" width="80" height="28" /><text x="658" y="418">B · 58/100</text></g>
            <g className="route-label label-c"><rect x="724" y="172" width="80" height="28" /><text x="737" y="191">C · 76/100</text></g>
            <path className="intercept" d="M744 324l18 18m0-18l-18 18" />
          </svg>
        ) : null}
      </div>
      <figcaption>{analyzed ? "ภาพตัวอย่างการแสดงเส้นทาง ไม่ใช่ผลการแข่งขันจริง" : "ภาพก่อนวิเคราะห์เส้นทาง"}</figcaption>
    </figure>
  );
}
