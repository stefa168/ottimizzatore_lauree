<script lang="ts">
    import "../app.css";
    import {ModeWatcher} from "mode-watcher";
    import {Toaster} from "$lib/components/ui/sonner/";

    // https://kit.svelte.dev/docs/single-page-apps
    export const ssr = false;

    // Icons
    import MdiArchive from '~icons/mdi/archive'
    import MdiAlertCircleOutline from '~icons/mdi/alert-circle-outline'
    import MdiRobotExcited from '~icons/mdi/robot-excited'
    import MdiCogOutline from '~icons/mdi/cog-outline'
    import MdiBookInformationVariant from '~icons/mdi/book-information-variant'
    import MdiLoading from '~icons/mdi/loading'

    // Components
    import DropdownButton from "$lib/sidebar/DropdownButton.svelte";
    import {onMount} from "svelte";
    import {Button} from "$lib/components/ui/button";
    import NewCommissionDialog from "$lib/NewCommissionDialog.svelte";

    // Behaviour
    let fileInput: HTMLInputElement | null;

    async function handle_new_file_submit(event: SubmitEvent) {
        try {
            let excel = fileInput?.files?.[0];

            if (excel == undefined) {
                return;
            }
            if (!(excel.name.endsWith('xlsx') || excel.name.endsWith('xls'))) {
                alert("Sono solo accettati file XLSX o XLS.");
                return;
            }

            let data = new FormData();
            data.append('file', excel)

            const response = await fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: data
            });

            console.log(await response.json());
        } catch (error) {
            console.error("Error:", error)
        }
    }

    let problems_data: { 'loaded': boolean, 'problems': { 'id': number, 'title': string; } [] } = {
        loaded: false,
        problems: []
    };

    async function fetch_problems_list() {
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
         class="flex-grow flex flex-col px-3 overflow-y-scroll ">
        <ul class="space-y-2 font-medium">
            <li>
                <NewCommissionDialog/>
            </li>
            <li>
                <DropdownButton buttonText="Problemi Attivi" loaded={problems_data.loaded} open={true}>
                    {#if problems_data.problems.length > 0}
                        {#each problems_data.problems as problem (problem.id)}
                            <li>
                                <Button href="/commission/{problem.id}"
                                        class="flex items-center pl-6 whitespace-pre-line h-fit gap-x-2"
                                        variant="link">
                                    <span class="flex-shrink-0 bg-blue-600 rounded w-4 h-4"></span>
                                    <span class="flex-grow">{problem.title}</span>
                                </Button>
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
                    <MdiArchive class="me-2 h-4 w-4"/>
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

<main class="p-4 sm:ml-64">
    <slot/>
</main>