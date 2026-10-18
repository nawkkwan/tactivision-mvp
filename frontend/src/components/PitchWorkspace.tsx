import { useEffect, useMemo, useRef, useState } from "react";
import { Arrow, Circle, Group, Image as KonvaImage, Label, Layer, Line, Rect, Stage, Tag, Text } from "react-konva";
import type { CalibrationPair, Detection, PassType, Point2D } from "../types";

const DEFAULT_CANVAS_WIDTH = 760;
const teamColors = {
  team_a: "#50d9ff",
  team_b: "#ff5c67",
  unassigned: "#eaaf37",
} as const;

function useCanvasImage(source: string | null) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!source) {
      setImage(null);
      return;
    }
    const nextImage = new window.Image();
    nextImage.onload = () => setImage(nextImage);
    nextImage.src = source;
    return () => {
      nextImage.onload = null;
    };
  }, [source]);
  return image;
}

interface PitchWorkspaceProps {
  imageUrl: string | null;
  imageWidth: number;
  imageHeight: number;
  detections: Detection[];
  stage: number;
  carrierId: string | null;
  candidateCarrierId: string | null;
  calibrationPairs: CalibrationPair[];
  calibrationOutlierIndices?: number[];
  targetPixel: Point2D | null;
  interceptPixel: Point2D | null;
  passType: PassType;
  onDetectionClick: (detection: Detection) => void;
  onCanvasClick: (point: Point2D) => void;
}

export function PitchWorkspace({
  imageUrl,
  imageWidth,
  imageHeight,
  detections,
  stage,
  carrierId,
  candidateCarrierId,
  calibrationPairs,
  calibrationOutlierIndices = [],
  targetPixel,
  interceptPixel,
  passType,
  onDetectionClick,
  onCanvasClick,
}: PitchWorkspaceProps) {
  const shellRef = useRef<HTMLDivElement>(null);
  const image = useCanvasImage(imageUrl);
  const [hoveredDetectionId, setHoveredDetectionId] = useState<string | null>(null);
  const [canvasWidth, setCanvasWidth] = useState(DEFAULT_CANVAS_WIDTH);
  const scale = imageWidth > 0 ? canvasWidth / imageWidth : 1;
  const canvasHeight = Math.max(1, imageHeight * scale);
  const carrier = useMemo(
    () => detections.find((item) => item.id === carrierId),
    [carrierId, detections],
  );

  useEffect(() => {
    const shell = shellRef.current;
    if (!shell) return;
    const updateWidth = (width: number) => setCanvasWidth(Math.max(1, Math.floor(width)));
    updateWidth(shell.clientWidth);
    const observer = new ResizeObserver(([entry]) => updateWidth(entry.contentRect.width));
    observer.observe(shell);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={shellRef}
      className={`canvas-shell ${image ? "has-image" : ""}`}
      role="img"
      aria-label="พื้นที่วิเคราะห์ภาพฟุตบอล"
    >
      {!image ? <div className="canvas-empty">อัปโหลดภาพ หรือคลิก "ลองฉากตัวอย่าง" เพื่อเริ่มต้นวิเคราะห์</div> : null}
      {image ? (
        <Stage
          width={canvasWidth}
          height={canvasHeight}
          onMouseLeave={() => setHoveredDetectionId(null)}
          onClick={(event) => {
            if (event.target !== event.target.getStage()) return;
            const pointer = event.target.getStage()?.getPointerPosition();
            if (pointer) onCanvasClick({ x: pointer.x / scale, y: pointer.y / scale });
          }}
        >
          <Layer>
            <KonvaImage image={image} width={canvasWidth} height={canvasHeight} listening={false} />
            {carrier && targetPixel ? (
              <Arrow
                points={[
                  carrier.foot_pixel.x * scale,
                  carrier.foot_pixel.y * scale,
                  targetPixel.x * scale,
                  targetPixel.y * scale,
                ]}
                stroke={passType === "ground" ? "#10b981" : "#eaaf37"}
                fill={passType === "ground" ? "#10b981" : "#eaaf37"}
                strokeWidth={4}
                pointerLength={12}
                pointerWidth={12}
                dash={passType === "ground" ? [12, 7] : [4, 10]}
              />
            ) : null}
            {targetPixel ? (
              <Circle
                x={targetPixel.x * scale}
                y={targetPixel.y * scale}
                radius={10}
                fill="#10b981"
                stroke="#060d18"
                strokeWidth={3}
              />
            ) : null}
            {interceptPixel ? (
              <Group x={interceptPixel.x * scale} y={interceptPixel.y * scale}>
                <Line points={[-10, -10, 10, 10]} stroke="#eaaf37" strokeWidth={4} />
                <Line points={[-10, 10, 10, -10]} stroke="#eaaf37" strokeWidth={4} />
              </Group>
            ) : null}
            {detections.map((detection) => {
              const selected = detection.id === carrierId || detection.id === candidateCarrierId;
              const hovered = detection.id === hoveredDetectionId;
              const roleName = detection.class_name === "goalkeeper"
                ? "ผู้รักษาประตู"
                : detection.class_name === "referee"
                  ? "ผู้ตัดสิน"
                  : "ผู้เล่น";
              const classSuffix =
                detection.class_name === "goalkeeper" ? " (โกล)" : detection.class_name === "referee" ? " (ผู้ตัดสิน)" : "";
              const label = selected || hovered
                ? `${detection.id.toUpperCase()} · ${roleName}`
                : `${detection.id.toUpperCase()}${classSuffix}`;
              const color =
                detection.class_name === "ball"
                  ? "#ffffff"
                  : teamColors[detection.team_id ?? "unassigned"];
              return (
                <Group
                  key={detection.id}
                  onMouseEnter={() => setHoveredDetectionId(detection.id)}
                  onMouseLeave={() => setHoveredDetectionId(null)}
                  onClick={(event) => {
                    event.cancelBubble = true;
                    onDetectionClick(detection);
                  }}
                >
                  <Rect
                    x={detection.bbox.x * scale}
                    y={detection.bbox.y * scale}
                    width={detection.bbox.width * scale}
                    height={detection.bbox.height * scale}
                    fill="transparent"
                    stroke={selected ? "#eaaf37" : color}
                    strokeWidth={selected || hovered ? 2 : 1.25}
                    hitStrokeWidth={10}
                    cornerRadius={2}
                  />
                  {detection.class_name !== "referee" ? (
                    <Group x={detection.foot_pixel.x * scale} y={detection.foot_pixel.y * scale}>
                      <Circle
                        radius={selected ? 5 : 4}
                        fill={selected ? "#eaaf37" : color}
                        stroke="#060d18"
                        strokeWidth={1}
                        hitStrokeWidth={8}
                      />
                      <Line points={[-7, 0, 7, 0]} stroke={color} strokeWidth={1} listening={false} />
                      <Line points={[0, -7, 0, 7]} stroke={color} strokeWidth={1} listening={false} />
                    </Group>
                  ) : null}
                  <Label x={detection.bbox.x * scale} y={Math.max(0, detection.bbox.y * scale - 18)}>
                    <Tag fill={selected ? "#eaaf37" : color} cornerRadius={2} />
                    <Text
                      text={label}
                      fill="#060d18"
                      fontSize={10}
                      fontStyle="bold"
                      padding={3}
                    />
                  </Label>
                </Group>
              );
            })}
            {stage === 3
              ? calibrationPairs.map((pair, index) => (
                  <Group key={pair.label} x={pair.image.x * scale} y={pair.image.y * scale}>
                    <Circle
                      radius={13}
                      fill={calibrationOutlierIndices.includes(index) ? "#ef4444" : "#eaaf37"}
                      stroke="#060d18"
                      strokeWidth={3}
                    />
                    <Text
                      text={pair.label.split(":")[0] || String(index + 1)}
                      fill="#060d18"
                      fontSize={9}
                      fontStyle="bold"
                      x={-9}
                      y={-5}
                      width={18}
                      align="center"
                    />
                  </Group>
                ))
              : null}
          </Layer>
        </Stage>
      ) : null}
    </div>
  );
}

