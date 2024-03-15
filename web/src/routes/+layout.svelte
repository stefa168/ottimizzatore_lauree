<script lang="ts">
    import "../app.css";
    import {ModeWatcher} from "mode-watcher";
    import {toast} from "svelte-sonner";
    import type {CommissionUploadSuccessEvent} from "./schema";
    import {goto, beforeNavigate, afterNavigate} from "$app/navigation";
    import {onMount} from "svelte";

    // Icons
    import MdiAlertCircleOutline from '~icons/mdi/alert-circle-outline'
    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'
    import MdiLoading from '~icons/mdi/loading'
    import RadixIconsTrash from '~icons/radix-icons/trash'
    import RadixIconsArchive from '~icons/radix-icons/archive'
    import RadixIconsPencil2 from '~icons/radix-icons/pencil-2'

    // Components
    import DropdownButton from "$lib/sidebar/DropdownButton.svelte";
    import NewCommissionDialog from "$lib/NewCommissionDialog.svelte";
    import * as ContextMenu from "$lib/components/ui/context-menu"
    import * as AlertDialog from "$lib/components/ui/alert-dialog";
    import {Button} from "$lib/components/ui/button";
    import {Toaster} from "$lib/components/ui/sonner";

    type CommissionMinimal = {
        id: number;
        title: string;
    }

    let problems_data: { 'loaded': boolean, 'problems': CommissionMinimal [] } = {
        loaded: false,
        problems: []
    };

    async function fetch_problems_list() {
        problems_data.loaded = false;
        problems_data.problems = [];

        try {
            fetch('http://localhost:5000/commission')
                .then(response => response.json())
                .then((data) => {
                    problems_data.problems = data;
                    problems_data.loaded = true;
                })
            console.log(problems_data);
        } catch (err) {
            console.error(err);
        }
    }

    onMount(async () => {
        await fetch_problems_list();
    });

    function uploadSuccess(event: CommissionUploadSuccessEvent) {
        const d = event.detail;
        problems_data.problems.push({id: d.id, title: d.name});
        // Force reactivity
        problems_data = problems_data;
        toast.success("La commissione è stata salvata correttamente; la sto aprendo...");
        goto(`/commission/${d.id}`)
    }

    let deletionAlertOpen = false;
    let commissionToBeDeleted: CommissionMinimal | null = null;

    function openDeletionAlert(problemId: CommissionMinimal) {
        commissionToBeDeleted = problemId;
        deletionAlertOpen = true;
    }

    function onDeletionAlertStateChange(open: boolean) {
        if (!open) {
            commissionToBeDeleted = null;
        }
    }

    function deleteCommission() {
        if (commissionToBeDeleted !== null) {
            fetch(`http://localhost:5000/commission/${commissionToBeDeleted.id}`, {
                method: 'DELETE'
            }).then(() => {
                problems_data.problems = problems_data.problems.filter(p => p.id !== commissionToBeDeleted?.id);
                problems_data = problems_data;
                onDeletionAlertStateChange(false);
                toast.success("La commissione è stata eliminata correttamente.");
                goto('/');
            });
        }
    }

    $: loadingProblem = false;

    beforeNavigate(({from, to}) => {
        // If the id changes it means that we are moving to a new page.
        // Only in this case we want to show the loading message because we might take a while to load the data of the
        // new commission chosen.
        console.log(from, to, from?.route.id, to?.route.id)
        if (from?.params?.id != to?.params?.id) {
            loadingProblem = true;
        }
    });

    afterNavigate(() => {
        loadingProblem = false;
    });
</script>

<ModeWatcher/>
<Toaster closeButton/>

<aside id="sidebar"
       class="flex flex-col fixed top-0 left-0 z-40 w-64 h-full transition-transform -translate-x-full sm:translate-x-0 border-e"
       aria-label="Sidebar">
    <!-- Titolo -->
    <header id="sidebar-logo"
            class="px-4 py-4">
        <a href="/" class="flex items-center ">
            <img src="/Logo_UniTO_2022_no_testo.svg" class="h-12" alt="Logo Unito"/>
            <h3 class="self-center text-center scroll-m-20 text-2xl font-semibold tracking-tight">
                Ottimizzatore Lauree
            </h3>
        </a>
    </header>
    <nav id="sidebar-problems-navigator"
         class="flex-grow flex flex-col px-3 overflow-y-scroll {loadingProblem ? 'blur-sm pointer-events-none' : ''}">
        <ul class="space-y-2 font-medium">
            <li>
                <NewCommissionDialog on:commission-created={uploadSuccess}/>
            </li>
            <li>
                <DropdownButton buttonText="Problemi Attivi" childCount={problems_data.problems.length}
                                loaded={problems_data.loaded} open={true}>
                    {#if problems_data.problems.length > 0}
                        <AlertDialog.Root bind:open={deletionAlertOpen}>
                            <AlertDialog.Content>
                                <AlertDialog.Header>
                                    <AlertDialog.Title class="text-destructive">
                                        Confermi l'eliminazione della commissione "{commissionToBeDeleted?.title}"?
                                    </AlertDialog.Title>
                                    <AlertDialog.Description>
                                        <p>Questa operazione è <span class="underline">irreversibile</span>, ed
                                            eliminerà tutti i dati associati alla commissione (studenti e
                                            configurazione, <strong>NON i docenti</strong>).</p>
                                        <p>Vuoi procedere?</p>
                                    </AlertDialog.Description>
                                </AlertDialog.Header>
                                <AlertDialog.Footer>
                                    <AlertDialog.Cancel>Annulla</AlertDialog.Cancel>
                                    <AlertDialog.Action on:click={deleteCommission}
                                                        class="bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90">
                                        Continua
                                    </AlertDialog.Action>
                                </AlertDialog.Footer>
                            </AlertDialog.Content>
                        </AlertDialog.Root>
                        {#each problems_data.problems as problem (problem.id)}
                            <li>
                                <ContextMenu.Root>
                                    <ContextMenu.Trigger>
                                        <Button href="/commission/{problem.id}/info"
                                                class="flex items-center pl-6 whitespace-pre-line h-fit gap-x-2"
                                                variant="link">
                                            <span class="flex-shrink-0 bg-blue-600 rounded w-4 h-4"></span>
                                            <span class="flex-grow break-words hyphens-auto">{problem.title}</span>
                                        </Button>
                                    </ContextMenu.Trigger>
                                    <ContextMenu.Content>
                                        <ContextMenu.Item>
                                            <RadixIconsPencil2 class="me-2 w-4 h-4"/>
                                            Rinomina
                                        </ContextMenu.Item>
                                        <ContextMenu.Item>
                                            <RadixIconsArchive class="me-2 w-4 h-4"/>
                                            Archivia
                                        </ContextMenu.Item>
                                        <ContextMenu.Separator/>
                                        <ContextMenu.Item
                                                class="text-destructive"
                                                on:click={(_) => openDeletionAlert(problem)}>
                                            <RadixIconsTrash class="me-1 w-4 h-4"/>
                                            Elimina
                                        </ContextMenu.Item>
                                    </ContextMenu.Content>
                                </ContextMenu.Root>
                            </li>
                        {/each}
                    {:else}
                        <li class="flex items-center mx-2 ps-4 p-2 text-amber-600 group dark:text-amber-400">
                            <MdiAlertCircleOutline class="w-5 h-5"/>
                            <span class="ms-2 text-sm font-medium">Nessun problema disponibile</span>
                        </li>
                    {/if}
                </DropdownButton>
            </li>
            <li class="mt-4 pb-4 ">
                <Button variant="ghost" class="px-3 w-full justify-start">
                    <RadixIconsArchive class="me-2 h-4 w-4"/>
                    Problemi Archiviati
                </Button>
            </li>
        </ul>
    </nav>
    <footer id="sidebar-footer"
            class="flex-shrink-0 p-4 w-full z-60 bottom-0 start-0 pt-4 border-t">
        <ul class="ps-0.5 space-y-0.5 text-md text-gray-400 dark:text-gray-500">
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiRobotExcited/>
                    <span class="ms-1.5">Stato Solver</span>
                </a>
            </li>
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiCogOutline/>
                    <span class="ms-1.5">Impostazioni</span>
                </a>
            </li>
            <li>
                <a href="#"
                   class="flex items-center transition dark:hover:text-white">
                    <MdiBookInformationVariant/>
                    <span class="ms-1.5">Documentazione</span>
                </a>
            </li>
        </ul>
    </footer>
</aside>

<main class="pt-6 p-4 sm:ml-64 transition duration-1000 ease-in-out relative">
    {#if loadingProblem}
        <div id="loadingMessage"
             class="mt-32 flex flex-col items-center justify-center h-max absolute z-10 w-full"
             style="position: absolute">
            <MdiLoading class="w-16 h-16 animate-spin"/>
            <span class="mt-4 text-lg font-medium">Caricando...</span>
        </div>
    {/if}
    <slot class="{loadingProblem ? 'blur-sm pointer-events-none' : ''}"/>
</main>