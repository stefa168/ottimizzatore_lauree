import {command, query} from "$app/server";
import {z} from "zod";
import {backendFetch, jsonBody} from "$lib/server/backend";
import {
  OptimizationConfigurationRecapSchema,
  OptimizationConfigurationSchema,
  type OptimizationConfiguration
} from "@/schema/optimization";
import {optimizationTaskStatusFactory} from "@/utils";

const id = z.number().int().nonnegative();
const configRef = z.object({sid: id, cid: id});

const POLL_INTERVAL_MS = 2000;

const fetchConfiguration = async (sid: number, cid: number) =>
  OptimizationConfigurationSchema.parse(await backendFetch(`/sessions/${sid}/configuration/${cid}`));

// ── Queries ──────────────────────────────────────────────────────────────────

export const getConfigurations = query(id, async (sid) =>
  z.array(OptimizationConfigurationRecapSchema).parse(await backendFetch(`/sessions/${sid}/configuration`)));

export const getConfiguration = query(configRef, async ({sid, cid}) => fetchConfiguration(sid, cid));

/**
 * Streams the configuration while its optimization runs: the server re-reads it every few seconds and stops once the
 * optimization has ended (successfully or not).
 */
export const watchConfiguration = query.live(configRef, async function* ({sid, cid}) {
  while (true) {
    const configuration = await fetchConfiguration(sid, cid);
    yield configuration;

    const status = optimizationTaskStatusFactory(configuration);
    if (status.ended || status.failed || !status.started) return;

    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }
});

// ── Commands ─────────────────────────────────────────────────────────────────

/** Creates a new configuration, optionally as a copy of an existing one. */
export const newConfiguration = command(z.object({
  sid: id,
  cloneFrom: z.record(z.unknown()).optional(),
}), async ({sid, cloneFrom}) => {
  const created = OptimizationConfigurationSchema.parse(await backendFetch(
    `/sessions/${sid}/configuration/new`,
    cloneFrom ? jsonBody('POST', cloneFrom) : undefined
  ));
  await getConfigurations(sid).refresh();
  return created;
});

export const updateConfiguration = command(z.object({
  sid: id,
  cid: id,
  data: z.record(z.unknown()),
}), async ({sid, cid, data}): Promise<OptimizationConfiguration> => {
  const updated = OptimizationConfigurationSchema.parse(
    await backendFetch(`/sessions/${sid}/configuration/${cid}`, jsonBody('PATCH', data)));
  getConfiguration({sid, cid}).set(updated);
  await getConfigurations(sid).refresh();
  return updated;
});

export const startOptimization = command(configRef, async ({sid, cid}) => {
  await backendFetch(`/sessions/${sid}/configuration/${cid}/solve`);
  await getConfiguration({sid, cid}).refresh();
});
