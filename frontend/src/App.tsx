import { useMemo, useRef, useState } from "react";
import { calibrateImage, detectImage, simulatePass } from "./api";
import { DetectionReview } from "./components/DetectionReview";
import { PitchWorkspace } from "./components/PitchWorkspace";
import { RiskResults } from "./components/RiskResults";
import { StepRail } from "./components/StepRail";
import { demoAnalysis } from "./demo";
import type {
  CalibrationPair,
  Comparison,
  DetectResponse,
  Detection,
  PassType,
  Point2D,
  SimulationParameters,
  TargetMode,
} from "./types";

const defaultParameters: SimulationParameters = {
  ball_speed: 18,
  chip_speed: 14,
  chip_apex_height: 3,
  long_ball_speed: 15.8,
  long_ball_apex_height: 3.8,
  defender_speed: 7,
  attacker_speed: 7,
  reaction_time: 0.3,
  reach_radius: 1,
  sample_step: 0.5,
};

const landmarks = [
  { number: 1, label: "มุมสนามซ้ายบน", field: { x: 0, y: 0 } },
  { number: 2, label: "กึ่งกลางเส้นบน", field: { x: 52.5, y: 0 } },
  { number: 3, label: "มุมสนามขวาบน", field: { x: 105, y: 0 } },
  { number: 4, label: "กึ่งกลางเส้นซ้าย", field: { x: 0, y: 34 } },
  { number: 5, label: "จุดกลางสนาม", field: { x: 52.5, y: 34 } },
  { number: 6, label: "กึ่งกลางเส้นขวา", field: { x: 105, y: 34 } },
  { number: 7, label: "มุมสนามซ้ายล่าง", field: { x: 0, y: 68 } },
  { number: 8, label: "มุมสนามขวาล่าง", field: { x: 105, y: 68 } },
] as const;

function applyHomography(point: Point2D, matrix: number[][]): Point2D | null {
  const denominator = matrix[2][0] * point.x + matrix[2][1] * point.y + matrix[2][2];
  if (Math.abs(denominator) < 1e-9) return null;
  return {
    x: (matrix[0][0] * point.x + matrix[0][1] * point.y + matrix[0][2]) / denominator,
    y: (matrix[1][0] * point.x + matrix[1][1] * point.y + matrix[1][2]) / denominator,
  };
}

function invertMatrix3(matrix: number[][]): number[][] | null {
  const [[a, b, c], [d, e, f], [g, h, i]] = matrix;
  const determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
  if (Math.abs(determinant) < 1e-9) return null;
  return [
    [(e * i - f * h) / determinant, (c * h - b * i) / determinant, (b * f - c * e) / determinant],
    [(f * g - d * i) / determinant, (a * i - c * g) / determinant, (c * d - a * f) / determinant],
    [(d * h - e * g) / determinant, (b * g - a * h) / determinant, (a * e - b * d) / determinant],
  ];
}

function suggestCarrier(detections: Detection[]): string | null {
  const ball = detections.find((item) => item.class_name === "ball");
  const players = detections.filter(
    (item) => item.class_name === "player" || item.class_name === "goalkeeper",
  );
  if (!ball || players.length === 0) return players[0]?.id ?? null;
  let best: Detection | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const player of players) {
    const distance = Math.hypot(
      player.foot_pixel.x - ball.foot_pixel.x,
      player.foot_pixel.y - ball.foot_pixel.y,
    );
    if (distance < bestDistance) {
      best = player;
      bestDistance = distance;
    }
  }
  return best?.id ?? null;
}

function cloneDemo(): DetectResponse {
  return structuredClone(demoAnalysis);
}

function App() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<DetectResponse | null>(null);
  const [isFixture, setIsFixture] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [manualMode, setManualMode] = useState(false);
  const [pendingLandmark, setPendingLandmark] = useState<(typeof landmarks)[number] | null>(null);
  const [calibrationPairs, setCalibrationPairs] = useState<CalibrationPair[]>([]);
  const [candidateCarrierId, setCandidateCarrierId] = useState<string | null>(null);
  const [carrierId, setCarrierId] = useState<string | null>(null);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [activeComparisonId, setActiveComparisonId] = useState<string | null>(null);
  const [parameters, setParameters] = useState<SimulationParameters>(defaultParameters);
  const [passType, setPassType] = useState<PassType>("ground");
  const [targetMode, setTargetMode] = useState<TargetMode>("receiver");
  const [runnerId, setRunnerId] = useState<string | null>(null);

  const activeComparison = useMemo(
    () => comparisons.find((item) => item.id === activeComparisonId) ?? comparisons.at(-1) ?? null,
    [activeComparisonId, comparisons],
  );
  const candidate = useMemo(
    () => analysis?.detections.find((item) => item.id === candidateCarrierId) ?? null,
    [analysis, candidateCarrierId],
  );

  function resetAnalysis(nextImageUrl: string | null = null) {
    if (imageUrl?.startsWith("blob:")) URL.revokeObjectURL(imageUrl);
    setImageUrl(nextImageUrl);
    setAnalysis(null);
    setStep(1);
    setMaxStep(1);
    setIsFixture(false);
    setManualMode(false);
    setCalibrationPairs([]);
    setPendingLandmark(null);
    setCandidateCarrierId(null);
    setCarrierId(null);
    setComparisons([]);
    setPassType("ground");
    setTargetMode("receiver");
    setRunnerId(null);
    setActiveComparisonId(null);
    setError(null);
    setNotice(null);
  }

  async function handleFile(file: File) {
    const nextUrl = URL.createObjectURL(file);
    resetAnalysis(nextUrl);
    setBusy(true);
    setNotice("กำลังตรวจผู้เล่น แบ่งทีม และลอง Auto Calibration…");
    try {
      const result = await detectImage(file);
      setAnalysis(result);
      setManualMode(result.calibration.status !== "success");
      setStep(2);
      setMaxStep(2);
      setNotice(`วิเคราะห์ภาพด้วย ${result.detector.model} สำเร็จ`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "วิเคราะห์ภาพไม่สำเร็จ");
      setNotice(null);
    } finally {
      setBusy(false);
    }
  }

  function loadDemo() {
    resetAnalysis("/demo-pitch.svg");
    const result = cloneDemo();
    setAnalysis(result);
    setIsFixture(true);
    setStep(2);
    setMaxStep(2);
    setNotice("กำลังใช้ฉากและ Detection ตัวอย่าง ข้อมูลส่วนนี้ไม่ใช่ผลจาก AI");
  }

  function updateDetection(id: string, patch: Partial<Detection>) {
    setAnalysis((current) =>
      current
        ? {
            ...current,
            detections: current.detections.map((item) =>
              item.id === id
                ? {
                    ...item,
                    ...patch,
                    team_id: patch.class_name === "referee" ? "unassigned" : patch.team_id ?? item.team_id,
                  }
                : item,
            ),
          }
        : current,
    );
    setCarrierId(null);
    setCandidateCarrierId(null);
    setComparisons([]);
    setMaxStep((current) => Math.min(current, 4));
  }

  function removeDetection(id: string) {
    setAnalysis((current) =>
      current
        ? { ...current, detections: current.detections.filter((item) => item.id !== id) }
        : current,
    );
    setCarrierId(null);
    setComparisons([]);
    setMaxStep((current) => Math.min(current, 4));
  }

  function continueToCalibration() {
    if (!analysis) return;
    const assignedPlayers = analysis.detections.filter(
      (item) =>
        (item.class_name === "player" || item.class_name === "goalkeeper") &&
        (item.team_id === "team_a" || item.team_id === "team_b"),
    );
    const teamCounts = assignedPlayers.reduce(
      (counts, player) => ({ ...counts, [player.team_id!]: counts[player.team_id!] + 1 }),
      { team_a: 0, team_b: 0, unassigned: 0 },
    );
    if (assignedPlayers.length < 3 || teamCounts.team_a === 0 || teamCounts.team_b === 0) {
      setError("กรุณากำหนดผู้เล่นอย่างน้อย 3 คน และต้องมีทั้ง Team A กับ Team B");
      return;
    }
    setError(null);
    setStep(3);
    setMaxStep((current) => Math.max(current, 3));
    setManualMode(analysis.calibration.status !== "success");
  }

  function handleCanvasClick(point: Point2D) {
    if (step === 3 && manualMode) {
      if (!pendingLandmark) {
        setError("เลือกชื่อจุดอ้างอิงก่อน แล้วจึงคลิกตำแหน่งเดียวกันบนภาพ");
        return;
      }
      setCalibrationPairs((current) => [
        ...current.filter((pair) => pair.label !== pendingLandmark.label),
        { label: pendingLandmark.label, image: point, field: pendingLandmark.field },
      ]);
      setNotice(`บันทึกจุด “${pendingLandmark.label}” แล้ว`);
      setPendingLandmark(null);
      setError(null);
      return;
    }

    if (step === 5 && carrierId && analysis?.calibration.matrix) {
      if (targetMode === "receiver") {
        setNotice("เลือกโหมดพื้นที่ว่างหรือแทงทะลุช่องก่อนคลิกบนสนาม");
        return;
      }
      if (targetMode === "through_ball" && !runnerId) {
        setError("เลือกเพื่อนร่วมทีมที่จะวิ่งรับบอลก่อน แล้วคลิกจุดว่างข้างหน้า");
        return;
      }
      const fieldPoint = applyHomography(point, analysis.calibration.matrix);
      if (!fieldPoint || fieldPoint.x < 0 || fieldPoint.x > 105 || fieldPoint.y < 0 || fieldPoint.y > 68) {
        setError("จุดที่เลือกอยู่นอกขอบเขตสนามหลัง Calibration");
        return;
      }
      const targetLabel = `${targetMode === "through_ball" ? `แทงให้ ${runnerId} ไปที่` : "พื้นที่ว่าง"} ${fieldPoint.x.toFixed(1)}, ${fieldPoint.y.toFixed(1)} m`;
      void runSimulation(
        targetMode === "through_ball"
          ? { type: "through_ball", receiver_id: runnerId!, position: fieldPoint }
          : { type: "space", position: fieldPoint },
        point,
        targetLabel,
      );
    }
  }

  async function submitManualCalibration() {
    if (!analysis || calibrationPairs.length < 4) {
      setError("ต้องเลือกจุดอ้างอิงอย่างน้อย 4 จุด");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await calibrateImage(analysis.image, analysis.detections, calibrationPairs);
      setAnalysis({ ...analysis, calibration: result.calibration, detections: result.detections });
      if (result.calibration.status === "success") {
        setManualMode(false);
        setNotice("Manual Calibration สำเร็จ ตรวจตำแหน่งแล้วไปขั้นถัดไปได้");
      } else {
        setError(result.calibration.message);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Calibration ไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  function acceptCalibration() {
    if (!analysis || analysis.calibration.status !== "success") {
      setError("Calibration ยังไม่สำเร็จ กรุณากำหนดจุดอ้างอิงก่อน");
      return;
    }
    const suggestion = suggestCarrier(analysis.detections);
    setCandidateCarrierId(suggestion);
    setStep(4);
    setMaxStep((current) => Math.max(current, 4));
    setError(null);
    setNotice(suggestion ? `AI แนะนำ ${suggestion} เป็น Ball Carrier กรุณาตรวจและยืนยัน` : null);
  }

  function confirmCarrier() {
    if (!analysis || !candidate) {
      setError("กรุณาคลิกเลือก Ball Carrier บนภาพ");
      return;
    }
    if (!candidate.field_position || candidate.team_id === "unassigned" || !candidate.team_id) {
      setError("ผู้เล่นที่เลือกต้องมี Team ID และพิกัดสนามที่ผ่าน Calibration");
      return;
    }
    setCarrierId(candidate.id);
    setRunnerId(null);
    setStep(5);
    setMaxStep(5);
    setError(null);
    setNotice(`ล็อก ${candidate.id} เป็น Ball Carrier แล้ว คลิกเพื่อนร่วมทีมหรือพื้นที่ว่าง`);
  }

  async function runSimulation(
    target: { type: "receiver" | "space" | "through_ball"; position: Point2D; receiver_id?: string },
    targetPixel: Point2D,
    targetLabel: string,
  ) {
    if (!analysis || !carrierId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await simulatePass({
        detections: analysis.detections,
        carrierId,
        passType,
        target,
        parameters,
      });
      let interceptPixel: Point2D | null = null;
      if (result.intercept_point && analysis.calibration.matrix) {
        const inverse = invertMatrix3(analysis.calibration.matrix);
        if (inverse) interceptPixel = applyHomography(result.intercept_point, inverse);
      }
      const comparison: Comparison = {
        id: crypto.randomUUID(),
        targetLabel,
        targetPixel,
        interceptPixel,
        result,
      };
      setComparisons((current) => [...current.slice(-2), comparison]);
      setActiveComparisonId(comparison.id);
      setNotice(`คำนวณ ${targetLabel} แล้ว — ความเสี่ยงถูกตัดบอล ${result.risk_percent}%`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "คำนวณ Simulation ไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  function handleDetectionClick(detection: Detection) {
    if (step === 4 && detection.class_name !== "ball" && detection.class_name !== "referee") {
      setCandidateCarrierId(detection.id);
      setNotice(`เลือก ${detection.id} เป็น Ball Carrier รอยืนยัน`);
      setError(null);
      return;
    }
    if (step !== 5 || !analysis || !carrierId) return;
    if (targetMode !== "receiver") {
      setNotice(targetMode === "through_ball"
        ? "โหมดแทงทะลุช่องทำงานอยู่ — เลือกผู้วิ่งแล้วคลิกจุดว่างข้างหน้า"
        : "โหมดพื้นที่ว่างทำงานอยู่ — คลิกตำแหน่งว่างบนสนาม");
      return;
    }
    if (detection.id === carrierId) {
      setError("Ball Carrier ไม่สามารถส่งบอลให้ตัวเอง");
      return;
    }
    const carrier = analysis.detections.find((item) => item.id === carrierId);
    if (
      !carrier ||
      detection.class_name === "ball" ||
      detection.class_name === "referee" ||
      !detection.field_position
    ) return;
    if (detection.team_id !== carrier.team_id) {
      setError("เลือกผู้เล่นฝ่ายตรงข้ามเป็นผู้รับบอลไม่ได้");
      return;
    }
    void runSimulation(
      { type: "receiver", receiver_id: detection.id, position: detection.field_position },
      detection.foot_pixel,
      `ส่งให้ ${detection.id}`,
    );
  }

  const statusLabel = busy
    ? "กำลังประมวลผล"
    : analysis
      ? `${analysis.detector.model} · ${analysis.detector.mode === "fine_tuned" ? "Fine-tuned" : isFixture ? "Sample fixture" : "Generic"}`
      : "พร้อมเริ่มวิเคราะห์";

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="TactiVision หน้าหลัก">
          <span className="brand-mark">TV</span>
          <span><strong>TactiVision</strong><small>PASS INTERCEPTION LAB</small></span>
        </a>
        <div className="status-pill"><i className={busy ? "pulse" : ""} />{statusLabel}</div>
      </header>

      <main id="top">
        <section className="hero">
          <div>
            <span className="eyebrow">STATIC FRAME · TACTICAL DECISION SUPPORT</span>
            <h1>มองเห็นทางเลือก<br /><em>ก่อนบอลจะเคลื่อนที่</em></h1>
          </div>
          <p>
            วิเคราะห์แนวจ่ายบอลจากภาพนิ่ง เปรียบเทียบผู้รับและพื้นที่ว่าง
            ด้วยพิกัดสนามจริงและสมมติฐานที่ตรวจสอบได้
          </p>
        </section>

        <StepRail current={step} maxStep={maxStep} onStep={setStep} />

        {error ? <div className="alert error-alert" role="alert"><strong>ตรวจสอบอีกครั้ง</strong>{error}</div> : null}
        {notice ? <div className="alert notice-alert" role="status">{notice}</div> : null}

        <section className="workspace-grid">
          <div className="visual-column">
            <PitchWorkspace
              imageUrl={imageUrl}
              imageWidth={analysis?.image.width ?? 1200}
              imageHeight={analysis?.image.height ?? 700}
              detections={analysis?.detections ?? []}
              stage={step}
              carrierId={carrierId}
              candidateCarrierId={candidateCarrierId}
              calibrationPairs={calibrationPairs}
              targetPixel={activeComparison?.targetPixel ?? null}
              interceptPixel={activeComparison?.interceptPixel ?? null}
              passType={activeComparison?.result.pass_type ?? passType}
              onDetectionClick={handleDetectionClick}
              onCanvasClick={handleCanvasClick}
            />
            <div className="legend">
              <span><i className="dot team-a" />Team A</span>
              <span><i className="dot team-b" />Team B</span>
              <span><i className="dot target-dot" />Pass target</span>
              <span><i className="cross">×</i>Interception point</span>
            </div>
          </div>

          <aside className="control-panel">
            {step === 1 ? (
              <div className="panel-content intro-panel">
                <span className="panel-number">01</span>
                <span className="eyebrow">START A NEW FRAME</span>
                <h2>เลือกภาพการแข่งขัน</h2>
                <p>ใช้ภาพมุมถ่ายทอดกว้างที่เห็นผู้เล่นและเส้นสนามชัด รองรับ JPEG, PNG และ WebP สูงสุด 10 MB</p>
                <input
                  ref={fileInput}
                  className="sr-only"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void handleFile(file);
                    event.target.value = "";
                  }}
                />
                <button className="primary-button" type="button" disabled={busy} onClick={() => fileInput.current?.click()}>
                  อัปโหลดภาพจริง <span>→</span>
                </button>
                <button className="secondary-button" type="button" disabled={busy} onClick={loadDemo}>
                  ลองฉากตัวอย่าง
                </button>
                <small>ฉากตัวอย่างใช้ Fixture ที่ระบุชัดเจน ไม่ใช่ผล Detection จาก AI</small>
              </div>
            ) : null}

            {step === 2 && analysis ? (
              <div className="panel-content">
                <span className="panel-number">02</span>
                <span className="eyebrow">VERIFY BEFORE ANALYSIS</span>
                <h2>ตรวจผู้เล่นและทีม</h2>
                <p>แก้ Class หรือ Team ID เมื่อ AI แบ่งผิด ผู้รักษาประตูอาจมีสีเสื้อต่างจากเพื่อนร่วมทีม</p>
                <DetectionReview detections={analysis.detections} onUpdate={updateDetection} onRemove={removeDetection} />
                <button className="primary-button" type="button" onClick={continueToCalibration}>
                  ยืนยันผู้เล่นและทีม <span>→</span>
                </button>
              </div>
            ) : null}

            {step === 3 && analysis ? (
              <div className="panel-content">
                <span className="panel-number">03</span>
                <span className="eyebrow">PIXELS → METRES</span>
                <h2>Calibration สนาม</h2>
                <div className={`calibration-card ${analysis.calibration.status}`}>
                  <div><strong>{analysis.calibration.method.toUpperCase()}</strong><span>{Math.round(analysis.calibration.confidence * 100)}%</span></div>
                  <p>{analysis.calibration.message}</p>
                  {analysis.calibration.reprojection_error !== null ? (
                    <small>Reprojection error: {analysis.calibration.reprojection_error.toFixed(2)}</small>
                  ) : null}
                </div>
                {!manualMode && analysis.calibration.status === "success" ? (
                  <>
                    <button className="primary-button" type="button" onClick={acceptCalibration}>
                      ใช้ผล Calibration นี้ <span>→</span>
                    </button>
                    <button className="text-button" type="button" onClick={() => setManualMode(true)}>
                      กำหนดจุดด้วยตนเองแทน
                    </button>
                  </>
                ) : (
                  <div className="manual-calibration">
                    <p><strong>เลือกจุดจากแผนผัง แล้วคลิกจุดเดียวกันบนภาพใหญ่</strong></p>
                    <div className="landmark-guide" aria-label="แผนผังตำแหน่งจุดอ้างอิงบนสนาม">
                      <div className="landmark-guide-heading">
                        <span>แผนผังสนามอ้างอิง</span>
                        <small>บน–ล่างอ้างอิงตามแผนผังนี้</small>
                      </div>
                      <div className="mini-pitch">
                        <span className="mini-pitch-halfway" />
                        <span className="mini-pitch-circle" />
                        <span className="mini-pitch-box mini-pitch-box-left" />
                        <span className="mini-pitch-box mini-pitch-box-right" />
                        {landmarks.map((landmark) => {
                          const completed = calibrationPairs.some((pair) => pair.label === landmark.label);
                          const pending = pendingLandmark?.label === landmark.label;
                          return (
                            <button
                              type="button"
                              key={`pitch-${landmark.label}`}
                              className={`${pending ? "pending" : ""} ${completed ? "completed" : ""}`}
                              style={{
                                left: `${(landmark.field.x / 105) * 100}%`,
                                top: `${(landmark.field.y / 68) * 100}%`,
                              }}
                              title={landmark.label}
                              aria-label={`จุด ${landmark.number}: ${landmark.label}${completed ? " เลือกแล้ว" : ""}`}
                              aria-pressed={pending}
                              onClick={() => setPendingLandmark(landmark)}
                            >
                              {completed ? "✓" : landmark.number}
                            </button>
                          );
                        })}
                      </div>
                      <p className={`landmark-instruction ${pendingLandmark ? "active" : ""}`}>
                        {pendingLandmark
                          ? `เลือกจุด ${pendingLandmark.number}: ${pendingLandmark.label} แล้ว — คลิกตำแหน่งเดียวกันบนภาพใหญ่`
                          : "กดหมายเลขที่มองเห็นชัดในภาพ แล้วไปคลิกตำแหน่งเดียวกันบนภาพใหญ่"}
                      </p>
                    </div>
                    <div className="landmark-grid">
                      {landmarks.map((landmark) => {
                        const completed = calibrationPairs.some((pair) => pair.label === landmark.label);
                        return (
                          <button
                            type="button"
                            key={landmark.label}
                            className={`${pendingLandmark?.label === landmark.label ? "pending" : ""} ${completed ? "completed" : ""}`}
                            onClick={() => setPendingLandmark(landmark)}
                          >
                            <span>{completed ? "✓" : landmark.number}</span>{landmark.label}
                          </button>
                        );
                      })}
                    </div>
                    <p className="counter">เลือกแล้ว {calibrationPairs.length}/4 จุดขั้นต่ำ</p>
                    <button
                      className="primary-button"
                      type="button"
                      disabled={busy || calibrationPairs.length < 4}
                      onClick={() => void submitManualCalibration()}
                    >
                      คำนวณ Manual Calibration
                    </button>
                    {analysis.calibration.status === "success" ? (
                      <button className="text-button" type="button" onClick={() => setManualMode(false)}>
                        กลับไปใช้ผลเดิม
                      </button>
                    ) : null}
                  </div>
                )}
              </div>
            ) : null}

            {step === 4 && analysis ? (
              <div className="panel-content carrier-panel">
                <span className="panel-number">04</span>
                <span className="eyebrow">LOCK THE ORIGIN</span>
                <h2>ยืนยันคนครองบอล</h2>
                <p>ระบบเสนอผู้เล่นที่ใกล้ลูกบอลที่สุด คลิกกรอบคนอื่นได้หากคำแนะนำไม่ตรงกับจังหวะจริง</p>
                <div className="carrier-choice">
                  <span>ผู้เล่นที่เลือก</span>
                  <strong>{candidate?.id ?? "ยังไม่ได้เลือก"}</strong>
                  <small>{candidate ? `${candidate.team_id?.replace("team_", "Team ").toUpperCase()} · ${candidate.class_name}` : "คลิกผู้เล่นบนภาพ"}</small>
                </div>
                <button className="primary-button" type="button" disabled={!candidate} onClick={confirmCarrier}>
                  ล็อก Ball Carrier <span>→</span>
                </button>
              </div>
            ) : null}

            {step === 5 && analysis ? (
              <div className="panel-content simulation-panel">
                <span className="panel-number">05</span>
                <span className="eyebrow">COMPARE PASS OPTIONS</span>
                <h2>เลือกเป้าหมาย</h2>
                <p>เลือกรูปแบบการจ่ายและประเภทเป้าหมาย แล้วคลิกผู้เล่นหรือพื้นที่บนสนาม ผลใหม่จะไม่รัน Detection ซ้ำ</p>
                <div className="locked-carrier"><span>Ball Carrier</span><strong>{carrierId}</strong><i>LOCKED</i></div>
                <div className="simulation-choices">
                  <span>รูปแบบการจ่าย</span>
                  <div className="segmented-control" role="group" aria-label="รูปแบบการจ่ายบอล">
                    <button type="button" aria-pressed={passType === "ground"} onClick={() => setPassType("ground")}>
                      <strong>GROUND</strong><small>ลูกเรียด</small>
                    </button>
                    <button type="button" aria-pressed={passType === "chip"} onClick={() => setPassType("chip")}>
                      <strong>CHIP</strong><small>ลูกชิพ</small>
                    </button>
                    <button type="button" aria-pressed={passType === "long_ball"} onClick={() => setPassType("long_ball")}>
                      <strong>LONG</strong><small>เปิดยาว</small>
                    </button>
                  </div>
                  <span>ประเภทเป้าหมาย</span>
                  <div className="segmented-control" role="group" aria-label="ประเภทเป้าหมาย">
                    <button type="button" aria-pressed={targetMode === "receiver"} onClick={() => { setTargetMode("receiver"); setRunnerId(null); }}>
                      <strong>PLAYER</strong><small>ส่งให้เพื่อน</small>
                    </button>
                    <button type="button" aria-pressed={targetMode === "space"} onClick={() => { setTargetMode("space"); setRunnerId(null); }}>
                      <strong>SPACE</strong><small>จ่ายเข้าที่ว่าง</small>
                    </button>
                    <button type="button" aria-pressed={targetMode === "through_ball"} onClick={() => { setTargetMode("through_ball"); setRunnerId(null); }}>
                      <strong>THROUGH</strong><small>แทงทะลุช่อง</small>
                    </button>
                  </div>
                </div>
                {targetMode !== "space" ? (
                  <div className="receiver-shortcuts" aria-label="รายชื่อผู้รับบอลในทีม">
                    <span>{targetMode === "through_ball" ? "เลือกเพื่อนที่จะวิ่งรับบอล" : "เลือกผู้รับในทีม"}</span>
                    <div>
                      {analysis.detections
                        .filter((item) => {
                          const carrier = analysis.detections.find((candidate) => candidate.id === carrierId);
                          return (
                            item.id !== carrierId &&
                            item.team_id === carrier?.team_id &&
                            item.field_position !== null &&
                            (item.class_name === "player" || item.class_name === "goalkeeper")
                          );
                        })
                        .map((receiver) => (
                          <button
                            type="button"
                            key={receiver.id}
                            aria-pressed={targetMode === "through_ball" ? runnerId === receiver.id : undefined}
                            onClick={() => targetMode === "through_ball" ? setRunnerId(receiver.id) : handleDetectionClick(receiver)}
                          >
                            {receiver.id}
                          </button>
                        ))}
                    </div>
                  </div>
                ) : <p className="space-hint">คลิกพื้นที่ว่างบนภาพเพื่อกำหนดจุดตกของบอล</p>}
                {targetMode === "through_ball" ? (
                  <p className="space-hint">เลือกจุดข้างหน้าผู้วิ่งบนภาพ ระบบสมมติว่าผู้เล่นวิ่งตรงไปยังจุดนี้ ไม่ได้เดาทิศทางจากภาพนิ่ง</p>
                ) : null}
                <details className="advanced-panel">
                  <summary>Advanced Settings</summary>
                  <div className="field-grid">
                    {([
                      ["ball_speed", "Ball speed", "m/s", 1, 60, 0.5],
                      ["chip_speed", "Chip speed", "m/s", 1, 40, 0.5],
                      ["chip_apex_height", "Chip apex", "m", 1, 8, 0.25],
                      ["long_ball_speed", "Long ball speed*", "m/s", 1, 40, 0.5],
                      ["long_ball_apex_height", "Long ball apex*", "m", 1, 10, 0.25],
                      ["defender_speed", "Defender speed", "m/s", 1, 15, 0.5],
                      ["attacker_speed", "Attacker speed", "m/s", 1, 15, 0.5],
                      ["reaction_time", "Reaction time", "s", 0, 3, 0.1],
                      ["reach_radius", "Reach radius", "m", 0, 3, 0.1],
                    ] as const).map(([key, label, unit, min, max, increment]) => (
                      <label key={key}>
                        <span>{label}</span>
                        <div><input
                          type="number"
                          min={min}
                          max={max}
                          step={increment}
                          value={parameters[key]}
                          onChange={(event) => setParameters((current) => ({ ...current, [key]: Number(event.target.value) }))}
                        /><small>{unit}</small></div>
                      </label>
                    ))}
                  </div>
                  <button className="text-button" type="button" onClick={() => setParameters(defaultParameters)}>คืนค่าเริ่มต้น</button>
                  <small className="model-note">* ค่าเปิดยาวเป็นค่าทดลองจากงานศึกษาหนึ่งชุด ไม่ใช่ค่ามาตรฐานสากล</small>
                </details>
                {activeComparison ? (
                  <div className={`active-risk risk-${activeComparison.result.risk}`}>
                    <span>LATEST RESULT</span>
                    <strong>{activeComparison.result.risk_percent}%</strong>
                    <p>ระดับ {activeComparison.result.risk.toUpperCase()}</p>
                    <p>{activeComparison.result.explanation}</p>
                    <details>
                      <summary>ดูรายละเอียดการคำนวณ</summary>
                      <dl>
                        <div><dt>ระยะจ่าย</dt><dd>{activeComparison.result.pass_distance.toFixed(2)} m</dd></div>
                        <div><dt>รูปแบบ</dt><dd>{activeComparison.result.pass_type.toUpperCase()}</dd></div>
                        <div><dt>เวลาบอล</dt><dd>{activeComparison.result.ball_time.toFixed(3)} s</dd></div>
                        <div><dt>ผู้สกัด</dt><dd>{activeComparison.result.interceptor_id ?? "ไม่มี"}</dd></div>
                        <div><dt>ผู้รับที่เร็วที่สุด</dt><dd>{activeComparison.result.receiver_id ?? "ไม่มี"}</dd></div>
                        <div><dt>เวลาผู้รับถึงจุด</dt><dd>{activeComparison.result.receiver_arrival_time?.toFixed(3) ?? "—"} s</dd></div>
                        <div><dt>ผู้รับเทียบกับบอล</dt><dd>{activeComparison.result.receiver_ball_margin?.toFixed(3) ?? "—"} s</dd></div>
                        <div><dt>Time margin</dt><dd>{activeComparison.result.minimum_margin?.toFixed(3) ?? "—"} s</dd></div>
                      </dl>
                      <p>{activeComparison.result.disclaimer}</p>
                    </details>
                  </div>
                ) : null}
              </div>
            ) : null}
          </aside>
        </section>

        {step === 5 ? (
          <RiskResults
            comparisons={comparisons}
            activeId={activeComparison?.id ?? null}
            onSelect={setActiveComparisonId}
            onClear={() => {
              setComparisons([]);
              setActiveComparisonId(null);
            }}
          />
        ) : null}

        <section className="method-strip">
          <div><span>01</span><strong>DETECT ONCE</strong><p>วิเคราะห์ภาพเพียงครั้งเดียวต่อจังหวะ</p></div>
          <div><span>02</span><strong>CALIBRATE</strong><p>แปลง Pixel เป็นระยะบนสนามจริง</p></div>
          <div><span>03</span><strong>SIMULATE FAST</strong><p>เปลี่ยนเป้าหมายโดยไม่ Detect ซ้ำ</p></div>
        </section>
      </main>

      <footer>
        <strong>TactiVision MVP</strong>
        <p>เปอร์เซ็นต์เป็นดัชนีความเสี่ยงจากแบบจำลอง ไม่ใช่ความน่าจะเป็นจากข้อมูลการแข่งขันจริง</p>
      </footer>
    </div>
  );
}

export default App;

