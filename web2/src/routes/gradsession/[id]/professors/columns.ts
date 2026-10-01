// Libraries
import type {ColumnDef, FilterFn, InitialTableState, SortingFn} from "@tanstack/table-core";
import {renderComponent} from "@/components/ui/data-table";
import {toast} from "svelte-sonner";

// Project types
import type {SessionProfessor, UniversityRole} from "@/types";
import type {SessionData} from "../../SessionData.svelte";

// APIs
import {ProfessorsApi} from "@/api/ProfessorsApi";
import {GradSessionApi} from "@/api/GradSesssionApi";

// Components
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorBurdenComponent from "./ProfessorBurden.svelte";
import ProfessorRoleSelector from "./ProfessorRoleSelector.svelte";
import ProfessorAvailabilitySelector from "./ProfessorAvailabilitySelector.svelte";
import ProfessorNameCell from "./ProfessorNameCell.svelte";
import ProfessorRowActions, {type ProfessorAction} from "./ProfessorRowActions.svelte";
import DataTableColumnFilterButton from "@/components/DataTableColumnFilterButton.svelte";
import {AvailabilityOptions, UniversityRoles} from "@/const";
import {fromRawDates} from "@/api/RawTypes";
import {sortableHeader} from "@/components/table/utils";

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

// Burdens include the students of splits and substitutes, so a split professor still shows their whole load
const compareProfessorBurdens: (sd: SessionData) => SortingFn<SessionProfessor> = (sd) => (rowA, rowB) => {
  const burdenA = sd.subtreeBurden(rowA.original.id)
  const burdenB = sd.subtreeBurden(rowB.original.id)

  return (burdenA.asCounterSupervisor + burdenA.asSupervisor) - (burdenB.asCounterSupervisor + burdenB.asSupervisor);
}

// 1-based position of a split among the splits of the same professor
const partNumber = (sd: SessionData, sp: SessionProfessor) => {
  if (sp.relation !== 'SPLIT' || sp.derived_from_id === null) return undefined;
  const siblings = (sd.childrenOf.get(sp.derived_from_id) ?? [])
    .filter(c => c.relation === 'SPLIT')
    .toSorted((a, b) => a.id - b.id);
  return siblings.findIndex(c => c.id === sp.id) + 1;
}

export const columns: (sd: SessionData, onAction: (action: ProfessorAction, sp: SessionProfessor) => void) => ColumnDef<SessionProfessor>[] = (sd, onAction) => [
  {
    id: "surname",
    accessorFn: (sp: SessionProfessor) => sp.professor.surname,
    enableMultiSort: true,
    header: ({column}) => sortableHeader("Cognome", column),
    cell: ({row}) => renderComponent(ProfessorNameCell, {
      sp: row.original,
      depth: row.depth,
      partNumber: partNumber(sd, row.original),
      children: sd.childrenOf.get(row.original.id),
      canExpand: row.getCanExpand(),
      expanded: row.getIsExpanded(),
      toggle: row.getToggleExpandedHandler(),
    })
  }, {
    id: "first_name",
    accessorFn: (sp: SessionProfessor) => sp.professor.first_name,
    header: ({column}) => sortableHeader("Nome", column),
    // Splits share the professor's name, so their row shows the note instead
    cell: ({row}) => row.original.relation === 'SPLIT'
      ? (row.original.user_note || "")
      : renderComponent(StyledFullName, {fullName: row.original.professor, show: "name"}),
  }, {
    id: "role",
    accessorFn: (sp: SessionProfessor) => sp.professor.role,
    header: ({column}) => renderComponent(DataTableColumnFilterButton<SessionProfessor>, {
      title: "Ruolo Didattico",
      entriesMap: UniversityRoles,
      column,
    }),
    filterFn: arrayIncludesFilter,
    // A split is the same person as its parent row: its role is edited there
    cell: ({row}) => row.original.relation === 'SPLIT' ? "" : renderComponent(ProfessorRoleSelector, {
      value: row.original.professor.role,
      onUpdateValue: async (newRole: UniversityRole) =>
        await ProfessorsApi()
          .updateProfessor({id: row.original.professor.id, role: newRole})
          .then((updatedProf) => {
            // The same professor can appear in several rows (e.g. original and splits)
            sd.sessionProfessors
              .filter(sp => sp.professor.id === updatedProf.id)
              .forEach(sp => sd.updateSessionProfessor({id: sp.id, professor: updatedProf}))
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
    accessorFn: professor => professor.availability,
    filterFn: arrayIncludesFilter,
    cell: ({row}) => renderComponent(ProfessorAvailabilitySelector, {
      value: row.original.availability,
      onUpdateValue: async (newAvailability) =>
        await GradSessionApi()
          .updateSessionProfessor(sd.session.id, row.original.id, newAvailability)
          .then(fromRawDates<SessionProfessor>)
          .then((updatedSP) => {
            sd.updateSessionProfessor(updatedSP)
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
    id: "burden",
    header: ({column}) => sortableHeader("Carico", column),
    accessorFn: professor => sd.subtreeBurden(professor.id),
    sortingFn: compareProfessorBurdens(sd),
    enableMultiSort: true,
    cell: ({row}) => renderComponent(ProfessorBurdenComponent, {burden: sd.subtreeBurden(row.original.id)})
  }, {
    id: "actions",
    header: "",
    enableSorting: false,
    cell: ({row}) => renderComponent(ProfessorRowActions, {
      sp: row.original,
      children: sd.childrenOf.get(row.original.id),
      onAction
    })
  }
]