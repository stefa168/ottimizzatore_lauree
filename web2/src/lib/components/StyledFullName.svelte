<script lang="ts">
    import {capitalize} from "$lib/utils";
    import type {NameSurname} from "@/types";

    interface Props {
        fullName?: NameSurname;
        applyStyle?: boolean;
        show?: 'both' | 'name' | 'surname'
    }

    let {fullName = undefined, applyStyle = true, show = 'both'}: Props = $props();

</script>
<div>
    {#if !fullName}
        <span class="font-extralight">-</span>
    {:else}
        {#if show !== 'name'}
            <span class="{applyStyle ? 'font-bold' : '' }">{capitalize(fullName.surname)}</span>
        {/if}
        {#if show !== 'surname'}
            <span class="{applyStyle ? 'font-light' : '' }">{capitalize(fullName.first_name)}</span>
        {/if}
    {/if}
</div>