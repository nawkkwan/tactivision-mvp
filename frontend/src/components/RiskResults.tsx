import { useRef, useState } from "react";
import type { Comparison } from "../types";

interface RiskResultsProps {
  comparisons: Comparison[];
  activeId: string | null;
  pendingSlot: number | null;
  onSelect: (id: string) => void;
  onClear: () => void;
}

const riskLabels = {
  low: "ความเสี่ยงต่ำ",
  medium: "ความเสี่ยงปานกลาง",
  high: "ความเสี่ยงสูง",
} as const;

const passTypeLabels = {
  ground: "ลูกเรียด",
  chip: "ลูกชิพ",
  long_ball: "ลูกเปิดยาว",
} as const;

export function RiskResults({ comparisons, activeId, pendingSlot, onSelect, onClear }: RiskResultsProps) {
  const reportRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState<"image" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const activeComparison = comparisons.find((item) => item.id === activeId) ?? null;
  const lowestScore = comparisons.length > 0 ? Math.min(...comparisons.map((item) => item.result.risk_percent)) : null;
  const isComplete = comparisons.length === 3;

  async function createReportImage() {
    if (!reportRef.current || !isComplete || pendingSlot !== null) {
      throw new Error("กรุณารอให้ผลเปรียบเทียบ A, B และ C คำนวณครบก่อน");
    }
    const [{ toPng }] = await Promise.all([import("html-to-image"), document.fonts.ready]);
    return toPng(reportRef.current, {
      backgroundColor: "#ffffff",
      cacheBust: true,
      pixelRatio: 2,
      filter: (node) => !(node instanceof HTMLElement && node.dataset.exportIgnore === "true"),
    });
  }

  function reportFilename(extension: "png" | "pdf") {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `tactivision-abc-${timestamp}.${extension}`;
  }

  function downloadFile(url: string, filename: string) {
    const link = document.createElement("a");
    link.download = filename;
    link.href = url;
    link.click();
  }

  async function exportImage() {
    setExporting("image");
    setExportError(null);
    try {
      downloadFile(await createReportImage(), reportFilename("png"));
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "ส่งออกภาพไม่สำเร็จ");
    } finally {
      setExporting(null);
    }
  }

  async function exportPdf() {
    setExporting("pdf");
    setExportError(null);
    try {
      const [{ jsPDF }, image] = await Promise.all([import("jspdf"), createReportImage()]);
      const dimensions = await new Promise<{ width: number; height: number }>((resolve, reject) => {
        const preview = new Image();
        preview.onload = () => resolve({ width: preview.naturalWidth, height: preview.naturalHeight });
        preview.onerror = () => reject(new Error("เตรียมภาพสำหรับ PDF ไม่สำเร็จ"));
        preview.src = image;
      });
      const orientation = dimensions.width >= dimensions.height ? "landscape" : "portrait";
      const pdf = new jsPDF({ orientation, unit: "mm", format: "a4" });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 8;
      const scale = Math.min(
        (pageWidth - margin * 2) / dimensions.width,
        (pageHeight - margin * 2) / dimensions.height,
      );
      const width = dimensions.width * scale;
      const height = dimensions.height * scale;
      pdf.addImage(image, "PNG", (pageWidth - width) / 2, (pageHeight - height) / 2, width, height);
      pdf.save(reportFilename("pdf"));
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "ส่งออก PDF ไม่สำเร็จ");
    } finally {
      setExporting(null);
    }
  }

  return (
    <aside className="board-results" aria-labelledby="board-results-title">
      <div ref={reportRef} className="board-export-report">
        <div className="board-results-heading">
          <div>
            <span className="eyebrow">TactiVision · เปรียบเทียบในสนามเดียวกัน</span>
            <h2 id="board-results-title">ทางเลือก A / B / C</h2>
          </div>
          {comparisons.length > 0 ? (
            <button type="button" className="text-button" data-export-ignore="true" onClick={onClear}>ล้างทั้งหมด</button>
          ) : null}
        </div>

        <div className="board-result-list">
          {[0, 1, 2].map((slot) => {
            const comparison = comparisons[slot];
            const slotLabel = String.fromCharCode(65 + slot);
            const pending = pendingSlot === slot;
            if (!comparison) {
              return (
                <div className={`board-result-card empty ${pending ? "pending" : ""}`} key={slot}>
                  <span className={`route-swatch route-${slot}`}>{slotLabel}</span>
                  <div>
                    <strong>{pending ? "กำลังคำนวณทางเลือก…" : `ทางเลือก ${slotLabel}`}</strong>
                    <small>{pending ? "สนามยังใช้งานและดูข้อมูลอื่นได้" : "คลิกผู้เล่นหรือพื้นที่ว่างบนสนาม"}</small>
                  </div>
                </div>
              );
            }
            const lowest = comparison.result.risk_percent === lowestScore;
            return (
              <button
                type="button"
                key={comparison.id}
                className={`board-result-card risk-${comparison.result.risk} ${activeId === comparison.id ? "active" : ""} ${pending ? "pending" : ""}`}
                onClick={() => onSelect(comparison.id)}
              >
                <span className={`route-swatch route-${slot}`}>{slotLabel}</span>
                <span className="board-result-summary">
                  <strong>{comparison.targetLabel}</strong>
                  <small>{passTypeLabels[comparison.result.pass_type]} · {riskLabels[comparison.result.risk]}</small>
                  <small>ระยะ {comparison.result.pass_distance.toFixed(1)} ม. · เวลาบอล {comparison.result.ball_time.toFixed(2)} วิ.</small>
                  {lowest ? <em>เสี่ยงถูกสกัดต่ำสุดในชุดนี้</em> : null}
                </span>
                <span className="risk-score"><strong>{comparison.result.risk_percent}</strong><small>/100</small></span>
                {pending ? <span className="result-pending-label">กำลังคำนวณใหม่</span> : null}
              </button>
            );
          })}
        </div>
        <p className="board-defender-note">คำนวณผู้เล่นฝ่ายตรงข้ามทุกคน รวมผู้รักษาประตู ในฐานะผู้ที่อาจเข้ามาสกัดบอล</p>
        {isComplete ? (
          <p className="board-export-disclaimer">คะแนนเป็นดัชนีความเสี่ยงจากแบบจำลอง ไม่ใช่ความน่าจะเป็นจากข้อมูลการแข่งขันจริง</p>
        ) : null}
      </div>

      {isComplete ? (
        <div className="board-export-actions" aria-label="ส่งออกผลเปรียบเทียบ A B และ C">
          <span>บันทึกผลสำหรับโค้ชและนักเตะ</span>
          <div>
            <button type="button" disabled={exporting !== null || pendingSlot !== null} onClick={() => void exportImage()}>
              {exporting === "image" ? "กำลังสร้างภาพ…" : "ดาวน์โหลดภาพ PNG"}
            </button>
            <button type="button" disabled={exporting !== null || pendingSlot !== null} onClick={() => void exportPdf()}>
              {exporting === "pdf" ? "กำลังสร้าง PDF…" : "ดาวน์โหลด PDF"}
            </button>
          </div>
        </div>
      ) : (
        <p className="board-export-hint">เพิ่มผลให้ครบ A, B และ C เพื่อส่งออกเป็นภาพหรือ PDF</p>
      )}
      {exportError ? <p className="board-export-error" role="alert">{exportError}</p> : null}

      {activeComparison ? (
        <section className={`board-active-detail risk-${activeComparison.result.risk}`}>
          <div className="board-active-title">
            <span>รายละเอียดทางเลือกที่เลือก</span>
            <strong>คะแนนความเสี่ยง {activeComparison.result.risk_percent}/100</strong>
          </div>
          <dl>
            <div><dt>รูปแบบการจ่าย</dt><dd>{passTypeLabels[activeComparison.result.pass_type]}</dd></div>
            <div><dt>ระยะทาง</dt><dd>{activeComparison.result.pass_distance.toFixed(1)} เมตร</dd></div>
            <div><dt>เวลาบอลเดินทาง</dt><dd>{activeComparison.result.ball_time.toFixed(2)} วินาที</dd></div>
            <div><dt>ผู้เล่นที่ใกล้สกัดที่สุด</dt><dd>{activeComparison.result.interceptor_id?.toUpperCase() ?? "ไม่มี"}</dd></div>
            <div><dt>ส่วนต่างเวลาสกัด</dt><dd>{activeComparison.result.minimum_margin?.toFixed(2) ?? "—"} วินาที</dd></div>
          </dl>
          <p>{activeComparison.result.explanation.replace(/\d+%/, `${activeComparison.result.risk_percent}/100`)}</p>
          <details>
            <summary>สมมติฐานที่ใช้คำนวณ</summary>
            <dl className="assumption-grid">
              <div><dt>ความเร็วบอล</dt><dd>{activeComparison.result.pass_type === "ground" ? activeComparison.parameters.ball_speed : activeComparison.result.pass_type === "chip" ? activeComparison.parameters.chip_speed : activeComparison.parameters.long_ball_speed} ม./วิ</dd></div>
              <div><dt>ความเร็วฝ่ายรับ/โกล</dt><dd>{activeComparison.parameters.defender_speed} ม./วิ</dd></div>
              <div><dt>เวลาตอบสนอง</dt><dd>{activeComparison.parameters.reaction_time} วินาที</dd></div>
              <div><dt>รัศมีสกัด</dt><dd>{activeComparison.parameters.reach_radius} เมตร</dd></div>
            </dl>
            <p className="model-disclaimer">คะแนนนี้มาจากแบบจำลองคิเนมาติกส์ตามสมมติฐานข้างต้น ไม่ใช่ความน่าจะเป็นที่ปรับเทียบจากผลการแข่งขันจริง</p>
          </details>
        </section>
      ) : <p className="board-empty-help">เลือกเป้าหมายบนสนามเพื่อเริ่มเปรียบเทียบ ระบบจะเติม A, B และ C ตามลำดับ</p>}
    </aside>
  );
}
