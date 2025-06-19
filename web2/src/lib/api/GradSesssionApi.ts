// todo replace
import type {GradSession} from "@/types";
import {createQuery, type QueryClient} from "@tanstack/svelte-query";

const PUBLIC_BACKEND_URL = "http://127.0.0.1:8000/api/v1";
// import { PUBLIC_BACKEND_URL } from '$env/static/public';

export const GradSessionKeys = {
    all: ['gs'] as const,
    session: (id: number) => [...GradSessionKeys.all, id] as const,
}

export const GradSessionApi = (customFetch = fetch) => ({
    getAll: async (): Promise<GradSession[]> => {
        const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions`);
        return (await response.json()) as GradSession[]
    },
    getById: async (id: number): Promise<GradSession> => {
        const response = await customFetch(`${PUBLIC_BACKEND_URL}/sessions/${id}`);
        return (await response.json()) as GradSession;
    }
});

export const GradSessionApiQueries = (queryClient: QueryClient, customFetch = fetch) => ({
    allSessionsQuery: () =>
        createQuery({
            queryKey: GradSessionKeys.all,
            queryFn: GradSessionApi(customFetch).getAll,
            select: data => data.map(session => ({
                ...session,
                created_at: new Date(session.created_at),
                updated_at: new Date(session.updated_at)
            }))
        }),
});