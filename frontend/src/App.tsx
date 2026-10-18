import { useEffect, useMemo, useRef, useState } from "react";
import { calibrateImage, detectImage, simulatePass } from "./api";
import { DetectionReview } from "./components/DetectionReview";
import { FieldMap } from "./components/FieldMap";
import { PassAnalysisBoard } from "./components/PassAnalysisBoard";
import { PitchWorkspace } from "./components/PitchWorkspace";
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
  SimulationSelection,
  SimulationTarget,
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

const landmarkGroups = [
  {
    title: "เส้นขอบและเส้นแบ่งครึ่งสนาม",
    points: [
      { label: "มุมสนามซ้ายบน", field: { x: 0, y: 0 } },
      { label: "เส้นบนตรงกลาง", field: { x: 52.5, y: 0 } },
      { label: "มุมสนามขวาบน", field: { x: 105, y: 0 } },
      { label: "เส้นแบ่งครึ่งสนามฝั่งซ้าย", field: { x: 0, y: 34 } },
      { label: "เส้นแบ่งครึ่งสนามฝั่งขวา", field: { x: 105, y: 34 } },
      { label: "มุมสนามซ้ายล่าง", field: { x: 0, y: 68 } },
      { label: "เส้นล่างตรงกลาง", field: { x: 52.5, y: 68 } },
      { label: "มุมสนามขวาล่าง", field: { x: 105, y: 68 } },
    ],
  },
  {
    title: "วงกลมกลางสนาม",
    points: [
      { label: "จุดกลางสนาม", field: { x: 52.5, y: 34 } },
      { label: "วงกลมกลางสนามด้านบน", field: { x: 52.5, y: 24.85 } },
      { label: "วงกลมกลางสนามด้านล่าง", field: { x: 52.5, y: 43.15 } },
      { label: "วงกลมกลางสนามด้านซ้าย", field: { x: 43.35, y: 34 } },
      { label: "วงกลมกลางสนามด้านขวา", field: { x: 61.65, y: 34 } },
    ],
  },
  {
    title: "จุดโทษ",
    points: [
      { label: "จุดโทษฝั่งซ้าย", field: { x: 11, y: 34 } },
      { label: "จุดโทษฝั่งขวา", field: { x: 94, y: 34 } },
    ],
  },
  {
    title: "มุมกรอบเขตโทษ",
    points: [
      { label: "กรอบเขตโทษซ้ายบน ด้านเส้นประตู", field: { x: 0, y: 13.84 } },
      { label: "กรอบเขตโทษซ้ายบน ด้านใน", field: { x: 16.5, y: 13.84 } },
      { label: "กรอบเขตโทษซ้ายล่าง ด้านเส้นประตู", field: { x: 0, y: 54.16 } },
      { label: "กรอบเขตโทษซ้ายล่าง ด้านใน", field: { x: 16.5, y: 54.16 } },
      { label: "กรอบเขตโทษขวาบน ด้านใน", field: { x: 88.5, y: 13.84 } },
      { label: "กรอบเขตโทษขวาบน ด้านเส้นประตู", field: { x: 105, y: 13.84 } },
      { label: "กรอบเขตโทษขวาล่าง ด้านใน", field: { x: 88.5, y: 54.16 } },
      { label: "กรอบเขตโทษขวาล่าง ด้านเส้นประตู", field: { x: 105, y: 54.16 } },
    ],
  },
  {
    title: "มุมกรอบประตู",
    points: [
      { label: "กรอบประตูซ้ายบน ด้านเส้นประตู", field: { x: 0, y: 24.84 } },
      { label: "กรอบประตูซ้ายบน ด้านใน", field: { x: 5.5, y: 24.84 } },
      { label: "กรอบประตูซ้ายล่าง ด้านเส้นประตู", field: { x: 0, y: 43.16 } },
      { label: "กรอบประตูซ้ายล่าง ด้านใน", field: { x: 5.5, y: 43.16 } },
      { label: "กรอบประตูขวาบน ด้านใน", field: { x: 99.5, y: 24.84 } },
      { label: "กรอบประตูขวาบน ด้านเส้นประตู", field: { x: 105, y: 24.84 } },
      { label: "กรอบประตูขวาล่าง ด้านใน", field: { x: 99.5, y: 43.16 } },
      { label: "กรอบประตูขวาล่าง ด้านเส้นประตู", field: { x: 105, y: 43.16 } },
    ],
  },
  {
    title: "จุดตัดส่วนโค้งกรอบเขตโทษ",
    points: [
      { label: "ส่วนโค้งกรอบเขตโทษซ้ายบน", field: { x: 16.5, y: 26.69 } },
      { label: "ส่วนโค้งกรอบเขตโทษซ้ายล่าง", field: { x: 16.5, y: 41.31 } },
      { label: "ส่วนโค้งกรอบเขตโทษขวาบน", field: { x: 88.5, y: 26.69 } },
      { label: "ส่วนโค้งกรอบเขตโทษขวาล่าง", field: { x: 88.5, y: 41.31 } },
    ],
  },
] as const;

let nextLandmarkNumber = 1;
const landmarks = landmarkGroups
  .flatMap((group) => group.points.map((point) => ({ ...point, group: group.title })))
  .map((landmark) => {
    if (landmark.label === "จุดกลางสนาม") return { ...landmark, code: "P12" };
    if (nextLandmarkNumber === 12) nextLandmarkNumber += 1;
    return { ...landmark, code: `P${nextLandmarkNumber++}` };
  });

function calibrationErrorLevel(error: number | null) {
  if (error === null) return null;
  if (error <= 0.75) return { label: "ดี", className: "good" };
  if (error <= 2) return { label: "ควรตรวจซ้ำ", className: "warning" };
  return { label: "สูงเกินเกณฑ์", className: "danger" };
}

function hasCalibrationPair(pair: CalibrationPair, landmark: (typeof landmarks)[number]) {
  return pair.label.startsWith(`${landmark.code}:`);
}

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
  if (!ball || players.length === 0) return null;
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

function analysisProgressLabel(progress: number) {
  if (progress < 24) return "กำลังอัปโหลดภาพเข้าสู่ระบบ";
  if (progress < 55) return "โมเดลกำลังตรวจจับผู้เล่นและลูกบอล";
  if (progress < 78) return "กำลังแยกทีมจากสีชุดแข่งขัน";
  if (progress < 100) return "กำลังเตรียมพิกัดและผลวิเคราะห์";
  return "วิเคราะห์ภาพเสร็จแล้ว";
}

function App() {
  const fileInput = useRef<HTMLInputElement>(null);
  const controlPanel = useRef<HTMLElement>(null);
  const simulationRequest = useRef<AbortController | null>(null);
  const simulationSelection = useRef<SimulationSelection | null>(null);
  const [step, setStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<DetectResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [manualMode, setManualMode] = useState(false);
  const [pendingLandmark, setPendingLandmark] = useState<(typeof landmarks)[number] | null>(null);
  const [calibrationPairs, setCalibrationPairs] = useState<CalibrationPair[]>([]);
  const [showGuide, setShowGuide] = useState(false);
  const [candidateCarrierId, setCandidateCarrierId] = useState<string | null>(null);
  const [carrierId, setCarrierId] = useState<string | null>(null);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [activeComparisonId, setActiveComparisonId] = useState<string | null>(null);
  const [pendingSlot, setPendingSlot] = useState<number | null>(null);
  const [parameters, setParameters] = useState<SimulationParameters>(defaultParameters);
  const [passType, setPassType] = useState<PassType>("ground");
  const [targetMode, setTargetMode] = useState<TargetMode>("receiver");
  const [runnerId, setRunnerId] = useState<string | null>(null);

  const activeComparison = useMemo(
    () => comparisons.find((item) => item.id === activeComparisonId) ?? null,
    [activeComparisonId, comparisons],
  );
  const candidate = useMemo(
    () => analysis?.detections.find((item) => item.id === candidateCarrierId) ?? null,
    [analysis, candidateCarrierId],
  );

  useEffect(() => () => {
    simulationRequest.current?.abort();
    simulationRequest.current = null;
  }, []);

  useEffect(() => {
    if (analysisProgress === null || analysisProgress >= 92) return;
    const timer = window.setInterval(() => {
      setAnalysisProgress((current) => {
        if (current === null) return null;
        const increment = current < 30 ? 7 : current < 65 ? 4 : 2;
        return Math.min(92, current + increment);
      });
    }, 650);
    return () => window.clearInterval(timer);
  }, [analysisProgress]);

  useEffect(() => {
    const content = controlPanel.current?.querySelector<HTMLElement>(".panel-content");
    if (content) content.scrollTop = 0;
  }, [step]);

  function cancelSimulation() {
    if (simulationRequest.current) {
      simulationRequest.current.abort();
      simulationRequest.current = null;
      setBusy(false);
    }
    simulationSelection.current = null;
    setPendingSlot(null);
  }

  function resetAnalysis(nextImageUrl: string | null = null) {
    cancelSimulation();
    if (imageUrl?.startsWith("blob:")) URL.revokeObjectURL(imageUrl);
    setImageUrl(nextImageUrl);
    setAnalysis(null);
    setStep(1);
    setMaxStep(1);
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
    setPendingSlot(null);
    setError(null);
    setNotice(null);
    setAnalysisProgress(null);
  }

  async function handleFile(file: File) {
    const nextUrl = URL.createObjectURL(file);
    resetAnalysis(nextUrl);
    setBusy(true);
    setAnalysisProgress(6);
    setNotice("กำลังตรวจผู้เล่น แบ่งทีม และลอง Auto Calibration…");
    try {
      const result = await detectImage(file);
      setAnalysisProgress(100);
      await new Promise((resolve) => window.setTimeout(resolve, 300));
      setAnalysis(result);
      setManualMode(result.calibration.status !== "success");
      setStep(2);
      setMaxStep(2);
      setNotice(`วิเคราะห์ภาพด้วย ${result.detector.model} สำเร็จ`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "วิเคราะห์ภาพไม่สำเร็จ");
      setNotice(null);
    } finally {
      setAnalysisProgress(null);
      setBusy(false);
    }
  }

  function loadDemo() {
    resetAnalysis("/demo-pitch.svg");
    const result = cloneDemo();
    setAnalysis(result);
    setStep(2);
    setMaxStep(2);
    setNotice("กำลังใช้ฉากและ Detection ตัวอย่าง ข้อมูลส่วนนี้ไม่ใช่ผลจาก AI");
  }

  function updateDetection(id: string, patch: Partial<Detection>) {
    cancelSimulation();
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
    cancelSimulation();
    setAnalysis((current) =>
      current
        ? { ...current, detections: current.detections.filter((item) => item.id !== id) }
        : current,
    );
    setCarrierId(null);
    setCandidateCarrierId(null);
    setRunnerId(null);
    setComparisons([]);
    setActiveComparisonId(null);
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

  function clearCalibrationFailureFeedback(message: string) {
    setAnalysis((current) => {
      if (
        !current
        || current.calibration.status !== "needs_manual"
        || current.calibration.reprojection_error === null
      ) return current;
      return {
        ...current,
        calibration: {
          ...current.calibration,
          confidence: 0,
          reprojection_error: null,
          outlier_indices: [],
          message,
        },
      };
    });
  }

  function handleCanvasClick(point: Point2D) {
    if (step === 3 && manualMode) {
      if (busy) return;
      if (!pendingLandmark) {
        setError("เลือกชื่อจุดอ้างอิงก่อน แล้วจึงคลิกตำแหน่งเดียวกันบนภาพ");
        return;
      }
      setCalibrationPairs((current) => [
        ...current.filter((pair) => !hasCalibrationPair(pair, pendingLandmark)),
        { label: `${pendingLandmark.code}: ${pendingLandmark.label}`, image: point, field: pendingLandmark.field },
      ]);
      clearCalibrationFailureFeedback("แก้ไขจุดอ้างอิงแล้ว เมื่อพร้อมให้คำนวณ Manual Calibration อีกครั้ง");
      setNotice(`บันทึก ${pendingLandmark.code} · ${pendingLandmark.label} แล้ว`);
      setPendingLandmark(null);
      setError(null);
      return;
    }

    if (step === 5 && carrierId && analysis?.calibration.matrix) {
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
      if (targetMode !== "through_ball") setTargetMode("space");
      void runSimulation(
        targetMode === "through_ball"
          ? { type: "through_ball", receiver_id: runnerId!, position: fieldPoint }
          : { type: "space", position: fieldPoint },
        point,
        targetLabel,
      );
    }
  }

  function handleFieldMapClick(fieldPoint: Point2D) {
    if (step !== 5 || !analysis || !carrierId || !analysis.calibration.matrix) return;
    if (targetMode === "through_ball" && !runnerId) {
      setError("เลือกเพื่อนร่วมทีมที่จะวิ่งรับบอลก่อน แล้วคลิกจุดว่างบนแผนผัง 2D");
      return;
    }
    const inverse = invertMatrix3(analysis.calibration.matrix);
    const targetPixel = inverse ? applyHomography(fieldPoint, inverse) : null;
    if (!targetPixel) {
      setError("ไม่สามารถแปลงจุดบนสนามกลับไปยังภาพจริงได้");
      return;
    }
    const targetLabel = `${targetMode === "through_ball" ? `แทงให้ ${runnerId} ไปที่` : "พื้นที่ว่าง"} ${fieldPoint.x.toFixed(1)}, ${fieldPoint.y.toFixed(1)} m`;
    if (targetMode !== "through_ball") setTargetMode("space");
    void runSimulation(
      targetMode === "through_ball"
        ? { type: "through_ball", receiver_id: runnerId!, position: fieldPoint }
        : { type: "space", position: fieldPoint },
      targetPixel,
      targetLabel,
    );
  }

  function removeCalibrationPoints(label?: string) {
    if (busy) return;
    setCalibrationPairs((current) => label ? current.filter((pair) => pair.label !== label) : []);
    clearCalibrationFailureFeedback("เลือกจุดอ้างอิงใหม่ให้ตรงจุดตัดของเส้นสนามและกระจายรอบภาพ");
    setPendingLandmark((current) => !label || current?.code === label.split(":")[0] ? null : current);
    setError(null);
    setNotice(label ? `ลบจุด “${label}” แล้ว สามารถเลือกใหม่ได้` : "ล้างจุดอ้างอิงทั้งหมดแล้ว");
  }

  async function submitManualCalibration() {
    if (!analysis || calibrationPairs.length < 4) {
      setError("ต้องเลือกจุดอ้างอิงอย่างน้อย 4 จุด");
      return;
    }
    cancelSimulation();
    setComparisons([]);
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
    setNotice(suggestion
      ? `AI แนะนำ ${suggestion} เป็น Ball Carrier กรุณาตรวจและยืนยัน`
      : "ไม่สามารถแนะนำคนครองบอลได้ กรุณาคลิกเลือกผู้เล่นบนภาพ");
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
    cancelSimulation();
    if (carrierId !== candidate.id) setComparisons([]);
    setCarrierId(candidate.id);
    setRunnerId(null);
    setStep(5);
    setMaxStep(5);
    setError(null);
    setNotice(`ล็อก ${candidate.id} เป็น Ball Carrier แล้ว คลิกเพื่อนร่วมทีมหรือพื้นที่ว่าง`);
  }

  async function runSimulation(
    target: SimulationTarget,
    targetPixel: Point2D,
    targetLabel: string,
    nextPassType: PassType = passType,
    nextParameters: SimulationParameters = parameters,
    replaceSlot?: number,
  ) {
    if (!analysis || !carrierId) return;
    simulationRequest.current?.abort();
    const request = new AbortController();
    const activeSlot = comparisons.findIndex((item) => item.id === activeComparisonId);
    const targetSlot = replaceSlot ?? (comparisons.length < 3 ? comparisons.length : Math.max(0, activeSlot));
    simulationRequest.current = request;
    simulationSelection.current = { target, targetPixel, targetLabel };
    setPendingSlot(targetSlot);
    setBusy(true);
    setError(null);
    setNotice(`กำลังคำนวณ ${targetLabel} · ${nextPassType.toUpperCase()}…`);
    try {
      const result = await simulatePass({
        detections: analysis.detections,
        carrierId,
        passType: nextPassType,
        target,
        parameters: nextParameters,
        signal: request.signal,
      });
      if (request.signal.aborted || simulationRequest.current !== request) return;
      let interceptPixel: Point2D | null = null;
      if (result.intercept_point && analysis.calibration.matrix) {
        const inverse = invertMatrix3(analysis.calibration.matrix);
        if (inverse) interceptPixel = applyHomography(result.intercept_point, inverse);
      }
      const comparison: Comparison = {
        id: crypto.randomUUID(),
        target,
        targetLabel,
        targetPixel,
        parameters: { ...nextParameters },
        interceptPixel,
        result,
      };
      setComparisons((current) => {
        if (targetSlot < current.length) return current.map((item, index) => index === targetSlot ? comparison : item);
        return [...current, comparison].slice(0, 3);
      });
      setActiveComparisonId(comparison.id);
      setNotice(`คำนวณ ${targetLabel} แล้ว — คะแนนความเสี่ยง ${result.risk_percent}/100`);
    } catch (caught) {
      if (request.signal.aborted || simulationRequest.current !== request) return;
      setError(caught instanceof Error ? caught.message : "คำนวณ Simulation ไม่สำเร็จ");
      setNotice(null);
    } finally {
      if (simulationRequest.current === request) {
        simulationRequest.current = null;
        setPendingSlot(null);
        setBusy(false);
      }
    }
  }

  function changePassType(nextPassType: PassType) {
    if (nextPassType === passType) return;
    setPassType(nextPassType);
    setError(null);
    const selection = simulationSelection.current;
    if (selection) {
      const slot = comparisons.findIndex((item) => item.id === activeComparisonId);
      void runSimulation(selection.target, selection.targetPixel, selection.targetLabel, nextPassType, parameters, slot >= 0 ? slot : undefined);
    }
  }

  function changeTargetMode(nextMode: TargetMode) {
    if (nextMode === targetMode) return;
    cancelSimulation();
    setTargetMode(nextMode);
    setRunnerId(null);
    setError(null);
    setNotice(nextMode === "receiver"
      ? "เลือกผู้รับบอลบนภาพจริงหรือแผนผัง 2D เพื่อคำนวณใหม่"
      : nextMode === "space"
        ? "คลิกพื้นที่ว่างบนภาพจริงหรือแผนผัง 2D เพื่อคำนวณใหม่"
        : "เลือกเพื่อนที่จะวิ่งรับบอล แล้วคลิกจุดว่างข้างหน้าบนภาพจริงหรือแผนผัง 2D");
  }

  function changeRunner(id: string) {
    if (id === runnerId) return;
    cancelSimulation();
    setRunnerId(id);
    setError(null);
    setNotice(`เลือก ${id} เป็นผู้วิ่งแล้ว คลิกจุดว่างข้างหน้าเพื่อคำนวณใหม่`);
  }

  function changeParameters(nextParameters: SimulationParameters) {
    setParameters(nextParameters);
    const selection = simulationSelection.current;
    if (selection) {
      const slot = comparisons.findIndex((item) => item.id === activeComparisonId);
      void runSimulation(selection.target, selection.targetPixel, selection.targetLabel, passType, nextParameters, slot >= 0 ? slot : undefined);
    }
  }

  function selectComparison(id: string) {
    const comparison = comparisons.find((item) => item.id === id);
    if (!comparison) return;
    cancelSimulation();
    simulationSelection.current = comparison;
    setPassType(comparison.result.pass_type);
    setTargetMode(comparison.target.type);
    setRunnerId(comparison.target.type === "through_ball" ? comparison.target.receiver_id ?? null : null);
    setParameters({ ...comparison.parameters });
    setActiveComparisonId(id);
    setError(null);
    setNotice(`แสดงผล ${comparison.targetLabel} · ${comparison.result.pass_type.toUpperCase()}`);
  }

  function handleDetectionClick(detection: Detection) {
    if (step === 4 && detection.class_name !== "ball" && detection.class_name !== "referee") {
      setCandidateCarrierId(detection.id);
      setNotice(`เลือก ${detection.id} เป็น Ball Carrier รอยืนยัน`);
      setError(null);
      return;
    }
    if (step !== 5 || !analysis || !carrierId) return;
    if (targetMode === "through_ball") {
      setNotice("โหมดแทงทะลุช่องทำงานอยู่ — เลือกผู้วิ่งในตั้งค่าขั้นสูง แล้วคลิกจุดว่างข้างหน้า");
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
    setTargetMode("receiver");
    void runSimulation(
      { type: "receiver", receiver_id: detection.id, position: detection.field_position },
      detection.foot_pixel,
      `ส่งให้ ${detection.id}`,
    );
  }

  const errorLevel = calibrationErrorLevel(analysis?.calibration.reprojection_error ?? null);
  const calibrationOutlierIndices = analysis?.calibration.outlier_indices ?? [];
  const calibrationOutlierLabels = calibrationOutlierIndices
    .map((index) => calibrationPairs[index]?.label.split(":")[0])
    .filter((label): label is string => Boolean(label));

  function renderLandmarkCategoryControls() {
    return (
      <section className="visual-landmark-selector" aria-label="เลือกจุดอ้างอิงสำหรับ Manual Calibration">
        <header>
          <div><span className="eyebrow">MANUAL CALIBRATION</span><h3>เลือกจุดอ้างอิงที่มองเห็นในภาพ</h3></div>
          <p>เลือกอย่างน้อย 4 จุด แล้วคลิกตำแหน่งเดียวกันบนภาพการแข่งขันด้านบน</p>
        </header>
        <div className="landmark-categories">
          {landmarkGroups.map((group) => {
            const groupLandmarks = landmarks.filter((landmark) => landmark.group === group.title);
            const selectedCount = groupLandmarks.filter((landmark) =>
              calibrationPairs.some((pair) => hasCalibrationPair(pair, landmark)),
            ).length;
            return (
              <details className="landmark-category" key={group.title} open={group.title === "วงกลมกลางสนาม"}>
                <summary><span>{group.title}</span><small>{selectedCount}/{groupLandmarks.length}</small></summary>
                <div className="landmark-grid">
                  {groupLandmarks.map((landmark) => {
                    const completed = calibrationPairs.some((pair) => hasCalibrationPair(pair, landmark));
                    return (
                      <button
                        type="button"
                        key={landmark.label}
                        className={`${pendingLandmark?.label === landmark.label ? "pending" : ""} ${completed ? "completed" : ""}`}
                        aria-pressed={pendingLandmark?.label === landmark.label}
                        disabled={busy}
                        onClick={() => setPendingLandmark(landmark)}
                      >
                        <span>{completed ? "✓" : landmark.code}</span>{landmark.label}
                      </button>
                    );
                  })}
                </div>
              </details>
            );
          })}
        </div>
        <footer>
          <p className="counter">เลือกแล้ว {calibrationPairs.length}/4 จุดขั้นต่ำ</p>
          <button className="primary-button" type="button" disabled={busy || calibrationPairs.length < 4} onClick={() => void submitManualCalibration()}>
            คำนวณ Manual Calibration <span>→</span>
          </button>
        </footer>
      </section>
    );
  }

  return (
    <div className="analysis-page">
      <main id="top" className="analysis-main">
        <section className="tool-header">
          <div className="tool-title-wrap">
            <span className="tool-badge">ANALYSIS WORKSPACE · TACTICAL PASS COMPARATOR</span>
            <h1>ระบบวิเคราะห์และจำลองความเสี่ยงในการจ่ายบอล</h1>
            <p>
              ประเมินทางเลือกการส่งบอลจากภาพนิ่งจังหวะการแข่งขัน • คำนวณความเสี่ยงในการถูกตัดบอลบนระนาบสนามจริง 105 × 68 เมตร ด้วยโมเดลคิเนมาติกส์
            </p>
          </div>
          <div className="tool-meta-badge">
            <span className="meta-label">WORKSPACE STATUS</span>
            <span className="meta-value">{busy ? "PROCESSING" : "READY"} · 105 × 68 M</span>
          </div>
          <button className="analysis-guide-button" type="button" onClick={() => setShowGuide(true)}>คู่มือการใช้งาน</button>
        </section>

        <StepRail current={step} maxStep={maxStep} onStep={(nextStep) => {
          if (step === 5 && nextStep !== 5) cancelSimulation();
          setStep(nextStep);
        }} />

        {error ? (
          <div className="alert error-alert" role="alert">
            <span className="alert-icon" aria-hidden="true">!</span>
            <span><strong>ข้อความแจ้งเตือน</strong>{error}</span>
          </div>
        ) : null}
        {analysisProgress !== null ? (
          <div className="alert notice-alert analysis-progress-alert" role="status">
            <div><span>{analysisProgressLabel(analysisProgress)}</span><strong>{Math.round(analysisProgress)}%</strong></div>
            <div className="analysis-progress-track" role="progressbar" aria-label="ความคืบหน้าการวิเคราะห์ภาพโดยประมาณ" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(analysisProgress)}>
              <span style={{ width: `${analysisProgress}%` }} />
            </div>
          </div>
        ) : notice ? <div className="alert notice-alert" role="status">{notice}</div> : null}

        {step === 5 && analysis && carrierId ? (
          <PassAnalysisBoard
            analysis={analysis}
            imageUrl={imageUrl}
            carrierId={carrierId}
            comparisons={comparisons}
            activeId={activeComparisonId}
            pendingSlot={pendingSlot}
            passType={passType}
            targetMode={targetMode}
            runnerId={runnerId}
            parameters={parameters}
            calibrationPairs={calibrationPairs}
            onPassTypeChange={changePassType}
            onDetectionClick={handleDetectionClick}
            onCanvasClick={handleCanvasClick}
            onFieldClick={handleFieldMapClick}
            onSelectComparison={selectComparison}
            onClearComparisons={() => {
              cancelSimulation();
              setComparisons([]);
              setActiveComparisonId(null);
              setNotice("ล้างผลแล้ว เลือกเป้าหมายเพื่อคำนวณใหม่");
            }}
            onTargetModeChange={changeTargetMode}
            onRunnerChange={changeRunner}
            onParametersChange={changeParameters}
            onResetParameters={() => changeParameters(defaultParameters)}
          />
        ) : (
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
              calibrationOutlierIndices={calibrationOutlierIndices}
              targetPixel={activeComparison?.targetPixel ?? null}
              interceptPixel={activeComparison?.interceptPixel ?? null}
              passType={activeComparison?.result.pass_type ?? passType}
              onDetectionClick={handleDetectionClick}
              onCanvasClick={handleCanvasClick}
            />
            {step === 3 && analysis && manualMode ? renderLandmarkCategoryControls() : null}
            {step === 3 && analysis?.calibration.status === "success" && !manualMode ? (
              <div className="calibration-image-action">
                <div>
                  <span>พิกัดสนามพร้อมใช้งาน</span>
                  <strong>ความเชื่อมั่น {Math.round((analysis?.calibration.confidence ?? 0) * 100)}% · ตรวจภาพแล้วไปขั้นถัดไป</strong>
                </div>
                <button className="primary-button" type="button" onClick={acceptCalibration}>ใช้ผลพิกัดสนามนี้และไปต่อ <span>→</span></button>
              </div>
            ) : null}
            {analysis && step >= 3 && analysis.calibration.status === "success" && !manualMode ? (
              <FieldMap
                detections={analysis.detections}
                carrierId={carrierId}
                candidateCarrierId={candidateCarrierId}
                stage={step}
                targetMode={targetMode}
                comparisons={[]}
                activeId={null}
                onDetectionClick={handleDetectionClick}
                onFieldClick={handleFieldMapClick}
              />
            ) : null}
            <div className="legend">
              <span><i className="dot team-a" />ทีม A (สีฟ้า)</span>
              <span><i className="dot team-b" />ทีม B (สีแดง)</span>
              <span><i className="dot target-dot" />เป้าหมายส่งบอล</span>
              <span><i className="cross">×</i>จุดเสี่ยงถูกสกัด</span>
            </div>
          </div>

          <aside className="control-panel" ref={controlPanel}>
            {step === 1 ? (
              <div className="panel-content intro-panel">
                <span className="panel-number">01</span>
                <span className="eyebrow">ขั้นตอนที่ 1</span>
                <h2>เลือกภาพการแข่งขัน</h2>
                <p>เลือกภาพมุมกว้างที่เห็นผู้เล่นและเส้นสนามชัดเจน รองรับไฟล์ JPEG, PNG และ WebP ขนาดไม่เกิน 10 MB</p>
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
                  อัปโหลดภาพจริงจากเครื่อง <span>→</span>
                </button>
                <button className="secondary-button" type="button" disabled={busy} onClick={loadDemo}>
                  ลองฉากตัวอย่าง (ไม่ต้องใช้ภาพ)
                </button>
                <small>ฉากตัวอย่างใช้ชุดข้อมูลจำลองเพื่อทดสอบระบบ โดยไม่ต้องเชื่อมต่อโมเดล AI ตรวจจับ</small>
              </div>
            ) : null}

            {step === 2 && analysis ? (
              <div className="panel-content">
                <span className="panel-number">02</span>
                <span className="eyebrow">ขั้นตอนที่ 2</span>
                <h2>ตรวจผู้เล่นและทีม</h2>
                <p>ตรวจสอบความถูกต้องของนักเตะ สลับบทบาทหรือทีมหาก AI จัดกลุ่มผิด และลบตำแหน่งลูกบอลที่เกินมาได้</p>
                <DetectionReview detections={analysis.detections} onUpdate={updateDetection} onRemove={removeDetection} />
                <button className="primary-button" type="button" onClick={continueToCalibration}>
                  ยืนยันผู้เล่นและไปเทียบพิกัดสนาม <span>→</span>
                </button>
              </div>
            ) : null}

            {step === 3 && analysis ? (
              <div className="panel-content">
                <span className="panel-number">03</span>
                <span className="eyebrow">ขั้นตอนที่ 3 · พิกเซลภาพ ➔ พิกัดสนามเมตร</span>
                <h2>เทียบพิกัดสนาม (105 × 68 ม.)</h2>
                <div className={`calibration-card ${analysis.calibration.status} ${errorLevel?.className ?? ""}`}>
                  <div>
                    <strong>{analysis.calibration.method === "auto" ? "เทียบพิกัดอัตโนมัติ" : "กำหนดจุดด้วยตนเอง"}</strong>
                    <span>ความเชื่อมั่น {Math.round(analysis.calibration.confidence * 100)}%</span>
                  </div>
                  <p>{analysis.calibration.message}</p>
                  {analysis.calibration.reprojection_error !== null && errorLevel ? (
                    <div className={`reprojection-status ${errorLevel.className}`}>
                      <span>ความคลาดเคลื่อนพิกัดเฉลี่ย:</span>
                      <strong>{analysis.calibration.reprojection_error.toFixed(2)} เมตร ({errorLevel.label})</strong>
                    </div>
                  ) : null}
                  {errorLevel?.className === "danger" ? (
                    <div className="calibration-recovery" role="alert">
                      <strong>ยังไม่ควรใช้ผลนี้</strong>
                      <span>
                        {calibrationOutlierLabels.length > 0
                          ? `จุดที่ควรตรวจและเลือกใหม่: ${calibrationOutlierLabels.join(", ")}`
                          : "ลบจุดเดิม แล้วเลือกจุดตัดของเส้นสนามที่มองเห็นชัดและกระจายรอบภาพใหม่"}
                      </span>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                          if (calibrationOutlierIndices.length > 0) {
                            const outliers = new Set(calibrationOutlierIndices);
                            setCalibrationPairs((current) => current.filter((_, index) => !outliers.has(index)));
                          } else {
                            setCalibrationPairs([]);
                          }
                          setAnalysis((current) => current ? {
                            ...current,
                            calibration: {
                              ...current.calibration,
                              confidence: 0,
                              reprojection_error: null,
                              outlier_indices: [],
                              message: "เลือกจุดอ้างอิงใหม่ให้ตรงจุดตัดของเส้นสนามและกระจายรอบภาพ",
                            },
                          } : current);
                          setPendingLandmark(null);
                          setError(null);
                          setNotice(calibrationOutlierIndices.length > 0
                            ? "ลบจุดที่คลาดเคลื่อนแล้ว กรุณาเลือกจุดเหล่านั้นใหม่"
                            : "ล้างจุดเดิมแล้ว กรุณาเลือกจุดอ้างอิงใหม่");
                        }}
                      >
                        {calibrationOutlierIndices.length > 0 ? "ลบจุดที่ควรแก้แล้วเลือกใหม่" : "ล้างจุดเดิมแล้วเลือกใหม่"}
                      </button>
                    </div>
                  ) : null}
                </div>
                {!manualMode && analysis.calibration.status === "success" ? (
                  <button className="text-button" type="button" onClick={() => setManualMode(true)}>
                    ต้องการเลือกจุดเทียบสนามด้วยตนเอง
                  </button>
                ) : (
                  <div className="manual-calibration">
                    <p><strong>ภาพไม่จำเป็นต้องเห็นทั้งสนาม</strong> เลือกจุดที่มองเห็นชัดอย่างน้อย 4 จุด กระจายกัน และไม่อยู่แนวเดียวกัน แล้วคลิกจุดเดียวกันบนภาพใหญ่</p>
                    <div className="landmark-guide" aria-label="แผนผังตำแหน่งจุดอ้างอิงบนสนาม">
                      <div className="landmark-guide-heading">
                        <span>แผนผังสนามอ้างอิง</span>
                        <small>{landmarks.length} จุดอ้างอิง · P12 คือจุดกลางสนาม</small>
                      </div>
                      <div className="mini-pitch">
                        <span className="mini-pitch-halfway" />
                        <span className="mini-pitch-circle" />
                        <span className="mini-pitch-box mini-pitch-box-left" />
                        <span className="mini-pitch-box mini-pitch-box-right" />
                        {landmarks.map((landmark) => {
                          const completed = calibrationPairs.some((pair) => hasCalibrationPair(pair, landmark));
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
                              disabled={busy}
                              aria-label={`${landmark.code}: ${landmark.label}${completed ? " เลือกแล้ว" : ""}`}
                              aria-pressed={pending}
                              onClick={() => setPendingLandmark(landmark)}
                            >
                              {completed ? "✓" : landmark.code}
                            </button>
                          );
                        })}
                      </div>
                      <p className={`landmark-instruction ${pendingLandmark ? "active" : ""}`}>
                        {pendingLandmark
                          ? `เลือก ${pendingLandmark.code}: ${pendingLandmark.label} แล้ว — คลิกตำแหน่งเดียวกันบนภาพใหญ่`
                          : "กดหมายเลขที่มองเห็นชัดในภาพ แล้วไปคลิกตำแหน่งเดียวกันบนภาพใหญ่"}
                      </p>
                      <div className="calibration-example">
                        <strong>ตัวอย่างการวางจุด</strong>
                        <span>✓ วางทับจุดตัดของเส้นจริง</span>
                        <span>× อย่าวางบนตัวผู้เล่น เงา หรือพื้นที่หญ้าใกล้เคียง</span>
                        <small>เลือกจุดที่กระจายรอบพื้นที่ภาพ ช่วยลดอาการ Marker กระโดดจาก Homography ที่ไม่เสถียร</small>
                      </div>
                      {pendingLandmark ? (
                        <button
                          className="text-button"
                          type="button"
                          disabled={busy}
                          onClick={() => {
                            setPendingLandmark(null);
                            setError(null);
                          }}
                        >
                          ยกเลิกการเลือกจุดนี้
                        </button>
                      ) : null}
                    </div>
                    {calibrationPairs.length > 0 ? (
                      <section className="calibration-points" aria-label="จุดอ้างอิงที่เลือกแล้ว">
                        <div className="calibration-points-heading">
                          <h3>จุดที่เลือก ({calibrationPairs.length})</h3>
                          <button
                            className="text-button danger"
                            type="button"
                            disabled={busy}
                            onClick={() => removeCalibrationPoints()}
                          >
                            ล้างทั้งหมด
                          </button>
                        </div>
                        <ol>
                          {calibrationPairs.map((pair, index) => (
                            <li className={calibrationOutlierIndices.includes(index) ? "calibration-point-error" : ""} key={pair.label}>
                              <span className="calibration-point-index">{pair.label.split(":")[0]}</span>
                              <span>{pair.label.slice(pair.label.indexOf(":") + 1).trim()}</span>
                              {calibrationOutlierIndices.includes(index) ? <strong>เลือกใหม่</strong> : null}
                              <button
                                className="text-button danger"
                                type="button"
                                disabled={busy}
                                aria-label={`ลบจุด ${pair.label}`}
                                onClick={() => removeCalibrationPoints(pair.label)}
                              >
                                ลบ
                              </button>
                            </li>
                          ))}
                        </ol>
                      </section>
                    ) : null}
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
                <span className="eyebrow">ขั้นตอนที่ 4</span>
                <h2>ระบุผู้เล่นครองบอล</h2>
                <p>{analysis.detections.some((item) => item.class_name === "ball")
                  ? "ระบบเสนอผู้เล่นที่อยู่ใกล้ลูกบอลที่สุดให้อัตโนมัติ สามารถคลิกกรอบผู้เล่นคนอื่นบนภาพได้หากคำแนะนำไม่ตรงกับจังหวะจริง"
                  : "ไม่พบตำแหน่งลูกบอลที่ชัดเจน กรุณาคลิกเลือกผู้เล่นบนภาพเพื่อระบุคนครองบอลด้วยตนเอง"}</p>
                <div className="carrier-choice">
                  <span>ผู้เล่นที่เลือกครองบอล</span>
                  <strong>{candidate ? candidate.id.toUpperCase() : "ยังไม่ได้เลือก"}</strong>
                  <small>{candidate ? `${candidate.team_id === "team_a" ? "ทีม A (สีฟ้า)" : candidate.team_id === "team_b" ? "ทีม B (สีแดง)" : "ยังไม่ระบุทีม"} · ${candidate.class_name === "goalkeeper" ? "ผู้รักษาประตู" : "ผู้เล่นทั่วไป"}` : "คลิกผู้เล่นบนภาพเพื่อเลือก"}</small>
                </div>
                <button className="primary-button" type="button" disabled={!candidate} onClick={confirmCarrier}>
                  ยืนยันผู้เล่นครองบอลคนนี้ <span>→</span>
                </button>
              </div>
            ) : null}

          </aside>
        </section>
        )}

      </main>

      {showGuide ? (
        <div className="modal-backdrop" onClick={() => setShowGuide(false)} role="dialog" aria-modal="true" aria-labelledby="guide-title">
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="eyebrow">USER MANUAL & WORKFLOW GUIDE</span>
                <h2 id="guide-title">คู่มือการใช้งานเว็บไซต์ TactiVision</h2>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowGuide(false)}
                aria-label="ปิดคู่มือ"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p className="modal-intro">
                TactiVision เป็นเครื่องมือสำหรับผู้ฝึกสอน นักวิเคราะห์แท็กติก และผู้สนใจกีฬาฟุตบอล เพื่อวิเคราะห์และเปรียบเทียบทางเลือกในการจ่ายบอลจากภาพนิ่งจังหวะการแข่งขันจริง โดยมี 5 ขั้นตอนหลัก:
              </p>

              <div className="guide-steps-grid">
                <div className="guide-step-card">
                  <div className="guide-step-header">
                    <span className="step-num">01</span>
                    <h4>เลือกภาพการแข่งขัน</h4>
                  </div>
                  <p>อัปโหลดภาพมุมถ่ายทอดกว้างที่มองเห็นเส้นสนามและนักเตะชัดเจน หรือกดปุ่ม <strong>“ลองฉากตัวอย่าง”</strong> เพื่อทดสอบระบบได้ทันทีโดยไม่ต้องใช้ภาพ</p>
                </div>

                <div className="guide-step-card">
                  <div className="guide-step-header">
                    <span className="step-num">02</span>
                    <h4>ตรวจผู้เล่นและทีม</h4>
                  </div>
                  <p>ระบบตรวจจับนักเตะและแยกสีเสื้อเป็น <strong>ทีม A (สีฟ้า)</strong> กับ <strong>ทีม B (สีแดง)</strong> ให้ตรวจทานบทบาท (ผู้เล่น/ผู้รักษาประตู/ผู้ตัดสิน) ให้ถูกต้อง</p>
                </div>

                <div className="guide-step-card">
                  <div className="guide-step-header">
                    <span className="step-num">03</span>
                    <h4>เทียบพิกัดสนาม (Calibration)</h4>
                  </div>
                  <p>ระบบแปลงภาพมุมกล้องลงสู่ระนาบสนามจริง <strong>105 × 68 เมตร</strong> อัตโนมัติ หรือสามารถคลิกกำหนดจุดอ้างอิงบนสนามอย่างน้อย 4 จุดได้เอง</p>
                </div>

                <div className="guide-step-card">
                  <div className="guide-step-header">
                    <span className="step-num">04</span>
                    <h4>ระบุผู้เล่นครองบอล</h4>
                  </div>
                  <p>คลิกเลือกนักเตะที่เป็นผู้ถือครองบอลและจะเป็นผู้เริ่มจ่ายบอลในจังหวะนั้น เพื่อใช้เป็นจุดเริ่มต้นของวิถีส่งบอล</p>
                </div>

                <div className="guide-step-card">
                  <div className="guide-step-header">
                    <span className="step-num">05</span>
                    <h4>จำลอง & เปรียบเทียบทางเลือก</h4>
                  </div>
                  <p>หน้าเริ่มต้นแสดงภาพการแข่งขันจริงเหมือนเดิม คลิกเพื่อนร่วมทีมเพื่อส่งเข้าเท้าหรือคลิกพื้นที่ว่างได้ทันที และสลับไปดูสนาม 2D/ดูคู่กันเพื่อเทียบเส้นทาง A, B และ C ได้สูงสุด 3 ทางเลือก</p>
                </div>
              </div>

              <div className="guide-notice-box">
                <strong>ความเข้าใจเกี่ยวกับ “ดัชนีความเสี่ยง (Pass Interception Risk)”</strong>
                <p>
                  คะแนนความเสี่ยง 0–100 เป็นดัชนีจากแบบจำลองคิเนมาติกส์ทางฟิสิกส์ (เวลาที่บอลเดินทางเทียบกับเวลาที่ฝ่ายตรงข้ามวิ่งเข้าสกัดบอล) <em>ไม่ใช่เปอร์เซ็นต์ความน่าจะเป็นจากข้อมูลการแข่งขันจริง</em> เพื่อให้การวิเคราะห์แท็กติกมีความโปร่งใสและตรวจสอบตัวแปรได้
                </p>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="primary-button modal-ack-btn" onClick={() => setShowGuide(false)}>
                เข้าใจแล้ว เริ่มใช้งานเว็บไซต์ <span>→</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;


