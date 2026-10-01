/**
 * The backend sends dates as ISO strings. Remote functions can transport real `Date`s, so the `created_at` and
 * `updated_at` fields are converted on the server, at any depth (e.g. also a session professor's `professor`).
 */
export function withDates<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map(withDates) as T;
  if (value === null || typeof value !== "object") return value as T;

  return Object.fromEntries(Object.entries(value).map(([key, v]) => [
    key,
    (key === "created_at" || key === "updated_at") && typeof v === "string" ? new Date(v) : withDates(v)
  ])) as T;
}
