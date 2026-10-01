import type {ApiErrorResponse} from "@/types";

/**
 * Converts an error thrown by a remote function (a SvelteKit `HttpError` whose body carries the backend's message and
 * `extra`) into the `ApiErrorResponse` shape used by the components.
 */
export function toApiError<TExtra = never>(e: unknown): ApiErrorResponse<TExtra> {
  if (e && typeof e === 'object' && 'status' in e && 'body' in e) {
    const {status, body} = e as { status: number, body?: App.Error };
    return {status_code: status, detail: body?.message ?? String(e), extra: body?.extra as TExtra | undefined};
  }
  return {status_code: 500, detail: e instanceof Error ? e.message : String(e)};
}
