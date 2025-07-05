import type {LayoutLoad} from "./$types";
import {GradSessionApi} from "@/api/GradSesssionApi";
import {transformGradSession, transformSessionProfessorList} from "@/api/RawTypes";
import {error} from "@sveltejs/kit";
import type {ApiErrorResponse} from "@/types";

export const load: LayoutLoad = async ({params, parent, fetch}) => {
  const session_id = Number.parseInt(params.id);
  let api = GradSessionApi(fetch);

  try {
    const [session, student_entries, professors] = await Promise.all([
      api.getById(session_id).then(transformGradSession),
      api.getStudents(session_id),
      api.getProfessors(session_id).then(transformSessionProfessorList)
    ]);

    return {
      session_id: session_id,
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