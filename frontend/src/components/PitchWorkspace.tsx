import { useEffect, useMemo, useState } from "react";
import { Arrow, Circle, Group, Image as KonvaImage, Label, Layer, Line, Rect, Stage, Tag, Text } from "react-konva";
import type { CalibrationPair, Detection, PassType, Point2D } from "../types";

const CANVAS_WIDTH = 760;
const teamColors = {
  team_a: "#50d9ff",
  team_b: "#ff7d87",
  unassigned: "#f8d66d",
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
  targetPixel,
  interceptPixel,
  passType,
  onDetectionClick,
  onCanvasClick,
}: PitchWorkspaceProps) {
  const image = useCanvasImage(imageUrl);
  const [hoveredDetectionId, setHoveredDetectionId] = useState<string | null>(null);
  const scale = imageWidth > 0 ? CANVAS_WIDTH / imageWidth : 1;
  const canvasHeight = Math.max(420, imageHeight * scale);
  const carrier = useMemo(
    () => detections.find((item) => item.id === carrierId),
    [carrierId, detections],
  );

  return (
    <div className="canvas-shell" role="img" aria-label="พื้นที่วิเคราะห์ภาพฟุตบอล">
      {!image ? <div className="canvas-empty">เลือกภาพเพื่อเริ่มวิเคราะห์</div> : null}
      {image ? (
        <Stage
          width={CANVAS_WIDTH}
          height={canvasHeight}
          onMouseLeave={() => setHoveredDetectionId(null)}
          onClick={(event) => {
            if (event.target !== event.target.getStage()) return;
            const pointer = event.target.getStage()?.getPointerPosition();
            if (pointer) onCanvasClick({ x: pointer.x / scale, y: pointer.y / scale });
          }}
        >
          <Layer>
            <KonvaImage image={image} width={CANVAS_WIDTH} height={imageHeight * scale} listening={false} />
            {carrier && targetPixel ? (
              <Arrow
                points={[
                  carrier.foot_pixel.x * scale,
                  carrier.foot_pixel.y * scale,
                  targetPixel.x * scale,
                  targetPixel.y * scale,
                ]}
                stroke={passType === "ground" ? "#62f5b3" : "#f8d66d"}
                fill={passType === "ground" ? "#62f5b3" : "#f8d66d"}
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
                fill="#62f5b3"
                stroke="#071512"
                strokeWidth={3}
              />
            ) : null}
            {interceptPixel ? (
              <Group x={interceptPixel.x * scale} y={interceptPixel.y * scale}>
                <Line points={[-10, -10, 10, 10]} stroke="#ffb45c" strokeWidth={4} />
                <Line points={[-10, 10, 10, -10]} stroke="#ffb45c" strokeWidth={4} />
              </Group>
            ) : null}
            {detections.map((detection) => {
              const selected = detection.id === carrierId || detection.id === candidateCarrierId;
              const hovered = detection.id === hoveredDetectionId;
              const classSuffix =
                detection.class_name === "goalkeeper" ? " GK" : detection.class_name === "referee" ? " REF" : "";
              const label = selected || hovered
                ? `${detection.id} · ${detection.class_name}`
                : `${detection.id}${classSuffix}`;
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
                    stroke={selected ? "#62f5b3" : color}
                    strokeWidth={selected || hovered ? 2 : 1.25}
                    hitStrokeWidth={10}
                    cornerRadius={2}
                  />
                  {detection.class_name !== "referee" ? (
                    <Group x={detection.foot_pixel.x * scale} y={detection.foot_pixel.y * scale}>
                      <Circle
                        radius={selected ? 5 : 4}
                        fill={selected ? "#62f5b3" : color}
                        stroke="#071512"
                        strokeWidth={1}
                        hitStrokeWidth={8}
                      />
                      <Line points={[-7, 0, 7, 0]} stroke={color} strokeWidth={1} listening={false} />
                      <Line points={[0, -7, 0, 7]} stroke={color} strokeWidth={1} listening={false} />
                    </Group>
                  ) : null}
                  <Label x={detection.bbox.x * scale} y={Math.max(0, detection.bbox.y * scale - 18)}>
                    <Tag fill={selected ? "#62f5b3" : color} cornerRadius={2} />
                    <Text
                      text={label}
                      fill="#071512"
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
                    <Circle radius={13} fill="#f8d66d" stroke="#071512" strokeWidth={3} />
                    <Text
                      text={pair.label.split(":")[0] || String(index + 1)}
                      fill="#071512"
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

