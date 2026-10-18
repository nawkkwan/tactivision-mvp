import { useRef, useState } from "react";
import { FieldMap } from "./FieldMap";
import { PitchWorkspace } from "./PitchWorkspace";
import { RiskResults } from "./RiskResults";
import type {
  CalibrationPair,
  Comparison,
  DetectResponse,
  Detection,
  PassType,
  Point2D,
  SimulationParameters,
  TargetMode,
} from "../types";

type BoardView = "field" | "image" | "split";

interface PassAnalysisBoardProps {
  analysis: DetectResponse;
  imageUrl: string | null;
  carrierId: string;
  comparisons: Comparison[];
  activeId: string | null;
  pendingSlot: number | null;
  passType: PassType;
  targetMode: TargetMode;
  runnerId: string | null;
  parameters: SimulationParameters;
  calibrationPairs: CalibrationPair[];
  onPassTypeChange: (passType: PassType) => void;
  onDetectionClick: (detection: Detection) => void;
  onCanvasClick: (point: Point2D) => void;
  onFieldClick: (point: Point2D) => void;
  onSelectComparison: (id: string) => void;
  onClearComparisons: () => void;
  onTargetModeChange: (mode: TargetMode) => void;
  onRunnerChange: (id: string) => void;
  onParametersChange: (parameters: SimulationParameters) => void;
  onResetParameters: () => void;
}

const passOptions: Array<{ id: PassType; title: string; detail: string; path: string }> = [
  { id: "ground", title: "ลูกเรียด", detail: "เส้นตรงติดพื้น", path: "M2 14 L30 14" },
  { id: "chip", title: "ลูกชิพ", detail: "โค้งระยะสั้น", path: "M2 15 Q16 2 30 15" },
  { id: "long_ball", title: "ลูกเปิดยาว", detail: "โค้งสูงและไกล", path: "M2 16 Q16 -3 30 16" },
];

function waitForBoardRender() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });
}

export function PassAnalysisBoard({
  analysis,
  imageUrl,
  carrierId,
  comparisons,
  activeId,
  pendingSlot,
  passType,
  targetMode,
  runnerId,
  parameters,
  calibrationPairs,
  onPassTypeChange,
  onDetectionClick,
  onCanvasClick,
  onFieldClick,
  onSelectComparison,
  onClearComparisons,
  onTargetModeChange,
  onRunnerChange,
  onParametersChange,
  onResetParameters,
}: PassAnalysisBoardProps) {
  const reportRef = useRef<HTMLElement>(null);
  const [view, setView] = useState<BoardView>("image");
  const [exporting, setExporting] = useState<"image" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const activeComparison = comparisons.find((item) => item.id === activeId) ?? null;
  const carrier = analysis.detections.find((item) => item.id === carrierId);
  const teammates = analysis.detections.filter(
    (item) =>
      item.id !== carrierId &&
      item.team_id === carrier?.team_id &&
      item.field_position !== null &&
      (item.class_name === "player" || item.class_name === "goalkeeper"),
  );

  async function createReportImage() {
    if (!reportRef.current || comparisons.length !== 3 || pendingSlot !== null) {
      throw new Error("กรุณารอให้ผลเปรียบเทียบ A, B และ C คำนวณครบก่อน");
    }
    const previousView = view;
    if (view !== "split") {
      setView("split");
      await waitForBoardRender();
    }
    try {
      const [{ toPng }] = await Promise.all([import("html-to-image"), document.fonts.ready]);
      return await toPng(reportRef.current, {
        backgroundColor: "#ffffff",
        cacheBust: true,
        pixelRatio: 2,
        filter: (node) => !(node instanceof HTMLElement && node.dataset.exportIgnore === "true"),
      });
    } finally {
      if (previousView !== "split") setView(previousView);
    }
  }

  function reportFilename(extension: "png" | "pdf") {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `tactivision-abc-with-pitch-${timestamp}.${extension}`;
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

  const fieldMap = (
    <FieldMap
      detections={analysis.detections}
      carrierId={carrierId}
      candidateCarrierId={null}
      stage={5}
      targetMode={targetMode}
      comparisons={comparisons}
      activeId={activeId}
      onDetectionClick={onDetectionClick}
      onFieldClick={onFieldClick}
    />
  );

  const imageMap = (
    <div className="board-image-view">
      <PitchWorkspace
        imageUrl={imageUrl}
        imageWidth={analysis.image.width}
        imageHeight={analysis.image.height}
        detections={analysis.detections}
        stage={5}
        carrierId={carrierId}
        candidateCarrierId={null}
        calibrationPairs={calibrationPairs}
        targetPixel={activeComparison?.targetPixel ?? null}
        interceptPixel={activeComparison?.interceptPixel ?? null}
        passType={activeComparison?.result.pass_type ?? passType}
        onDetectionClick={onDetectionClick}
        onCanvasClick={onCanvasClick}
      />
      <div className="board-image-help" data-export-ignore="true" aria-label="วิธีใช้งานภาพการแข่งขัน">
        <span className="eyebrow">ทำอะไรบนภาพนี้ได้บ้าง</span>
        <div>
          <article><b>คลิกเพื่อนร่วมทีม</b><small>คำนวณการส่งเข้าเท้าของผู้เล่นคนนั้นทันที</small></article>
          <article><b>คลิกพื้นที่ว่าง</b><small>สร้างทางเลือกการจ่ายบอลเข้าสู่พื้นที่เป้าหมาย</small></article>
          <article><b>เลือก A / B / C</b><small>ดูเส้นทางและรายละเอียดของทางเลือกที่ต้องการ</small></article>
        </div>
      </div>
    </div>
  );

  return (
    <section ref={reportRef} className="analysis-board" aria-labelledby="analysis-board-title">
      <header className="analysis-board-header">
        <div>
          <span className="eyebrow">STEP 5 · PASS ANALYSIS BOARD</span>
          <h2 id="analysis-board-title">วิเคราะห์ทางเลือกการจ่ายบอล</h2>
          <p>ผู้ครองบอล <strong>{carrierId.toUpperCase()}</strong> ถูกล็อกแล้ว — คลิกเพื่อนร่วมทีมหรือพื้นที่ว่างเพื่อสร้าง A/B/C</p>
        </div>
        <div className="board-ready"><i />พร้อมจำลอง</div>
      </header>

      <div className="board-workflow" data-export-ignore="true" aria-label="ขั้นตอนการใช้งานกระดานวิเคราะห์">
        <span className="done"><b>1</b> ผู้ครองบอล {carrierId.toUpperCase()}</span>
        <span className="current"><b>2</b> คลิกเป้าหมาย</span>
        <span className={comparisons.length > 0 ? "done" : ""}><b>3</b> ดูผลเปรียบเทียบ</span>
      </div>

      <div className="board-toolbar" data-export-ignore="true">
        <div className="board-pass-types" role="group" aria-label="รูปแบบวิถีการจ่ายบอล">
          {passOptions.map((option) => (
            <button type="button" key={option.id} aria-pressed={passType === option.id} onClick={() => onPassTypeChange(option.id)}>
              <svg viewBox="0 0 32 18" aria-hidden="true"><path d={option.path} /></svg>
              <span><strong>{option.title}</strong><small>{option.detail}</small></span>
            </button>
          ))}
        </div>
        <div className="board-view-tabs" role="tablist" aria-label="มุมมองกระดานวิเคราะห์">
          {([['image', 'ภาพจริง'], ['field', 'สนาม 2D'], ['split', 'ดูคู่กัน']] as const).map(([id, label]) => (
            <button type="button" role="tab" key={id} aria-selected={view === id} onClick={() => setView(id)}>{label}</button>
          ))}
        </div>
      </div>

      <div className="analysis-board-layout">
        <div className={`board-stage view-${view}`}>
          {view === "field" ? fieldMap : null}
          {view === "image" ? imageMap : null}
          {view === "split" ? <><div>{fieldMap}</div><div>{imageMap}</div></> : null}
          <div className="board-legend">
            <span><i className="route-dot route-0" />A</span>
            <span><i className="route-dot route-1" />B</span>
            <span><i className="route-dot route-2" />C</span>
            <span><b>×</b> จุดเสี่ยงถูกสกัด</span>
          </div>
        </div>

        <RiskResults
          comparisons={comparisons}
          activeId={activeId}
          pendingSlot={pendingSlot}
          exporting={exporting}
          exportError={exportError}
          onSelect={onSelectComparison}
          onClear={onClearComparisons}
          onExportImage={() => void exportImage()}
          onExportPdf={() => void exportPdf()}
        />
      </div>

      <details className="board-advanced" data-export-ignore="true">
        <summary>ตั้งค่าขั้นสูง · แทงทะลุช่อง / ความเร็ว / เวลาตอบสนอง</summary>
        <div className="advanced-target-mode">
          <button type="button" aria-pressed={targetMode === "through_ball"} onClick={() => onTargetModeChange(targetMode === "through_ball" ? "receiver" : "through_ball")}>
            แทงทะลุช่อง
          </button>
          <span>{targetMode === "through_ball" ? "เลือกผู้วิ่ง แล้วคลิกจุดปลายทางบนสนาม" : "โหมดปกติ: คลิกผู้เล่นหรือพื้นที่ว่างเพื่อคำนวณทันที"}</span>
        </div>
        {targetMode === "through_ball" ? (
          <div className="receiver-shortcuts" aria-label="เลือกผู้วิ่งไปรับบอล">
            <span>ผู้เล่นที่จะวิ่งรับบอล:</span>
            <div>{teammates.map((player) => (
              <button type="button" key={player.id} aria-pressed={runnerId === player.id} onClick={() => onRunnerChange(player.id)}>{player.id.toUpperCase()}</button>
            ))}</div>
          </div>
        ) : null}
        <div className="field-grid board-parameter-grid">
          {([
            ["ball_speed", "ความเร็วลูกเรียด", "ม./วิ", 1, 60, 0.5],
            ["chip_speed", "ความเร็วลูกชิพ", "ม./วิ", 1, 40, 0.5],
            ["chip_apex_height", "ความสูงลูกชิพ", "ม.", 1, 8, 0.25],
            ["long_ball_speed", "ความเร็วลูกเปิดยาว", "ม./วิ", 1, 40, 0.5],
            ["long_ball_apex_height", "ความสูงลูกเปิดยาว", "ม.", 1, 10, 0.25],
            ["defender_speed", "ความเร็วฝ่ายรับ/โกล", "ม./วิ", 1, 15, 0.5],
            ["attacker_speed", "ความเร็วผู้รับบอล", "ม./วิ", 1, 15, 0.5],
            ["reaction_time", "เวลาตอบสนอง", "วินาที", 0, 3, 0.1],
            ["reach_radius", "รัศมีสกัด", "ม.", 0, 3, 0.1],
          ] as const).map(([key, label, unit, min, max, increment]) => (
            <label key={key}><span>{label}</span><div><input type="number" min={min} max={max} step={increment} value={parameters[key]} onChange={(event) => onParametersChange({ ...parameters, [key]: Number(event.target.value) })} /><small>{unit}</small></div></label>
          ))}
        </div>
        <button type="button" className="text-button" onClick={onResetParameters}>คืนค่ามาตรฐานเริ่มต้น</button>
      </details>
    </section>
  );
}
