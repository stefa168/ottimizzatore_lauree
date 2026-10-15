<script lang="ts">
  import {getConfigurations} from "@/api/optimization.remote";

  let {sessionId, configurationId}: { sessionId: number, configurationId: number } = $props();

  const configuration = $derived((await getConfigurations(sessionId)).find(c => c.id === configurationId));
</script>

{#if configuration}
  La soluzione utilizzata è quella della configurazione
  <a href={`/gradsession/${sessionId}/optimization/${configuration.id}`} class="text-blue-500 hover:underline">{configuration.title}</a>:
  le sue commissioni sono conteggiate nell'<a href="/professors" class="text-blue-500 hover:underline">Elenco Docenti</a>.
{/if}
