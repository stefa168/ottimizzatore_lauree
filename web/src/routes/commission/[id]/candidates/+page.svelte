<script lang="ts">
    import StudentsTable from '../commission-students-table.svelte';
    import {selectedProblem} from "$lib/store";
</script>

{#if $selectedProblem !== undefined}
    <StudentsTable commission={$selectedProblem}/>
{/if}