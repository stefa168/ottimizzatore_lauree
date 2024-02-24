<script>
    import MdiBookClock from '~icons/mdi/book-clock'
    import MdiChevronRight from '~icons/mdi/chevron-right'

    export let buttonText = "Dropdown Button";
    export let open = false;
</script>

<button type="button"
        class="flex items-center w-full p-2 text-base text-gray-900 transition duration-75 rounded-lg group hover:bg-gray-100 dark:text-white dark:hover:bg-gray-700"
        aria-controls="dropdown-example" data-collapse-toggle="dropdown-example"
        on:click={() => open = !open}>
    <MdiBookClock
            class="flex-shrink-0 w-5 h-5 text-gray-500 transition duration-75 group-hover:text-gray-900 dark:text-gray-400 dark:group-hover:text-white"
            aria-hidden="true"/>
    <span class="flex-1 ms-3 text-left rtl:text-right whitespace-nowrap">{buttonText}</span>
    <MdiChevronRight class="w-6 h-6 transition-transform duration-200 {open ? 'rotate-90' : ''}" aria-hidden="true"/>
</button>

<ul id="lista-problemi-attivi" class="transition-all duration-300 ease-in-out overflow-hidden {open ? 'max-h-screen' : 'max-h-0'}">
    <slot />
</ul>