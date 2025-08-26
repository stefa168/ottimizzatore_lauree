// pollUntilFn.ts
import pRetry, {AbortError, type RetryContext} from "p-retry";

/**
 * Represents the configuration options for a polling mechanism.
 *
 * @template T - The type of the result being polled.
 *
 * @property {function(r: T): boolean} isDone - A predicate function that determines
 * whether the polling should stop based on the result.
 *
 * @property {number} [retries] - An optional number indicating the maximum number
 * of retries before giving up.
 *
 * @property {number} [minTimeout] - An optional number representing the minimum
 * timeout interval in milliseconds between attempts.
 *
 * @property {number} [maxTimeout] - An optional number representing the maximum
 * timeout interval in milliseconds.
 *
 * @property {boolean} [randomize] - An optional flag that indicates whether to add
 * jitter (randomized variance) to the timeout intervals.
 *
 * @property {AbortSignal} [signal] - An optional AbortSignal instance that can be
 * used to cancel the polling process.
 *
 * @property {function(e: RetryContext): void} [onFailedAttempt] - An optional callback function
 * to handle errors during polling. It receives a RetryContext parameter that provides
 * details about the error and retrying state.
 */
export interface PollOptions<T> {
  isDone: (r: T) => boolean;
  retries?: number;
  minTimeout?: number;
  maxTimeout?: number;
  randomize?: boolean; // jitter
  signal?: AbortSignal;
  onFailedAttempt?: (e: RetryContext) => Promise<void>;
}

/**
 * Polls a given asynchronous function until a specified condition is met or the maximum number of retries is reached.
 *
 * @param {function(AbortSignal): Promise<T>} fn The async function to be polled. It takes an `AbortSignal` as an argument
 * and returns a Promise that resolves to the expected value.
 * @param {Object} options Configuration options for the polling process.
 * @param {function(T): boolean} options.isDone A function that determines whether the polling process should stop. It takes
 * the resolved value of `fn` and returns a boolean.
 * @param {number} [options.retries=10] The maximum number of attempts to poll the function. Defaults to 10.
 * @param {number} [options.minTimeout=500] The minimum delay, in milliseconds, between polling attempts. Defaults to 500 ms.
 * @param {number} [options.maxTimeout=5000] The maximum delay, in milliseconds, between polling attempts. Defaults to 5000 ms.
 * @param {boolean} [options.randomize=true] Whether to introduce random variance in the delay time between retries. Defaults to true.
 * @param {AbortSignal} [options.signal] An optional `AbortSignal` to cancel the polling process. Throws an `AbortError` if aborted.
 * @param {function(Error): void} [options.onError] An optional error handler, called for each failed attempt.
 * @return {Promise<T | undefined>} A promise that resolves to the result of the successfully polled function if the condition is met
 * or `undefined` if the polling process is aborted or the maximum number of retries is reached.
 */
export async function pollUntil<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  options: PollOptions<T>
): Promise<T | undefined> {
  const {
    isDone,
    retries = 10,
    minTimeout = 500,
    maxTimeout = 5000,
    randomize = true,
    signal,
    onFailedAttempt,
  } = options;

  return pRetry(async () => {
    if (signal?.aborted)
      throw new AbortError('Aborted');

    const result = await fn(signal!);

    if (isDone(result))
      return result;

    throw new Error('Not done yet');
  }, {
    retries,
    minTimeout,
    maxTimeout,
    factor: 2,
    randomize,
    signal,
    onFailedAttempt
  });
}
