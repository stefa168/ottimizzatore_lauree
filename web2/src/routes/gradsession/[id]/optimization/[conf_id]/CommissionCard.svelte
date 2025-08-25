<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Card from "$lib/components/ui/card";
  import {formatTime} from "$lib/utils";
  import {SessionData} from "../../../SessionData.svelte";
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