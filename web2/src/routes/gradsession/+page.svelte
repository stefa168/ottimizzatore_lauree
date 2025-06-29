<script lang="ts">
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";
  import type {PageProps} from "./$types";

  let {data}: PageProps = $props();
</script>

<div class="border-b-2 mb-6">
  <h2 class="text-3xl mt-4 mb-1"> Sessioni di Laurea attivamente in gestione </h2>
  <p class="mb-2">In questa sezione sono indicate tutte le sessioni di laurea caricate e disponibili per la
    generazione delle commissioni.</p>
</div>

{#await data.sessions}
  Caricando le sessioni attive...
{:then sessions}
  <DataTable data={sessions} columns={columns}/>
{:catch error}
  Errore: {JSON.stringify(error)}
{/await}