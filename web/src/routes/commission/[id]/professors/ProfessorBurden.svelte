<script lang="ts">
    import type {ProfessorBurden} from "../commission_types";

    interface Props {
        burden: ProfessorBurden;
    }

    let {burden}: Props = $props();
</script>

<strong>
    {#if burden.asSupervisor > 0}
        <div>
            {burden.asSupervisor}
            <abbr title="Come Relatore" class="cursor-help">R</abbr>
        </div>
    {/if}

    {#if burden.asCounterSupervisor > 0}
        <div>
            {burden.asCounterSupervisor}
            <abbr title="Come Contro-Relatore" class="cursor-help">C</abbr>
        </div>
    {/if}

    {#if burden.asSupervisor === 0 && burden.asCounterSupervisor === 0}
        -
    {/if}
</strong>