<script lang="ts">
  /* Shadcn components */
  import {useQueryClient} from "@tanstack/svelte-query";
  import {GradSessionApiQueries} from "@/api/GradSesssionApi";

  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";

  const queryClient = useQueryClient();
  const gsApiQueries = GradSessionApiQueries(queryClient);

  const gsQuery = gsApiQueries.allSessionsQuery();

  let sessions = $derived($gsQuery.isSuccess ? $gsQuery.data : []);
</script>

<div class="border-b-2 mb-6">
  <h2 class="text-3xl mt-4 mb-1"> Sessioni di Laurea attivamente in gestione </h2>
  <p class="mb-2">In questa sezione sono indicate tutte le sessioni di laurea caricate e disponibili per la
    generazione delle commissioni.</p>
</div>

{#if $gsQuery.isPending}
  Caricando le sessioni attive...
{/if}

{#if $gsQuery.isError}
  Errore: {JSON.stringify($gsQuery.error)}
{/if}

{#if $gsQuery.isSuccess}
  <DataTable data={sessions} columns={columns}/>
{/if}