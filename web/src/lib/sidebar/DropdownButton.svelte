<script lang="ts">
    import MdiBookClock from '~icons/mdi/book-clock'
    import MdiChevronRight from '~icons/mdi/chevron-right'
    import {Button} from "$lib/components/ui/button";
    import MdiLoading from "~icons/mdi/loading";

    export let buttonText = "Dropdown Button";
    export let open = false;
    export let loaded = true;

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
    {:else }
        <MdiLoading class="w-6 h-6 ms-4 animate-spin"/>
    {/if}
</Button>

<ul id="lista-problemi-attivi"
    class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {open && loaded ? 'max-h-screen' : 'max-h-0'}">
    <slot/>
</ul>