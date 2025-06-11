<script lang="ts">
    import {page} from '$app/state';
    import MdiRobotDeadOutline from '~icons/mdi/robot-dead-outline'
</script>

<div class="mt-32 flex flex-col items-center justify-center h-full">
    <MdiRobotDeadOutline class="w-16 h-16"/>
    <div class="mt-4 text-center text-lg font-medium text-gray-600 dark:text-gray-400">
        <p>Si è verificato un errore!</p>
        <p class="font-mono">{page?.status}: {page?.error?.message}</p>
    </div>
</div>