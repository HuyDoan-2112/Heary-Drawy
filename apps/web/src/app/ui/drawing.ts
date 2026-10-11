import type { FixtureStroke } from '../fixtures';

export type Point = [number, number];
export interface DrawnStroke extends FixtureStroke {
  points: Point[];
}

/** Drawings use one 760 x 680 space on every device so strokes never stretch. */
export const DRAWING_WIDTH = 760;
export const DRAWING_HEIGHT = 680;

export function toPath(points: Point[]): string {
  const [[x, y], ...rest] = points;
  if (rest.length === 0) return `M${x} ${y} L${x + 0.1} ${y}`;
  return `M${x} ${y}${rest.map(([px, py]) => ` L${px} ${py}`).join('')}`;
}
