import type {ColumnDef} from "@tanstack/table-core";
import type {ProfessorBurden, SessionProfessor} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorBurdenComponent from "./ProfessorBurden.svelte";

export const columns: (burdens: Map<number, ProfessorBurden>) => ColumnDef<SessionProfessor>[] = (burdens) => [
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
    header: "Ruolo Universitario"
  }, {
    header: "Disponibilità"
  }, {
    header: "Carico",
    cell: ({row}) => renderComponent(ProfessorBurdenComponent, {burden: burdens.get(row.original.id)})
  }
]