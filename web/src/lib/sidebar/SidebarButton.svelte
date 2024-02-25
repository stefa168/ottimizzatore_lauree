<script lang="ts">
    import {type ComponentType, createEventDispatcher} from "svelte";

    // Temporary fix because Svelte doesn't have Typescript support for typing components
    export let Icon: ComponentType;

    const dispatch = createEventDispatcher();

    function handleClick() {
        dispatch('click');
    }
</script>

<a {...$$props}
   href="#"
   on:click={handleClick}
   class="group flex items-center p-2 text-gray-900 rounded-lg dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 group">
    <svelte:component this={Icon}
                      class="flex-shrink-0 w-5 h-5 text-gray-500 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white"/>
    <span class="flex-1 ms-3 group-hover:text-gray-900 dark:group-hover:text-white">
        <slot/>
    </span>
</a>