<script lang="ts">
  import type {ProfessorBurden} from "@/types";

  interface Props {
    burden?: ProfessorBurden;
  }

  let {burden}: Props = $props();
</script>

<div class="font-bold ms-6">
  {#if !burden || burden.asSupervisor === 0 && burden.asCounterSupervisor === 0}
    -
  {:else}
    {#if burden.asSupervisor > 0}
      {burden.asSupervisor}
      <abbr title="Come Relatore" class="cursor-help">R</abbr>
    {/if}

    {#if burden.asSupervisor > 0 && burden.asCounterSupervisor > 0}
      -
    {/if}

    {#if burden.asCounterSupervisor > 0}
      {burden.asCounterSupervisor}
      <abbr title="Come Contro-Relatore" class="cursor-help">C</abbr>
    {/if}
  {/if}
</div>