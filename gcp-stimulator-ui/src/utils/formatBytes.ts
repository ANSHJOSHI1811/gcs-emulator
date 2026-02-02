/**
 * Formats bytes into a human-readable string (KB, MB, GB).
 * @param bytes The number of bytes.
 * @param decimals The number of decimal places to use.
 * @returns A formatted string.
 */
export function formatBytes(bytes: number, decimals = 0): string {
  if (bytes === 0) return '0 MB';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const mb = bytes / (k * k);

  return `${parseFloat(mb.toFixed(dm))} MB`;
}
