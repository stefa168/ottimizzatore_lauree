<script lang="ts">
  import DataTable from "@/components/data-table.svelte";
  import {Input} from "@/components/ui/input";
  import {Button} from "@/components/ui/button";
  import LucideSearch from '~icons/lucide/search'
  import {columns, initialTableState} from "./columns";
  import {getProfessorsOverview, updateProfessorInfo} from "@/api/professors.remote";
  import type {ProfessorOverview, UniversityRole} from "@/types";
  import {fullName} from "@/utils";
  import {toApiError} from "@/errors";
  import {toast} from "svelte-sonner";

  const professors = $derived(await getProfessorsOverview());

  let t: DataTable<ProfessorOverview, string> | undefined = $state();
  let table = $derived(t?.table);

  // The command sends back the refreshed list, so the row updates by itself
  const update = (professor: ProfessorOverview, data: { role?: UniversityRole, prior_commissions?: number },
                  success: string) =>
    updateProfessorInfo({id: professor.id, ...data})
      .then(() => {
        toast.success(success);
      })
      .catch((e) => {
        toast.error(`Si è verificato un errore durante l'aggiornamento di ${fullName(professor)}`,
          {description: toApiError(e).detail});
        throw e;
      });

  const tableColumns = columns({
    updateRole: (p, role) => update(p, {role}, `Ruolo di ${fullName(p)} aggiornato.`),
    updatePriorCommissions: (p, count) =>
      update(p, {prior_commissions: count}, `Commissioni precedenti di ${fullName(p)}: ${count}.`),
  });
</script>

<div class="border-b-2 mb-6">
  <h2 class="text-3xl mt-4 mb-1">Elenco Docenti</h2>
  <p class="mb-2">
    Per ogni docente è indicato il numero di commissioni a cui ha partecipato. Vengono conteggiate le commissioni della
    soluzione utilizzata per ciascuna sessione archiviata, a cui si sommano le commissioni precedenti all'uso del
    sistema, modificabili direttamente dalla tabella.
  </p>
</div>

<div class="flex pb-4">
  <div class="relative">
    <Input
        placeholder="Cerca un docente..."
        class="h-8 pl-7"
        value={table?.getColumn("surname")?.getFilterValue() ?? ""}
        oninput={(e) => table?.getColumn("surname")?.setFilterValue(e.currentTarget.value)}
    />
    <LucideSearch class="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 select-none opacity-50"/>
  </div>
  <Button class="h-8 ms-2" variant="outline" onclick={() => {table?.resetSorting(); table?.resetColumnFilters();}}>
    Resetta la tabella
  </Button>
</div>

<DataTable
    bind:this={t}
    data={professors}
    columns={tableColumns}
    getRowId={(p) => String(p.id)}
    initialState={initialTableState()}
    singlePlural={{
      singular: () => "È presente un solo docente.",
      plural: (n) => `Sono presenti in totale ${n} docenti.`
    }}
    filteredSinglePlural={{
      singular: (n, total) => `È presente un solo docente (su ${total}) che corrisponde ai criteri di ricerca.`,
      plural: (n, total) => `Sono presenti ${n} docenti (su ${total}) che corrispondono ai criteri di ricerca.`
    }}
/>
