<script lang="ts">
    import {capitalize} from "$lib/utils";

    export let name: string | null = null;
    export let surname: string | null = null;
    export let applyStyle: boolean = true;

</script>
<div>
    {#if name === null && surname === null}
        <span class="font-extralight">-</span>
    {:else}
        {#if surname !== null}
            <span class="{applyStyle ? 'font-bold' : '' }">{capitalize(surname)}</span>
        {/if}
        {#if name !== null}
            <span class="{applyStyle ? 'font-light' : '' }">{capitalize(name)}</span>
        {/if}
    {/if}
</div>