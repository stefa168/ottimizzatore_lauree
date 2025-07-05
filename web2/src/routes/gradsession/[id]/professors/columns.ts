import type {ColumnDef} from "@tanstack/table-core";
import type {SessionProfessor} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorBurdenComponent from "./ProfessorBurden.svelte";
import ProfessorRoleSelector from "./ProfessorRoleSelector.svelte";
import type {SessionData} from "../../SessionData.svelte";

export const columns: (sd: SessionData) => ColumnDef<SessionProfessor>[] = (sd: SessionData) => [
  {
    accessorKey: "surname",
    header: "Cognome",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "surname"})
  }, {
    accessorKey: "first_name",
    header: "Nome",
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "name"})
  }, {
    accessorKey: "role",
    header: "Ruolo Universitario",
    cell: ({row}) => renderComponent(ProfessorRoleSelector, {
      value: row.original.role,
      onUpdateValue: (newRole) => {
        let professor = sd.professorsMap.get(row.original.id);
        if (!professor)
          return;

        // todo implement serverside mutation
        professor.role = newRole;
      }
    })
  }, {
    header: "Disponibilità"
  }, {
    header: "Carico",
    cell: ({row}) => renderComponent(ProfessorBurdenComponent, {burden: sd.professorsBurdens.get(row.original.id)})
  }
]