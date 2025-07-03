import type {LayoutLoad} from "./$types";
import {GradSessionApi} from "@/api/GradSesssionApi";
import {transformGradSession, transformSessionProfessorList} from "@/api/RawTypes";
import {error} from "@sveltejs/kit";
import type {ApiErrorResponse} from "@/types";
import {computeProfessorsBurdens} from "@/utils";

export const load: LayoutLoad = async ({params, parent, fetch}) => {
  const session_id = Number.parseInt(params.id);
  let api = GradSessionApi(fetch);

  try {
    const [session, student_entries, professors] = await Promise.all([
      api.getById(session_id).then(transformGradSession),
      api.getStudents(session_id),
      api.getProfessors(session_id).then(transformSessionProfessorList)
    ]);

    let professorsMap = new Map(professors.map(p => [p.id, p]));

    return {
      session_id: session_id,
      session,
      student_entries,
      professors,
      professorsMap,
      professorsBurdens: computeProfessorsBurdens(professorsMap, student_entries)
    };
  } catch (err) {
    // Handle the API error appropriately
    const apiError = err as ApiErrorResponse;
    error(apiError.status_code, {message: apiError.detail})
  }
}