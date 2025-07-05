import type {ColumnDef} from "@tanstack/table-core";
import type {SessionProfessor, UniversityRole} from "@/types";
import {renderComponent} from "@/components/ui/data-table";
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorBurdenComponent from "./ProfessorBurden.svelte";
import ProfessorRoleSelector from "./ProfessorRoleSelector.svelte";
import type {SessionData} from "../../SessionData.svelte";
import {ProfessorsApi} from "@/api/ProfessorsApi";
import {toast} from "svelte-sonner";

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
    header: "Ruolo Didattico",
    cell: ({row}) => renderComponent(ProfessorRoleSelector, {
      value: row.original.role,
      onUpdateValue: async (newRole: UniversityRole) =>
        await ProfessorsApi()
          .updateProfessor({id: row.original.id, role: newRole})
          .then((updatedProf) => {
            sd.professorsMap.get(row.original.id)!.role = updatedProf.role;
            toast.success("Ruolo del docente aggiornato correttamente.")
          })
          .catch(err => {
            console.error(err)
            toast.error("Si è verificato un errore durante l'aggiornamento del ruolo del docente", {
              duration: Number.POSITIVE_INFINITY,
              description: JSON.stringify(err)
            })
          })
    })
  }, {
    header: "Disponibilità"
  }, {
    header: "Carico",
    cell: ({row}) => renderComponent(ProfessorBurdenComponent, {burden: sd.professorsBurdens.get(row.original.id)})
  }
]