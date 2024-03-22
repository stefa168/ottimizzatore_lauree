<script lang="ts">
    import "../app.css";
    import {ModeWatcher, userPrefersMode} from "mode-watcher";
    import {toast} from "svelte-sonner";
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
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Switch from "$lib/components/ui/switch";
    import * as Select from "$lib/components/ui/select";
    import {Button} from "$lib/components/ui/button";
    import {Toaster} from "$lib/components/ui/sonner";
    import type {Commission} from "./commission/[id]/commission_types";
    import {
        type CommissionPreview,
        commissionsPreviewLoaded,
        commissionsPreview,
        fetchCommissionPreviews,
        deleteCommission, debugEnabled
    } from "$lib/store";
    import {Separator} from "$lib/components/ui/separator";
    import type {Selected} from "bits-ui";
    import {get} from "svelte/store";

    onMount(async () => {
        await fetchCommissionPreviews();
    });

    let deletionAlertOpen = false;
    let commissionToBeDeleted: CommissionPreview | null = null;

    function openDeletionAlert(problemId: CommissionPreview) {
        commissionToBeDeleted = problemId;
        deletionAlertOpen = true;
    }

    function onDeletionAlertStateChange(open: boolean) {
        if (!open) {
            commissionToBeDeleted = null;
        }
    }

    function startCommissionDeletion() {
        if (commissionToBeDeleted !== null) {
            // todo catch potential errors
            deleteCommission(commissionToBeDeleted).then(() => {
                onDeletionAlertStateChange(false);
                toast.success("La commissione è stata eliminata correttamente.");
                // todo redirect only if the currently opened commission is the one that has been deleted
                // todo redirect eagerly to avoid potential issues
                goto('/');
            });
        }
    }

    let settingsPopoverOpen = false;
    const handleThemeChange = (value: Selected<string> | undefined) => {
        const theme = value?.value;
        if (theme !== "system" && theme !== "light" && theme !== "dark") return;
        userPrefersMode.set(theme);
    }

    const themes: Selected<string>[] = [
        {value: "light", label: "Chiaro"},
        {value: "dark", label: "Scuro"},
        {value: "system", label: "Sistema"}
    ];
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
         class="flex-grow flex flex-col px-3 overflow-y-scroll">
        <ul class="space-y-2 font-medium">
            <li>
                <NewCommissionDialog/>
            </li>
            <li>
                <DropdownButton buttonText="Problemi Attivi"
                                childCount={$commissionsPreview.length}
                                loaded={$commissionsPreviewLoaded}
                                open={true}>
                    {#if $commissionsPreview.length > 0}
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
                                    <AlertDialog.Action on:click={startCommissionDeletion}
                                                        class="bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90">
                                        Continua
                                    </AlertDialog.Action>
                                </AlertDialog.Footer>
                            </AlertDialog.Content>
                        </AlertDialog.Root>
                        {#each $commissionsPreview as problem (problem.id)}
                            <li>
                                <ContextMenu.Root>
                                    <ContextMenu.Trigger>
                                        <Button data-sveltekit-preload-data="tap"
                                                href="/commission/{problem.id}/"
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
                        <li class="flex items-center mx-2 ps-4 p-2 text-yellow-600 group dark:text-yellow-400">
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
        <ul class="ps-0.5 space-y-0.5 text-md text-gray-600 dark:text-gray-500">
            <li>
                <button class="flex items-center transition dark:hover:text-white">
                    <MdiRobotExcited/>
                    <span class="ms-1.5">Stato Solver</span>
                </button>
            </li>
            <li>
                <button class="flex items-center transition dark:hover:text-white"
                        on:click={() => settingsPopoverOpen = !settingsPopoverOpen}>
                    <MdiCogOutline/>
                    <span class="ms-1.5">Impostazioni</span>
                </button>
                <Dialog.Root bind:open={settingsPopoverOpen}>
                    <Dialog.Content>
                        <Dialog.Header class="mb-2">
                            <Dialog.Title>
                                Impostazioni dell'Interfaccia
                            </Dialog.Title>
                        </Dialog.Header>
                        <div class="flex flex-row items-center justify-between px-4">
                            <div class="space-y-0.5">
                                <div class="flex items-center justify-between">
                                    <div class="text-sm font-medium leading-none mb-2">
                                        Tema
                                    </div>
                                    <Select.Root
                                            onSelectedChange={handleThemeChange}
                                            selected={themes.find(t => t.value === get(userPrefersMode))}>
                                        <Select.Trigger class="w-[180px]">
                                            <Select.Value placeholder="Tema"/>
                                        </Select.Trigger>
                                        <Select.Content>
                                            {#each themes as theme (theme.value)}
                                                <Select.Item value={theme.value}>
                                                    {theme.label}
                                                </Select.Item>
                                            {/each}
                                        </Select.Content>
                                    </Select.Root>
                                </div>
                                <div class="text-[0.8rem] text-muted-foreground mt-2">
                                    È possibile scegliere tra un'interfaccia chiara e una scura. In alternativa, è
                                    possibile lasciare che il sistema scelga automaticamente in base alle impostazioni
                                    del sistema operativo.
                                </div>
                            </div>

                        </div>
                        <Separator decorative={true}/>
                        <div class="flex flex-row items-center justify-between px-4">
                            <div class="space-y-0.5">
                                <div class="text-sm font-medium leading-none mb-2">
                                    Debug
                                </div>
                                <div class="text-[0.8rem] text-muted-foreground">
                                    Attivando questa impostazione verranno mostrati, dove predisposti, una serie di dati
                                    aggiuntivi utili per lo sviluppo.
                                </div>
                            </div>
                            <Switch.Root bind:checked={$debugEnabled}/>
                        </div>
                    </Dialog.Content>
                </Dialog.Root>
            </li>
            <li>
                <button class="flex items-center transition dark:hover:text-white">
                    <MdiBookInformationVariant/>
                    <span class="ms-1.5">Documentazione</span>
                </button>
            </li>
        </ul>
    </footer>
</aside>

<main class="pt-6 p-4 sm:ml-64 transition duration-1000 ease-in-out relative">
    <slot/>
</main>