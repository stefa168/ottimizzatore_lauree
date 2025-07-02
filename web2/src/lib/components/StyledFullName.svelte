<script lang="ts">
    import {capitalize} from "$lib/utils";
    import type {NameSurname} from "@/types";

    interface Props {
        fullName?: NameSurname;
        applyStyle?: boolean;
    }

    let {fullName = undefined, applyStyle = true}: Props = $props();

</script>
<div>
    {#if !fullName}
        <span class="font-extralight">-</span>
    {:else}
        <span class="{applyStyle ? 'font-bold' : '' }">{capitalize(fullName.surname)}</span>
        <span class="{applyStyle ? 'font-light' : '' }">{capitalize(fullName.first_name)}</span>
    {/if}
</div>