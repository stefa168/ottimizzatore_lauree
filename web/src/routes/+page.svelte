<script lang="ts">
    import MdiRobotConfusedOutline from '~icons/mdi/robot-confused-outline'


    export let data;

</script>


<!--<h2 class="text-2xl mb-1.5">Carica una nuova lista di candidati</h2>
<form on:submit|preventDefault={handle_new_file_submit}>
    <input type="file" name="file" bind:this={fileInput}><br>
    <input class="shadow-neutral-400 " type="submit" value="Upload">
</form>-->
<!--    {#if current_problem === undefined}
        <div class="mt-32 flex flex-col items-center justify-center h-full">
            <MdiRobotConfusedOutline class="w-16 h-16"/>
            <span class="mt-4 text-lg font-medium text-gray-600 dark:text-gray-400">Seleziona un problema o creane uno nuovo per iniziare</span>
        </div>
    {:else}
        <h2 class="text-2xl mb-1.5">{current_problem.title}</h2>
        <ul>
            {#each current_problem.entries as entry (entry.id)}
                <li>{entry.candidate.name}</li>
            {/each}
        </ul>
    {/if}-->
<div class="mt-32 flex flex-col items-center justify-center h-full">
    <MdiRobotConfusedOutline class="w-16 h-16"/>
    <span class="mt-4 text-lg font-medium text-gray-600 dark:text-gray-400">Seleziona un problema o creane uno nuovo per iniziare</span>
</div>