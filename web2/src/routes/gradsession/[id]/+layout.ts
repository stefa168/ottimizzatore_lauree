import type {LayoutLoad} from "./$types";
import {GradSessionApi} from "@/api/GradSesssionApi";
import {fromRawDates, fromRawList} from "@/api/RawTypes";
import {error} from "@sveltejs/kit";
import type {ApiErrorResponse, GradSession, GradSessionEntry, SessionProfessor} from "@/types";

export const load: LayoutLoad = async ({params, parent, fetch}) => {
  const session_id = Number.parseInt(params.id);
  let api = GradSessionApi(fetch);

  try {
    const [session, student_entries, professors] = await Promise.all([
      api.getById(session_id).then(fromRawDates<GradSession>),
      api.getStudents(session_id).then(fromRawList<GradSessionEntry>),
      api.getSessionProfessors(session_id).then(fromRawList<SessionProfessor>)
    ]);

    return {
      session_id,
      session,
      student_entries,
      professors,
    };
  } catch (err) {
    // Handle the API error appropriately
    const apiError = err as ApiErrorResponse;

    if (apiError.status_code === undefined) {
      throw err;
    }

    error(apiError.status_code, {message: apiError.detail});
  }
}