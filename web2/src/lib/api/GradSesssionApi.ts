// todo replace
import {
  type ApiErrorResponse,
  type GradSession,
  type ProfessorAvailability,
  type SessionProfessor,
} from "@/types";
import {createMutation, createQuery, type QueryClient} from "@tanstack/svelte-query";
import {
  type CommissionFormData,
  type UploadErrorDetails
} from "@/schema/CommissionFormSchema";
import {PUBLIC_BACKEND_URL} from "@/const";
import {
  type RawGradSession,
  type RawGradSessionEntry,
  type RawSessionProfessor,
  fromRawDates, fromRawList,
} from "@/api/RawTypes";

// import { PUBLIC_BACKEND_URL } from '$env/static/public';

export const GradSessionKeys = {
  all: ['gs'] as const,
  session: (id: number) => [...GradSessionKeys.all, id] as const,
  session_students: (session_id: number) => [...GradSessionKeys.session(session_id), 'students'] as const,
  session_professors: (session_id: number) => [...GradSessionKeys.session(session_id), 'professors'] as const,
}

export const GradSessionApi = (customFetch = fetch) => ({
  getAll: async (): Promise<RawGradSession[]> => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions`);

    if (!response.ok)
      throw await response.json() as ApiErrorResponse;

    return (await response.json()) as RawGradSession[];
  },
  getById: async (id: number): Promise<RawGradSession> => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${id}`);

    if (!response.ok)
      throw await response.json() as ApiErrorResponse;

    return (await response.json()) as RawGradSession;
  },
  create: async (data: CommissionFormData): Promise<RawGradSession> => {
    const formData = new FormData();
    // The not null check should never happen: we have a LOT of checks in place before arriving here, all set up with
    // zod that validates the passed data for us.
    formData.append('file', data.excel!);
    formData.append('title', data.title);

    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw await response.json();
    }

    return await response.json() as RawGradSession;
  },
  delete: async (id: number) => {
    await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${id}`, {
      method: 'DELETE'
    });
    return id;
  },
  getStudents: async (session_id: number) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/students`);
    return (await response.json()) as RawGradSessionEntry[];
  },
  getSessionProfessors: async (session_id: number) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/professors`);
    return (await response.json()) as RawSessionProfessor[];
  },
  updateSessionProfessor: async (session_id: number, session_prof_id: number, availability: ProfessorAvailability) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${session_id}/professors/${session_prof_id}`, {
      method: 'PATCH',
      body: JSON.stringify({availability}),
      headers: {'Content-Type': 'application/json'}
    });
    if (!response.ok)
      throw await response.json();

    return await response.json() as RawSessionProfessor;
  }
});

export const GradSessionApiQueries = (queryClient: QueryClient, customFetch = fetch) => ({
  allSessionsQuery: () =>
    createQuery({
      queryKey: GradSessionKeys.all,
      queryFn: GradSessionApi(customFetch).getAll,
      select: fromRawList<GradSession>
    }),
  sessionStudentsQuery: (session_id: number) =>
    createQuery({
      queryKey: GradSessionKeys.session_students(session_id),
      queryFn: () => GradSessionApi(customFetch).getStudents(session_id),
    }),
  sessionProfessorsQuery: (session_id: number) =>
    createQuery({
      queryKey: GradSessionKeys.session_professors(session_id),
      queryFn: () => GradSessionApi(customFetch).getSessionProfessors(session_id),
      select: fromRawList<SessionProfessor>
    }),
  uploadSessionMutation: () =>
    createMutation<GradSession, ApiErrorResponse<UploadErrorDetails>, CommissionFormData>({
      mutationFn: (data: CommissionFormData) => GradSessionApi(customFetch).create(data).then(fromRawDates<GradSession>),
      onSuccess: (raw) => {
        queryClient.invalidateQueries({queryKey: GradSessionKeys.all});
      },
    }),
  deleteSessionMutation: () =>
    createMutation({
      mutationFn: (id: number) => GradSessionApi(customFetch).delete(id),
      onSuccess: () => {
        queryClient.invalidateQueries({queryKey: GradSessionKeys.all});
      }
    })
});