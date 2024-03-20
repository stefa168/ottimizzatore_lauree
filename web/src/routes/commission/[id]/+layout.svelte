<script lang="ts">
    import * as Tabs from "$lib/components/ui/tabs";
    import type {Commission} from "./commission_types";
    import {page} from '$app/stores';
    import {afterNavigate, goto} from "$app/navigation";
    import {problemsData, selectedProblem, selectProblem} from "$lib/store";

    $: currentSection = $page.url.pathname.split('/').filter(s => s.length > 0)[2]

    afterNavigate((nav) => {
        // If the id changes it means that we are moving to a new commission.
        const differentCommission = nav.from?.params?.id != nav.to?.params?.id;
        if (!differentCommission) return;

        const newProblemId = Number(nav.to?.params?.id);
        const problem = $problemsData.find(p => p.id === newProblemId);

        if (problem === undefined) {
            goto('/');
            selectProblem(null);
        } else {
            selectProblem(problem);
            goto(`/commission/${problem.id}`);
        }
    })

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