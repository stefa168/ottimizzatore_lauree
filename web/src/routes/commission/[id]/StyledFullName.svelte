<script lang="ts">
    import {capitalize} from "$lib/utils";

    interface Props {
        name?: string | null;
        surname?: string | null;
        applyStyle?: boolean;
    }

    let {name = null, surname = null, applyStyle = true}: Props = $props();

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