import {command, query} from "$app/server";
import {z} from "zod";
import {backendFetch, jsonBody} from "$lib/server/backend";
import {withDates} from "$lib/server/dates";
import {getSessionProfessors, getSessionStudents} from "./sessions.remote";
import type {Professor, SessionProfessor} from "@/types";

const id = z.number().int().nonnegative();
const availability = z.enum(['always', 'morning', 'afternoon']);

/** After a change, the professors (and, if students moved, the students) of the session are sent back with the response. */
async function refreshSession(sid: number, studentsMoved = false) {
  await Promise.all([
    getSessionProfessors(sid).refresh(),
    ...(studentsMoved ? [getSessionStudents(sid).refresh()] : [])
  ]);
}

/** All known professors, e.g. to choose a substitute. */
export const getProfessors = query(async () =>
  withDates<Professor[]>(await backendFetch("/professors")));

/** Updates a professor (e.g. the role); `sid` is the session whose professors are refreshed. */
export const updateProfessor = command(z.object({
  sid: id,
  professor: z.object({id, role: z.enum(['ordinary', 'associate', 'researcher', 'unspecified'])}),
}), async ({sid, professor}) => {
  const updated = withDates<Professor>(await backendFetch("/professors", jsonBody('PATCH', professor)));
  await refreshSession(sid);
  return updated;
});

export const updateSessionProfessor = command(z.object({
  sid: id,
  spId: id,
  availability,
}), async ({sid, spId, availability}) => {
  const updated = withDates<SessionProfessor>(
    await backendFetch(`/sessions/${sid}/professors/${spId}`, jsonBody('PATCH', {availability})));
  await refreshSession(sid);
  return updated;
});

/**
 * Replaces the splits of an ORIGINAL Session Professor. An empty list of parts removes the split.
 * If the professor has substitutes, the request fails with a 409 (`extra.had_substitutes`) unless
 * `ignoreSubstitutes` is set, in which case they are removed.
 */
export const splitSessionProfessor = command(z.object({
  sid: id,
  spId: id,
  parts: z.array(z.object({when: availability, note: z.string().nullable(), students: z.array(id)})),
  ignoreSubstitutes: z.boolean().default(false),
}), async ({sid, spId, parts, ignoreSubstitutes}) => {
  await backendFetch(`/sessions/${sid}/professors/${spId}/split?ignore_substitutes=${ignoreSubstitutes}`,
    jsonBody('PATCH', parts));
  await refreshSession(sid, true);
});

/**
 * Assigns the students of a Session Professor to another professor. Called on a SUBSTITUTE, it changes the
 * substituting professor instead.
 */
export const substituteSessionProfessor = command(z.object({
  sid: id,
  spId: id,
  professorId: id,
  availability,
  note: z.string(),
}), async ({sid, spId, professorId, availability, note}) => {
  await backendFetch(`/sessions/${sid}/professors/${spId}/substitute/${professorId}`,
    jsonBody('PATCH', {availability, note}));
  await refreshSession(sid, true);
});

export const removeSubstitute = command(z.object({sid: id, spId: id}), async ({sid, spId}) => {
  await backendFetch(`/sessions/${sid}/professors/${spId}/substitute`, {method: 'DELETE'});
  await refreshSession(sid, true);
});
