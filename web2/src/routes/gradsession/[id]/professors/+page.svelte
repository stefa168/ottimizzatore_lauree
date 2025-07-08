<script lang="ts">
  import {columns, initialTableState} from "./columns";
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";
  import {Input} from "@/components/ui/input";
  import type {SessionProfessor} from "@/types";
  import {Button} from "@/components/ui/button";
  import {LucideSearch} from "@lucide/svelte";

  let sessionData = getSessionData();

  let initialState = $state(initialTableState());

  let t: DataTable<SessionProfessor, string> | undefined = $state();
  let table = $derived(t?.table)
</script>

<div class="flex items-center pb-4">
  <div class="relative">
    <Input
        placeholder="Cerca un docente..."
        class="h-8 pl-7"
        value={table?.getColumn("surname")?.getFilterValue() ?? ""}
        onchange={(e) => {
          table?.getColumn("surname")?.setFilterValue(e.currentTarget.value);
        }}
        oninput={(e) => {
          table?.getColumn("surname")?.setFilterValue(e.currentTarget.value);
        }}
    />
    <LucideSearch class="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 select-none opacity-50"/>
  </div>
  <Button
      class="h-8 ms-2"
      variant="outline"
      onclick={() => {table?.resetSorting(); table?.resetColumnFilters();}}>
    Resetta la tabella
  </Button>
</div>

<DataTable
    bind:this={t}
    data={sessionData.professors}
    columns={columns(sessionData)}
    {initialState}
/>