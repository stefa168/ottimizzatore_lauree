<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Card from "$lib/components/ui/card";
  import {formatTime} from "$lib/utils";
  import {SessionData} from "../../../SessionData.svelte";
  import type {SolutionCommission, SolutionCommissionMember} from "@/schema/optimization";
  import {fullName} from "@/utils";

  interface Props {
    sessionData: SessionData;
    commission: SolutionCommission;
  }

  let {sessionData, commission}: Props = $props();

  const students = $derived(commission.student_ids.map(s => sessionData.studentEntriesMap.get(s)).filter(s => s !== undefined));
  const bachelor = $derived(students.filter(student => student?.degree_level === "bachelors").length);
  const masters = $derived(students.filter(student => student?.degree_level === "masters").length);
  // The members are a snapshot of the solution, so they're shown even if the session professors changed afterwards
  const members = $derived(commission.members.toSorted((a, b) =>
    fullName(a.professor).localeCompare(fullName(b.professor))));

  const note = (m: SolutionCommissionMember) => [
    m.substitute_of && `sostituto di ${fullName(m.substitute_of)}`,
    m.part !== null && `parte ${m.part}`
  ].filter(Boolean).join(", ");
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
      {#each members as member (member.professor.id)}
        {@const professor = member.professor}
        <li>
          <span class={[professor.role === 'ordinary' && 'underline']}>
            {professor.surname} {professor.first_name}
          </span>
          {#if note(member)}
            <span class="text-xs text-muted-foreground">({note(member)})</span>
          {/if}
        </li>
      {/each}
    </ul>
  </Card.Content>
</Card.Root>