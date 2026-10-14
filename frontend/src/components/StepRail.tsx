const steps = [
  ["01", "เลือกภาพ"],
  ["02", "ตรวจผู้เล่น"],
  ["03", "Calibration"],
  ["04", "คนครองบอล"],
  ["05", "เปรียบเทียบ"],
] as const;

interface StepRailProps {
  current: number;
  onStep: (step: number) => void;
  maxStep: number;
}

export function StepRail({ current, onStep, maxStep }: StepRailProps) {
  return (
    <nav aria-label="ขั้นตอนการวิเคราะห์" className="step-rail">
      {steps.map(([number, label], index) => {
        const step = index + 1;
        const enabled = step <= maxStep;
        return (
          <button
            key={number}
            type="button"
            disabled={!enabled}
            aria-current={current === step ? "step" : undefined}
            className={`step-item ${current === step ? "step-active" : ""} ${step < current ? "step-done" : ""}`}
            onClick={() => enabled && onStep(step)}
          >
            <span>{number}</span>
            <strong>{label}</strong>
          </button>
        );
      })}
    </nav>
  );
}

