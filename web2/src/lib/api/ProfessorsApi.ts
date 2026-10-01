import type {ApiErrorResponse, PartialExcept, Professor} from "@/types";
import {PUBLIC_BACKEND_URL} from "@/const";
import type {RawProfessor} from "@/api/RawTypes";

export const ProfessorsApi = (customFetch = fetch) => ({
  getAll: async () => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/professors`);

    if (!response.ok)
      throw (await response.json()) as ApiErrorResponse;

    return (await response.json()) as RawProfessor[];
  },
  updateProfessor: async (prof: PartialExcept<Professor, 'id'>) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/professors`, {
      method: 'PATCH',
      body: JSON.stringify(prof),
      headers: {'Content-Type': 'application/json'}
    });

    if (!response.ok)
      throw (await response.json()) as ApiErrorResponse;

    return (await response.json()) as Professor;
  }
})