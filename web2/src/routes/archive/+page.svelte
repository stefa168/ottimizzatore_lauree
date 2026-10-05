<script lang="ts">
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "../gradsession/columns";
  import {getSessions} from "@/api/sessions.remote";

  const sessions = $derived((await getSessions()).filter(s => s.archived));
</script>

<div class="border-b-2 mb-6">
  <h2 class="text-3xl mt-4 mb-1">Sessioni di Laurea archiviate</h2>
  <p class="mb-2">Le sessioni archiviate restano consultabili, e possono essere ripristinate tra quelle attive dal menu
    delle azioni.</p>
</div>

<DataTable
    data={sessions}
    {columns}
    singlePlural={{
      singular: () => "È presente una sola sessione archiviata.",
      plural: (n) => `Sono presenti in totale ${n} sessioni archiviate.`
    }}
/>
