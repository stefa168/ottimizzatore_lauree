<script lang="ts">
    import * as Tabs from "$lib/components/ui/tabs";
    import type {Commission} from "./commission_types";
    import {page} from '$app/stores';
    import {afterNavigate, goto} from "$app/navigation";
    import {selectedProblem} from "$lib/store";
    import {afterUpdate, onDestroy, onMount} from "svelte";

    export let data: { commission: Commission };
    $: currentSection = $page.url.pathname.split('/').filter(s => s.length > 0)[2];

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

    function changeSection(section: string | undefined) {
        if (section === undefined || section === 'info') {
            goto(`/commission/${$selectedProblem?.id}`);
        } else {
            goto(`/commission/${$selectedProblem?.id}/${section}`);
        }
    }
</script>

<div class="container mx-auto pb-10">
    <h1 class="text-2xl mb-4">{$selectedProblem?.title}</h1>

    <Tabs.Root value={currentSection} onValueChange={changeSection} class="mb-2">
        <div id="toolbar" class="w-full">
            <Tabs.List class="content-center">
                <Tabs.Trigger value="info">Informazioni</Tabs.Trigger>
                <Tabs.Trigger value="candidates">Studenti Candidati</Tabs.Trigger>
                <Tabs.Trigger value="professors">Docenti della Commissione</Tabs.Trigger>
                <Tabs.Trigger value="optimization">Ottimizzazione</Tabs.Trigger>
            </Tabs.List>
        </div>
    </Tabs.Root>

    <slot/>
</div>