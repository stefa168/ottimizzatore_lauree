import type {ColumnDef, FilterFn, InitialTableState} from "@tanstack/table-core";
import {renderComponent} from "@/components/ui/data-table";
import {sortableHeader} from "@/components/table/utils";
import DataTableColumnFilterButton from "@/components/DataTableColumnFilterButton.svelte";
import StyledFullName from "@/components/StyledFullName.svelte";
import ProfessorRoleSelector from "@/components/ProfessorRoleSelector.svelte";
import NumberCellInput from "@/components/NumberCellInput.svelte";
import {UniversityRoles} from "@/const";
import type {ProfessorOverview, UniversityRole} from "@/types";

export const initialTableState: () => InitialTableState = () => ({
  sorting: [{id: 'surname', desc: false}]
});

// Searches both surname and first name
const nameFilter: FilterFn<ProfessorOverview> = (row, _columnId, filterValue: string) => {
  const query = (filterValue ?? "").trim().toLowerCase();
  const {surname, first_name} = row.original;
  return query === "" || `${surname} ${first_name}`.toLowerCase().includes(query)
    || `${first_name} ${surname}`.toLowerCase().includes(query);
};

const arrayIncludesFilter: FilterFn<ProfessorOverview> = (row, columnId, filterValue: string[]) =>
  !filterValue || filterValue.length === 0 || filterValue.includes(row.getValue<string>(columnId));

export interface ProfessorActions {
  updateRole: (professor: ProfessorOverview, role: UniversityRole) => Promise<void>;
  updatePriorCommissions: (professor: ProfessorOverview, count: number) => Promise<void>;
}

export const columns: (actions: ProfessorActions) => ColumnDef<ProfessorOverview>[] = (actions) => [
  {
    id: "surname",
    accessorFn: p => p.surname,
    header: ({column}) => sortableHeader("Cognome", column),
    filterFn: nameFilter,
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "surname"})
  }, {
    id: "first_name",
    accessorFn: p => p.first_name,
    header: ({column}) => sortableHeader("Nome", column),
    cell: ({row}) => renderComponent(StyledFullName, {fullName: row.original, show: "name"})
  }, {
    id: "role",
    accessorFn: p => p.role,
    header: ({column}) => renderComponent(DataTableColumnFilterButton<ProfessorOverview>, {
      title: "Ruolo Didattico",
      entriesMap: UniversityRoles,
      column,
    }),
    filterFn: arrayIncludesFilter,
    cell: ({row}) => renderComponent(ProfessorRoleSelector, {
      value: row.original.role,
      onUpdateValue: (role: UniversityRole) => actions.updateRole(row.original, role)
    })
  }, {
    id: "commissions",
    accessorFn: p => p.commissions,
    header: ({column}) => sortableHeader("Commissioni", column),
    cell: ({row}) => row.original.commissions
  }, {
    id: "prior_commissions",
    accessorFn: p => p.prior_commissions,
    header: ({column}) => sortableHeader("Commissioni precedenti", column),
    cell: ({row}) => renderComponent(NumberCellInput, {
      value: row.original.prior_commissions,
      onSave: (count: number) => actions.updatePriorCommissions(row.original, count),
      label: `Commissioni precedenti di ${row.original.surname} ${row.original.first_name}`,
    })
  }, {
    id: "total",
    accessorFn: p => p.total,
    header: ({column}) => sortableHeader("Totale", column),
    cell: ({row}) => row.original.total
  }, {
    id: "sessions",
    accessorFn: p => p.sessions,
    header: ({column}) => sortableHeader("Sessioni", column),
    cell: ({row}) => row.original.sessions
  }
];
