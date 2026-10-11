import type { FixtureStroke } from '../../app/fixtures';
import { DRAWING_HEIGHT, DRAWING_WIDTH, toPath, type DrawnStroke } from '../../app/ui/drawing';
import type { Stroke } from '../../generated/contracts';

const MAX_POINTS = 512;
const clamp = (value: number) => Math.min(1, Math.max(0, value));

/** Server strokes use 0-1 coordinates of the shared 760 x 680 drawing space. */
export function toServerStroke(stroke: DrawnStroke): Stroke {
  const step = Math.ceil(stroke.points.length / MAX_POINTS);
  const points = stroke.points.filter((_, index) => index % step === 0);
  return {
    stroke_id: `stroke_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
    color: stroke.color,
    width: 14,
    points: points.map(([x, y]) => ({ x: clamp(x / DRAWING_WIDTH), y: clamp(y / DRAWING_HEIGHT) })),
  };
}

export function toScreenStroke(stroke: Stroke): FixtureStroke {
  const points = stroke.points ?? [];
  return {
    color: stroke.color,
    d: points.length ? toPath(points.map((p) => [p.x * DRAWING_WIDTH, p.y * DRAWING_HEIGHT])) : '',
  };
}
