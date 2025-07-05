import type {ApiErrorResponse, PartialExcept, Professor} from "@/types";
import {PUBLIC_BACKEND_URL} from "@/const";

export const ProfessorsApi = (customFetch = fetch) => ({
  updateProfessor: async (prof: PartialExcept<Professor, 'id'>) => {
    const response = await customFetch(`${PUBLIC_BACKEND_URL}/professors`, {
      method: 'PATCH',
      body: JSON.stringify(prof),
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if(!response.ok)
      throw (await response.json()) as ApiErrorResponse;

    return (await response.json()) as Professor;
  }
})