/**
 * Figures and marks, formatted in one place.
 *
 * Everything here is locale-free and UTC on purpose: a date rendered by the
 * server and again by the browser has to come out identical, or React reports a
 * hydration mismatch.
 */

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function formatDate(value: string): string {
  const date = new Date(value);
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

export function formatTime(value: string): string {
  const date = new Date(value);
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

/**
 * The accession mark an item carries: its place on the sheet, zero-padded so
 * the rail reads as a column of figures.
 */
export function accessionMark(position: number): string {
  return `№ ${String(position).padStart(3, "0")}`;
}

export function dimensions(width: number, height: number): string {
  return `${width} × ${height}`;
}

/**
 * How long a step took, in the shortest honest unit.
 *
 * `—` until both ends exist: a step that is still running has no duration yet,
 * and inventing one from the current clock would make the server's render and
 * the browser's disagree.
 */
export function elapsed(start: string | null, end: string | null): string {
  if (!start || !end) {
    return "—";
  }

  const seconds = Math.max(
    0,
    Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000),
  );

  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m ${String(seconds % 60).padStart(2, "0")}s`;
  }

  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, "0")}m`;
}
