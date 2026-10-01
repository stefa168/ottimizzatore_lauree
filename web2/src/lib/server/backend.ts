import {error} from "@sveltejs/kit";
import {env} from "$env/dynamic/private";

/** Base URL of the Litestar API. Only the SvelteKit server talks to it, through remote functions. */
const BACKEND_URL = (env.BACKEND_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

/** Error body sent by the Litestar API. */
interface BackendError {
  detail?: string;
  status_code?: number;
  extra?: Record<string, unknown>;
}

/**
 * Calls the backend and returns the parsed JSON body (or `undefined` for empty responses).
 * Failures are turned into SvelteKit HTTP errors, keeping the backend's `detail` and `extra`.
 */
export async function backendFetch<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, init);
  } catch (e) {
    console.error(`Backend not reachable at ${BACKEND_URL}`, e);
    error(503, {message: "Backend non raggiungibile"});
  }

  const text = await response.text();
  const body: unknown = text ? JSON.parse(text) : undefined;

  if (!response.ok) {
    const err = (body ?? {}) as BackendError;
    error(response.status, {message: err.detail ?? response.statusText, extra: err.extra});
  }

  return body as T;
}

/** Shorthand for requests with a JSON body. */
export const jsonBody = (method: string, data: unknown): RequestInit => ({
  method,
  body: JSON.stringify(data),
  headers: {"Content-Type": "application/json"},
});
