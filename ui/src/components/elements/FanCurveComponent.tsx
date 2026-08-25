import { Box, Button, ButtonGroup, Flex, Text, useColorMode } from "@chakra-ui/react";
import { FC, PointerEvent, useState } from "react";
import { useSettingState } from "../../model/hooks";

const POINTS = [40, 50, 60, 70, 80, 90] as const;
const NAMES = ["st40", "st50", "st60", "st70", "st80", "st90"] as const;
const PRESETS = {
  Quiet: [20, 25, 35, 50, 70, 85],
  Balanced: [25, 35, 50, 70, 85, 100],
  Performance: [35, 50, 65, 80, 95, 100],
} as const;

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, Math.round(value)));

type CurveProps = { path: string };

const FanCurveComponent: FC<CurveProps> = ({ path }) => {
  const st40 = useSettingState<number>(`${path}.st40`);
  const st50 = useSettingState<number>(`${path}.st50`);
  const st60 = useSettingState<number>(`${path}.st60`);
  const st70 = useSettingState<number>(`${path}.st70`);
  const st80 = useSettingState<number>(`${path}.st80`);
  const st90 = useSettingState<number>(`${path}.st90`);
  const controls = [st40, st50, st60, st70, st80, st90];
  const values = controls.map(({ state }, index) =>
    clamp(typeof state === "number" ? state : PRESETS.Balanced[index], 0, 100)
  );
  const [dragging, setDragging] = useState<number | null>(null);
  const { colorMode } = useColorMode();
  const foreground = colorMode === "dark" ? "gray.100" : "gray.700";

  const updatePoint = (index: number, value: number) => {
    // Keep the curve monotonic in the UI as well as in the fan daemon.
    const min = index === 0 ? 0 : values[index - 1];
    const max = index === values.length - 1 ? 100 : values[index + 1];
    controls[index].setState(clamp(value, min, max));
  };

  const pointerValue = (
    event: PointerEvent<SVGSVGElement | SVGCircleElement>
  ) => {
    const canvas =
      event.currentTarget instanceof SVGSVGElement
        ? event.currentTarget
        : event.currentTarget.ownerSVGElement;
    if (!canvas) return 0;
    const rect = canvas.getBoundingClientRect();
    return clamp(100 - ((event.clientY - rect.top) / rect.height) * 100, 0, 100);
  };

  const applyPreset = async (preset: readonly number[]) => {
    // Raising points from hot to cool, then lowering cool to hot, keeps every
    // intermediate update valid for the daemon's monotonic-curve check.
    for (let index = values.length - 1; index >= 0; index--) {
      if (preset[index] > values[index]) await controls[index].setState(preset[index]);
    }
    for (let index = 0; index < values.length; index++) {
      if (preset[index] < values[index]) await controls[index].setState(preset[index]);
    }
  };

  const coordinates = values.map(
    (value, index) => `${index * (100 / (values.length - 1))},${100 - value}`
  );

  return (
    <Box borderWidth="1px" borderRadius="md" padding="0.8rem" marginBottom="0.9rem">
      <Flex justify="space-between" align="baseline" marginBottom="0.45rem">
        <Text fontWeight="bold">Fan curve</Text>
        <Text fontSize="sm" color={foreground}>Drag a point to change fan speed</Text>
      </Flex>
      <svg
        viewBox="-5 -5 110 110"
        width="100%"
        role="img"
        aria-label="Fan speed curve from 40 to 90 degrees Celsius"
        onPointerMove={(event) => dragging !== null && updatePoint(dragging, pointerValue(event))}
        onPointerUp={() => setDragging(null)}
        onPointerLeave={() => setDragging(null)}
        style={{ display: "block", touchAction: "none", minHeight: "10rem" }}
      >
        {[0, 25, 50, 75, 100].map((value) => (
          <line key={value} x1="0" x2="100" y1={100 - value} y2={100 - value} stroke="currentColor" opacity="0.18" />
        ))}
        <polyline points={coordinates.join(" ")} fill="none" stroke="var(--chakra-colors-brand-300)" strokeWidth="2.5" />
        {values.map((value, index) => (
          <g key={NAMES[index]}>
            <circle
              cx={index * (100 / (values.length - 1))}
              cy={100 - value}
              r="4.2"
              fill="var(--chakra-colors-brand-300)"
              stroke="currentColor"
              strokeWidth="1.2"
              onPointerDown={(event) => {
                event.preventDefault();
                setDragging(index);
                updatePoint(index, pointerValue(event));
              }}
              style={{ cursor: "ns-resize" }}
            />
            <text x={index * (100 / (values.length - 1))} y="108" textAnchor="middle" fill="currentColor" fontSize="7">{POINTS[index]}°</text>
          </g>
        ))}
      </svg>
      <Text fontSize="sm" color={foreground} marginTop="0.3rem">
        {values.map((value, index) => `${POINTS[index]}°: ${value}%`).join("  ·  ")}
      </Text>
      <ButtonGroup size="sm" marginTop="0.65rem" spacing="2">
        {Object.entries(PRESETS).map(([name, preset]) => (
          <Button key={name} onClick={() => void applyPreset(preset)}>{name}</Button>
        ))}
      </ButtonGroup>
    </Box>
  );
};

export const isFanCurve = (children: Record<string, unknown>) =>
  NAMES.every((name) => Object.prototype.hasOwnProperty.call(children, name));

export default FanCurveComponent;
