<script lang="ts">
    import * as Tabs from "$lib/components/ui/tabs";
    import type {Commission} from "./commission_types";
    import { page } from '$app/stores';
    import ProfessorsTable from "./commission-professors-table.svelte";
    import StudentsTable from "./commission-students-table.svelte";
    import {goto} from "$app/navigation";

    export let data: { commissionId: string, commissionData: Commission };

    $: commission = data.commissionData
    $: currentSection =  $page.url.pathname.split('/').filter(s => s.length > 0)[2]

    function changeSection(section: string | undefined) {
        goto(`/commission/${commission.id}/${section ? section : ''}`);
    }
</script>

<div class="container mx-auto pb-10">
    <h1 class="text-2xl mb-4">{commission.title}</h1>

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
    <!--<Tabs.Root value="candidates">
        <div id="toolbar" class="w-full">
            <Tabs.List class="content-center">
                <Tabs.Trigger value="candidates">Studenti Candidati</Tabs.Trigger>
                <Tabs.Trigger value="professors">Docenti della Commissione</Tabs.Trigger>
                <Tabs.Trigger value="optimization">Ottimizzazione</Tabs.Trigger>
            </Tabs.List>
        </div>
        <Tabs.Content value="candidates">
            <StudentsTable {commission}/>
        </Tabs.Content>
        <Tabs.Content value="professors" class="text-center">
            <ProfessorsTable {commissionProfessors}/>
        </Tabs.Content>
        <Tabs.Content value="optimization" class="text-center">
            <Card.Root>
                <Card.Header>
                    <Card.Title>Card Title</Card.Title>
                    <Card.Description>Card Description</Card.Description>
                </Card.Header>
                <Card.Content>
                    <p>Card Content</p>
                </Card.Content>
                <Card.Footer>
                    <p>Card Footer</p>
                </Card.Footer>
            </Card.Root>
        </Tabs.Content>
    </Tabs.Root>-->
</div>