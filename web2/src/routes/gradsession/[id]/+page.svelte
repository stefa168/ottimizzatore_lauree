<script lang="ts">
  import type {PageProps} from "./$types";
  import {goto} from "$app/navigation";

  import IcOutlineChecklist from '~icons/ic/outline-checklist'
  import IcOutlineReportProblem from '~icons/ic/outline-report-problem'
  import IcBaselineInfo from '~icons/ic/baseline-info'
  import IcOutlineKeyboardDoubleArrowRight from '~icons/ic/outline-keyboard-double-arrow-right'

  let {data}: PageProps = $props();
  let session_id = $derived(data.session_id);

  let studentEntries = $derived(data.student_entries);
  let bachelorStudents = $derived(studentEntries.filter(e => e.degree_level === 'bachelors'));
  let masterStudents = $derived(studentEntries.filter(e => e.degree_level === 'masters'));

  let professors = $derived(data.professors);
  let professorsWithoutRole = $derived(professors.filter(p => p.role === 'unspecified'));

  let problemsPresent = $derived(professorsWithoutRole.length > 0)
</script>

<div>
  <h2 class="text-2xl border-b-2 mt-6 mb-4 flex items-center">
    <IcBaselineInfo class="align-baseline"/>
    <span class="ms-2">Informazioni sulla sessione</span>
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
        <li>
          <p>{masterStudents.length} studenti magistrali</p>
          <p>Di questi {masterStudents.filter((s) => s.supervisor_assistant_id !== null).length} hanno un
            co-relatore e {masterStudents.filter((s) => s.counter_supervisor_id !== null).length} hanno un
            controrelatore.</p>
        </li>
      </ul>
    </li>
    <li>Alla commissione parteciperanno {professors.length} docenti.</li>
  </ul>
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
        <button class="inline-flex items-center justify-center text-blue-500 hover:underline"
                onclick={() => goto(`/gradsession/${session_id}/professors/`)}>
          Vai alla sezione
          <IcOutlineKeyboardDoubleArrowRight/>
        </button>
      </li>
    </ul>
  {:else}
    <p>Non è stato rilevato alcun problema relativo alla sessione di laurea.</p>
  {/if}
</div>
