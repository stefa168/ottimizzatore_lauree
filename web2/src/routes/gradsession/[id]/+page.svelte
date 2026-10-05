<script lang="ts">
  import {goto} from "$app/navigation";

  import IcOutlineChecklist from '~icons/ic/outline-checklist'
  import IcOutlineReportProblem from '~icons/ic/outline-report-problem'
  import IcBaselineInfo from '~icons/ic/baseline-info'
  import IcOutlineKeyboardDoubleArrowRight from '~icons/ic/outline-keyboard-double-arrow-right'
  import {getSessionData} from "../SessionData.svelte";
  import {getConfigurations} from "@/api/optimization.remote";
  import {Button} from "@/components/ui/button";
  import LucideSnowflake from '~icons/lucide/snowflake'
  import LucideDownload from '~icons/lucide/download'
  import {dateFormatter} from "@/utils";

  let sessionData = getSessionData();
  let session_id = $derived(sessionData.session.id);

  let studentEntries = $derived(sessionData.student_entries);
  let bachelorStudents = $derived(studentEntries.filter(e => e.degree_level === 'bachelors'));
  let masterStudents = $derived(studentEntries.filter(e => e.degree_level === 'masters'));

  // Distinct people: a split professor has several Session Professors, and substitutes are people too
  let professors = $derived([...new Map(sessionData.sessionProfessors.map(sp => [sp.professor.id, sp.professor])).values()]);
  let professorsWithoutRole = $derived(professors.filter(p => p.role === 'unspecified'));

  let problemsPresent = $derived(professorsWithoutRole.length > 0)

  // Configurations whose solution was frozen, i.e. judged final
  const finalSolutions = $derived((await getConfigurations(session_id)).filter(c => c.frozen));
</script>

<div>
  <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
    <IcBaselineInfo class="align-baseline"/>
    <span class="ms-2">Riepilogo della sessione</span>
  </h2>
  <ul class="list-disc list-outside ms-4">
    <li>
      Sessione di {studentEntries.length} laureandi, composta da:
      <ul class="ps-4 list-disc list-outside">
        <li hidden={bachelorStudents.length <=0}>
          <p>{bachelorStudents.length} studenti triennali</p>
          <p>Di questi, {bachelorStudents.filter((s) => s.supervisor_assistant_id !== null).length} hanno un
            co-relatore</p>
        </li>
        <li hidden={masterStudents.length <=0}>
          <p>{masterStudents.length} studenti magistrali</p>
          <p>Di questi {masterStudents.filter((s) => s.supervisor_assistant_id !== null).length} hanno un
            co-relatore e {masterStudents.filter((s) => s.counter_supervisor_id !== null).length} hanno un
            controrelatore.</p>
        </li>
      </ul>
    </li>
    <li>Alla sessione parteciperanno {professors.length} docenti.</li>
  </ul>
</div>

<div>
  <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
    <LucideSnowflake/>
    <span class="ms-2">Soluzioni finali</span>
  </h2>
  {#if finalSolutions.length === 0}
    <p>
      Nessuna soluzione è ancora stata congelata. Una soluzione ritenuta completa può essere congelata dalla sua
      configurazione, nella sezione <a href={`/gradsession/${session_id}/optimization`}
                                        class="text-blue-500 hover:underline">Ottimizzazione</a>.
    </p>
  {:else}
    <ul class="divide-y rounded-md border" aria-label="Soluzioni finali">
      {#each finalSolutions as configuration (configuration.id)}
        {@const url = `/gradsession/${session_id}/optimization/${configuration.id}`}
        <li class="flex items-center justify-between gap-4 px-4 py-2">
          <div>
            <a href={url} class="font-medium hover:underline">{configuration.title}</a>
            <p class="text-xs text-muted-foreground">Configurazione creata il {dateFormatter.format(configuration.created_at)}</p>
          </div>
          <Button variant="outline" size="sm" href={`${url}/export`} download data-sveltekit-reload>
            <LucideDownload/> Esporta XLS
          </Button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<div>
  <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
    {#if problemsPresent}
      <IcOutlineReportProblem class="text-destructive"/>
    {:else}
      <IcOutlineChecklist class="text"/>
    {/if}
    <span class="ms-2">Problemi</span>
  </h2>
  {#if problemsPresent}
    <ul class="list-disc list-outside ms-4">
      <li hidden={professorsWithoutRole.length <= 0}>
        {#if professorsWithoutRole.length === 1}
          <span class="text-destructive"> {professorsWithoutRole.length} docente </span> non ha un ruolo
          didattico assegnato.
        {:else}
          <span class="text-destructive"> {professorsWithoutRole.length} docenti </span> non hanno un ruolo
          didattico assegnato.
        {/if}
        <a href={`/gradsession/${session_id}/professors/`}
           class="inline-flex items-center justify-center text-blue-500 hover:underline">
          Vai alla sezione
          <IcOutlineKeyboardDoubleArrowRight/>
        </a>
      </li>
    </ul>
  {:else}
    <p>Non è stato rilevato alcun problema relativo alla sessione di laurea.</p>
  {/if}
</div>
