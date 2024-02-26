<script lang="ts">
    import MdiBookClock from '~icons/mdi/book-clock'
    import MdiChevronRight from '~icons/mdi/chevron-right'
    import {Button} from "$lib/components/ui/button";

    export let buttonText = "Dropdown Button";
    export let open = false;
</script>

<Button class="px-3 w-full justify-start"
        variant="ghost"
        on:click={() => open = !open}>
    <MdiBookClock class="me-2 h-4 w-4"/>
    <span>{buttonText}</span>
    <MdiChevronRight
            class="w-6 h-6 ms-2 transition-transform duration-200 {open ? 'rotate-90' : ''}"
            aria-hidden="true"/>
</Button>

<ul id="lista-problemi-attivi" class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {open ? 'max-h-screen' : 'max-h-0'}">
    <slot />
</ul>