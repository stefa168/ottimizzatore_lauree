<script lang="ts">
    import MdiBookClock from '~icons/mdi/book-clock'
    import MdiChevronRight from '~icons/mdi/chevron-right'
    import MdiLoading from "~icons/mdi/loading";
    import {Button} from "$lib/components/ui/button";
    import {Badge} from "$lib/components/ui/badge";

    interface Props {
        buttonText?: string;
        open?: boolean;
        loaded?: boolean;
        childCount?: number;
        children?: import('svelte').Snippet;
    }

    let {
        buttonText = "Dropdown Button",
        open = $bindable(false),
        loaded = true,
        childCount = 0,
        children
    }: Props = $props();

    function click_expand() {
        if (loaded)
            open = !open
    }
</script>

<Button class="px-3 w-full justify-start"
        variant="ghost"
        on:click={click_expand}>
    <MdiBookClock class="me-2 h-4 w-4"/>
    <span>{buttonText}</span>
    {#if loaded}
        <MdiChevronRight
                class="w-6 h-6 ms-2 transition-transform duration-200 {open ? 'rotate-90' : ''}"
                aria-hidden="true"/>
        <Badge class="ms-2" variant="outline">{childCount}</Badge>
    {:else }
        <MdiLoading class="w-6 h-6 ms-4 animate-spin"/>
    {/if}
</Button>

<ul id="lista-problemi-attivi"
    class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {open && loaded ? 'max-h-screen' : 'max-h-0'}">
    {@render children?.()}
</ul>