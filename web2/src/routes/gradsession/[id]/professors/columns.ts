// Libraries
import type {Column, ColumnDef, FilterFn, InitialTableState} from "@tanstack/table-core";
import {renderComponent} from "@/components/ui/data-table";
import {toast} from "svelte-sonner";

// Project types
import type {SessionProfessor, UniversityRole} from "@/types";
import {transformAvailabilityAndDate} from "@/api/RawTypes";
import type {SessionData} from "../../SessionData.svelte";

// APIs
import {ProfessorsApi} from "@/api/ProfessorsApi";
import {GradSessionApi} from "@/api/GradSesssionApi";

// Components
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorBurdenComponent from "./ProfessorBurden.svelte";
import ProfessorRoleSelector from "./ProfessorRoleSelector.svelte";
import ProfessorAvailabilitySelector from "./ProfessorAvailabilitySelector.svelte";
import DataTableColumnButton from "@/components/DataTableColumnButton.svelte";
import DataTableColumnFilterButton from "@/components/DataTableColumnFilterButton.svelte";
import {AvailabilityOptions, UniversityRoles} from "@/const";

function orderableHeader<T>(title: string, column: Column<T>) {
  return renderComponent(DataTableColumnButton, {
    title, column,
    onclick: column.getToggleSortingHandler(),
  });
}

export const initialTableState: () => InitialTableState = () => ({
  sorting: [{
    id: 'surname',
    desc: false
  }]
});

const arrayIncludesFilter: FilterFn<SessionProfessor> = (row, columnId, filterValue: string[]) => {
  if (!filterValue || filterValue.length === 0) {
    return true; // Show all rows if no filter is applied
  }

  const cellValue = row.getValue<string>(columnId);
  return filterValue.includes(cellValue);
};


export const columns: (sd: SessionData) => ColumnDef<SessionProfessor>[] = (sd: SessionData) => [
  {
    accessorKey: "surname",
    header: ({column}) => orderableHeader("Cognome", column),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "surname"})
  }, {
    accessorKey: "first_name",
    header: ({column}) => orderableHeader("Nome", column),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "name"}),
  }, {
    accessorKey: "role",
    header: ({column}) => renderComponent(DataTableColumnFilterButton<SessionProfessor>, {
      title: "Ruolo Didattico",
      entriesMap: UniversityRoles,
      column,
    }),
    filterFn: arrayIncludesFilter,
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
    id: "availability",
    header: ({column}) => renderComponent(DataTableColumnFilterButton<SessionProfessor>, {
      title: "Disponibilità",
      entriesMap: AvailabilityOptions,
      column
    }),
    accessorFn: originalRow => originalRow.availability.when,
    filterFn: arrayIncludesFilter,
    cell: ({row}) => renderComponent(ProfessorAvailabilitySelector, {
      value: row.original.availability.when,
      onUpdateValue: async (newAvailability) =>
        await GradSessionApi()
          .updateProfessorAvailability(sd.session.id, row.original.id, newAvailability)
          .then(transformAvailabilityAndDate)
          .then((updatedAvailability) => {
            let professor = sd.professorsMap.get(row.original.id)!;
            professor.availability = updatedAvailability
            toast.success("Disponibilità del docente per la sessione aggiornata correttamente.")
          })
          .catch(err => {
            console.error(err)
            toast.error("Si è verificato un errore durante l'aggiornamento della disponibilità del docente", {
              duration: Number.POSITIVE_INFINITY,
              description: JSON.stringify(err)
            })
          })
    })
  }, {
    header: "Carico",
    cell: ({row}) => renderComponent(ProfessorBurdenComponent, {burden: sd.professorsBurdens.get(row.original.id)})
  }
]