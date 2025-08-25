<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import {formatTime} from "$lib/utils";
  import {getSessionData, SessionData} from "../../../SessionData.svelte";
  import type {SolutionCommission} from "@/api/OptimizationConfigurationApi";

  interface Props {
    sessionData: SessionData;
    commission: SolutionCommission;
  }

  let {sessionData, commission}: Props = $props();

  const students = $derived(commission.student_ids.map(s => sessionData.studentEntriesMap.get(s)).filter(s => s !== undefined));
  const bachelor = $derived(students.filter(student => student?.degree_level === "bachelors").length);
  const masters = $derived(students.filter(student => student?.degree_level === "masters").length);
  const professors = $derived(commission.professor_ids.map(p => sessionData.sessionProfessorsMap.get(p)).filter(s => s !== undefined));

  const commissionDetails = $derived.by(() => {
    let result = "";
    result += bachelor > 0 ? `${bachelor}T` : '';

    if (masters > 0)
      result += result.length > 0 ? `, ${masters}M` : `${masters}M`;

    return result;
  });

  const commissionDetailsHover = $derived.by(() => {
    let result = '';

    result += bachelor > 0 ? `${bachelor} Studenti Triennali` : '';

    if (masters > 0)
      result += result.length > 0 ? `, ${masters} Studenti Magistrali` : '';

    return result;
  })
</script>

<Card.Root class="w-fit transition-all duration-300 hover:shadow-lg dark:hover:bg-primary-foreground gap-2">
  <Card.Header>
    <Card.Title>Commissione {commission.order_key + 1}</Card.Title>
    <Card.Description>
      <span class="flex flex-col">
        {#if bachelor > 0}
          <span>{bachelor} Candidati Triennali</span>
        {/if}
        {#if masters > 0}
          <span class="text-nowrap">{masters} Candidati Magistrali</span>
        {/if}
        <span>Durata: <strong>{formatTime(commission.duration)}</strong></span>
      </span>
    </Card.Description>
  </Card.Header>
  <Card.Content>
    <ul class="text-left">
      {#each professors as sessionProfessor}
        {@const professor = sessionProfessor.professor}
        <li><span class={[professor.role === 'ordinary' && 'underline']}>
          {professor.surname} {professor.first_name}
        </span></li>
      {/each}
    </ul>
  </Card.Content>
</Card.Root>