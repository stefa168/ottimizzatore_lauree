import {command, query} from "$app/server";
import {z} from "zod";
import {backendFetch} from "$lib/server/backend";
import {withDates} from "$lib/server/dates";
import type {GradSession, GradSessionEntry, SessionProfessor} from "@/types";

const id = z.number().int().nonnegative();

// ── Queries ──────────────────────────────────────────────────────────────────

export const getSessions = query(async () =>
  withDates<GradSession[]>(await backendFetch("/sessions")));

export const getSession = query(id, async (sid) =>
  withDates<GradSession>(await backendFetch(`/sessions/${sid}`)));

export const getSessionStudents = query(id, async (sid) =>
  withDates<GradSessionEntry[]>(await backendFetch(`/sessions/${sid}/students`)));

export const getSessionProfessors = query(id, async (sid) =>
  withDates<SessionProfessor[]>(await backendFetch(`/sessions/${sid}/professors`)));

/** Columns the uploaded Excel file must contain. */
export const getExpectedColumns = query(async () =>
  new Set(await backendFetch<string[]>("/sessions/upload/expected")));

// ── Commands ─────────────────────────────────────────────────────────────────

export const uploadSession = command(z.object({
  title: z.string(),
  only: z.enum(['bachelors', 'masters', 'both']).optional(),
  excel: z.instanceof(File),
}), async ({title, only, excel}) => {
  const formData = new FormData();
  formData.append('file', excel);
  formData.append('title', title);
  if (only && only !== 'both')
    formData.append('only', only);

  const session = withDates<GradSession>(await backendFetch("/sessions/upload", {method: 'POST', body: formData}));
  await getSessions().refresh();
  return session;
});

export const renameSession = command(z.object({sid: id, title: z.string()}), async ({sid, title}) => {
  const session = withDates<GradSession>(await backendFetch(`/sessions/${sid}`, {
    method: 'PATCH',
    body: JSON.stringify(title)
  }));
  getSession(sid).set(session);
  await getSessions().refresh();
  return session;
});

export const deleteSession = command(id, async (sid) => {
  await backendFetch(`/sessions/${sid}`, {method: 'DELETE'});
  await getSessions().refresh();
});
