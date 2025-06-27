// todo replace
import type {ApiErrorResponse, GradSession} from "@/types";
import {createMutation, createQuery, type QueryClient} from "@tanstack/svelte-query";
import type {CommissionFormData, UploadErrorDetails} from "@/schema/CommissionFormSchema";

const PUBLIC_BACKEND_URL = "http://127.0.0.1:8000/api/v1";

// import { PUBLIC_BACKEND_URL } from '$env/static/public';

export interface RawGradSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

// transforms.ts
export const transformGradSession = (raw: RawGradSession): GradSession => ({
  ...raw,
  created_at: new Date(raw.created_at),
  updated_at: new Date(raw.updated_at)
});

export const GradSessionKeys = {
  all: ['gs'] as const,
  session: (id: number) => [...GradSessionKeys.all, id] as const,
}

export const GradSessionApi = (customFetch = fetch) => ({
  getAll: async (): Promise<RawGradSession[]> => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions`);
    return (await response.json()) as RawGradSession[]
  },
  getById: async (id: number): Promise<RawGradSession> => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${id}`);
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

    return await response.json() as Promise<RawGradSession>
  }
});

export const GradSessionApiQueries = (queryClient: QueryClient, customFetch = fetch) => ({
  allSessionsQuery: () =>
    createQuery({
      queryKey: GradSessionKeys.all,
      queryFn: GradSessionApi(customFetch).getAll,
      select: data => data.map(transformGradSession)
    }),
  uploadSessionMutation: () =>
    createMutation<GradSession, ApiErrorResponse<UploadErrorDetails>, CommissionFormData>({
      mutationFn: (data: CommissionFormData) => GradSessionApi(customFetch)
        .create(data)
        .then((r) => transformGradSession(r)),
      onSuccess: (raw) => {
        queryClient.invalidateQueries({queryKey: GradSessionKeys.all});
      },

    }),
});