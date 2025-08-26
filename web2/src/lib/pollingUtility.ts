// pollUntilFn.ts
export type RequestFn<T> = (signal: AbortSignal) => Promise<T>;

/**
 * Options for configuring a cancelable polling function.
 *
 * @template T The type of the result that the polling function resolves with.
 * @property {number} [initialDelay] The initial delay in milliseconds before the first poll.
 * @property {number} [maxDelay] The maximum delay in milliseconds between successive polls.
 * @property {number} [timeout] The maximum time in milliseconds to keep polling before timing out.
 * @property {boolean} [jitter] If true, applies jitter to delay intervals to avoid synchronized polling.
 * @property {(result: T) => boolean} isDone A function that determines when the polling should stop based on the result.
 * @property {boolean} [continueOnError] If true, continues polling even after encountering an error.
 * @property {number} [maxRetries] The maximum number of retry attempts after encountering errors before stopping the poll.
 * @property {(err: unknown, attempt: number) => void} [onError] An optional callback function invoked on an error, providing the error and the current retry attempt.
 * @property {AbortController} [externalController] An optional AbortController instance for external cancellation control.
 */
export interface PollFnCancelableOptions
<T> {
  initialDelay?: number;
  maxDelay?: number;
  timeout?: number | null;
  jitter?: boolean;
  isDone: (result: T) => boolean;
  continueOnError?: boolean;
  maxRetries?: number;
  onError?: (err: unknown, attempt: number) => void; // optional hook
  externalController?: AbortController;
}

/**
 * Polls a given asynchronous function until a condition is met or a timeout/retry limit occurs.
 *
 * @param {RequestFn<T>} request - A function that executes the request and returns a promise resolving with a result of type T.
 * @param {PollFnCancelableOptions<T>} options - Configuration options for polling, including initial delay, max delay, timeout, jitter, and condition check.
 * @return {Promise<T>} A promise that resolves with the first result of type T that satisfies the isDone condition, or rejects if the polling fails or times out.
 */
export async function pollUntilFn<T>(
  request: RequestFn<T>,
  options: PollFnCancelableOptions<T>
): Promise<T | undefined> {
  const {
    initialDelay = 500,
    maxDelay = 5000,
    timeout = 60000,
    jitter = true,
    isDone,
    continueOnError = true,
    maxRetries,
    onError,
    externalController,
  } = options;

  const start = Date.now();
  let delay = initialDelay;
  let attempts = 0;

  const internalController = externalController ? undefined : new AbortController();
  const signal = externalController?.signal ?? internalController!.signal;

  try {
    while (!signal.aborted) {
      // Global guards
      if (maxRetries !== undefined && attempts >= maxRetries) {
        throw new Error('Max retries exceeded');
      }
      if (timeout && timeout > 0 && Date.now() - start > timeout) {
        throw new Error('Polling timed out');
      }

      try {
        const result = await request(signal);
        if (isDone(result)) {
          return result;
        }
      } catch (err) {
        if (isAbortError(err)) throw err;
        onError?.(err, attempts);
        if (!continueOnError) throw err;
      }

      attempts += 1;

      // Sleep with jitter
      const jitterValue = jitter ? Math.random() * 0.5 * delay : 0;
      await sleep(delay + jitterValue, signal);

      // Exponential backoff
      delay = Math.min(delay * 2, maxDelay);
    }
  } finally {
    if (internalController) internalController.abort();
    console.debug("Stopped polling", signal)
  }
  return undefined
}

/**
 * Determines if the provided error is an AbortError.
 *
 * @param {unknown} err - The error object to be checked.
 * @return {boolean} Returns `true` if the error is an AbortError; otherwise, `false`.
 */
function isAbortError(err: unknown): boolean {
  return err instanceof Error && (err.name === 'AbortError' || (err as any)?.code === 'ABORT_ERR');
}

/**
 * Pauses the execution for a given amount of time or until the provided abort signal is triggered.
 *
 * @param {number} ms - The duration in milliseconds for which to pause the execution.
 * @param {AbortSignal} [signal] - An optional AbortSignal to abort the sleep operation before the timeout completes.
 * @return {Promise<void>} A promise that resolves after the specified duration unless aborted by the signal.
 */
function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (ms <= 0) return Promise.resolve();
  return new Promise<void>((resolve, reject) => {
    const done = () => {
      cleanup();
      resolve();
    };
    const onAbort = () => {
      cleanup();
      reject(new DOMException('Aborted', 'AbortError'));
    };
    const cleanup = () => {
      clearTimeout(t);
      signal?.removeEventListener('abort', onAbort);
    };
    const t = setTimeout(done, ms);
    if (signal) {
      if (signal.aborted) onAbort();
      else signal.addEventListener('abort', onAbort);
    }
  });
}
