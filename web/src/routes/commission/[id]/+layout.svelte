<script lang="ts">
    import {afterUpdate, onDestroy} from "svelte";
    import {page} from '$app/stores';
    import {goto} from "$app/navigation";
    import {selectedProblem} from "$lib/store";
    import {browser} from "$app/environment";

    import type {Commission} from "./commission_types";

    import MdiInformationVariantBoxOutline from '~icons/mdi/information-variant-box-outline'
    import NimbusUniversity from '~icons/nimbus/university'
    import MaterialSymbolsPersonPin from '~icons/material-symbols/person-pin'
    import MageRobotUwuFill from '~icons/mage/robot-uwu-fill'

    export let data: { commission: Commission };
    $: currentSection = $page.url.pathname.split('/').filter(s => s.length > 0)[2] ?? 'info';

    // This is needed because the cycle is a bit complex because of how Svelte's lifecycle works:
    // 1. The page is navigated to
    // 2. The component is created. Before this, the corresponding .ts file is executed, and the selectedProblem is set,
    //    but only if it's not already set.
    // 3. The component is mounted.
    // We need to update the selectedProblem only when the user changes the chosen problem: in that case we will have
    // loaded the new problem and then data will contain it.
    afterUpdate(() => {
        selectedProblem.set(data.commission);
    });

    onDestroy(() => {
        selectedProblem.set(undefined);
    });

    function changeSection(section: Section) {
        console.log('Changing section to', section.name);
        // Fix to prevent the server from trying to call goto, because it can't
        if (browser) {
            const destination = section.path ?? section.name;
            goto(`/commission/${$selectedProblem?.id}/${destination}`);
        }
    }

    // Had to use any for the icon, if a better type is found, please update this!
    type Section = { label: string, name: string, path?: string, icon: any };
    const sections: Section[] = [
        {label: 'Informazioni', name: 'info', path: '', icon: MdiInformationVariantBoxOutline},
        {label: 'Studenti Candidati', name: 'candidates', icon: NimbusUniversity},
        {label: 'Docenti della Sessione', name: 'professors', icon: MaterialSymbolsPersonPin},
        {label: 'Ottimizzazione', name: 'optimization', icon: MageRobotUwuFill},
    ];
</script>

<div class="container mx-auto pb-10">
    <h1 class="text-2xl mb-4 font-medium">{$selectedProblem?.title}</h1>
    <!-- Styles from https://flowbite.com/docs/components/tabs/ -->
    <!-- Tabs Root -->
    <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
        <!-- Tabs List -->
        <ul class="flex flex-wrap -mb-px text-sm font-medium text-center text-gray-500 dark:text-gray-400">
            {#each sections as section}
                <li>
                    <button on:click={() => changeSection(section)}
                            data-active={currentSection === section.name}
                            class="inline-flex items-center justify-center p-4 px-2 border-b-2 border-transparent rounded-t-lg hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300 group data-[active=true]:text-primary data-[active=true]:border-primary transition-all ease-in-out duration-150">
                        <svelte:component this={section.icon} class="w-4 h-4 me-2"/>
                        <span>{section.label}</span>
                    </button>
                </li>
            {/each}
        </ul>
    </div>

    <slot/>
</div>