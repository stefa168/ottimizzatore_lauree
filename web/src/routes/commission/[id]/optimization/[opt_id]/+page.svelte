<script lang="ts">
    // Svelte
    import {selectedConfiguration, selectedProblem} from "$lib/store";
    import {derived, get, type Readable} from "svelte/store";
    // noinspection TypeScriptCheckImport
    import {env} from "$env/dynamic/public";

    // Shadcn
    import {Button} from "$lib/components/ui/button";
    import {Separator} from "$lib/components/ui/separator";

    // Icons
    import MdiReminder from '~icons/mdi/reminder'
    import MdiChevronRight from '~icons/mdi/chevron-right'
    import MdiCogPlayOutline from '~icons/mdi/cog-play-outline'
    import MdiUndoVariant from '~icons/mdi/undo-variant'
    import MdiCloudArrowUp from '~icons/mdi/cloud-arrow-up'
    import MdiContentDuplicate from '~icons/mdi/content-duplicate'
    import MdiData from '~icons/mdi/data'
    import MdiLoading from "~icons/mdi/loading";
    import MdiCubeSend from '~icons/mdi/cube-send'
    import MdiExclamation from '~icons/mdi/exclamation'

    // Components
    import CommissionCard from "./CommissionCard.svelte";
    import ConfigurationForm from "./ConfigurationForm.svelte";

    // Project modules
    import {getOptimizationStatus, type OptimizationStatus} from "./types";
    import {toast} from "svelte-sonner";
    import {onDestroy, onMount} from "svelte";
    import type {OptimizationConfiguration} from "../optimization_types";
    import {Poller} from "$lib/Poller";
    import {browser} from "$app/environment";
    import {invalidateAll} from "$app/navigation";
    import {page} from "$app/stores";
    import {error} from "@sveltejs/kit";

    let optStatus: OptimizationStatus = derived([selectedConfiguration], ([conf]) => getOptimizationStatus(conf));

    let settingsOpen = false;
    let tainted_fields_count: Readable<number>;
    let formComponent: ConfigurationForm;

    let resultsOpened = true;

    async function startOptimization() {
        const problem = get(selectedProblem);
        const configuration = get(selectedConfiguration);

        if (problem === undefined || configuration === undefined) {
            console.error('Problem or configuration not selected');
            return;
        }

        // We lock the configuration to prevent further modifications. This happens also on the backend, so we do this
        // to reflect the change on the UI.
        selectedConfiguration.update(conf => {
            if (conf === undefined) return undefined;

            return {
                ...conf,
                run_lock: true
            };
        });

        await fetch(`${env.PUBLIC_API_URL}/commission/${problem.id}/solve/${configuration.id}`, {method: 'POST'})
            .then(response => {
                if (!response.ok) {
                    // todo improve error presentation
                    toast.error(`Errore durante l'avvio dell'ottimizzazione: ${response.statusText}`);
                    throw new Error('Failed to start the optimization');
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
            })
            .catch(error => {
                console.error(error);

            });
    }

    let pollingInstance: Poller<OptimizationConfiguration> | null = null;

    onMount(() => {
        // Fix for some weird bug that happens when the page is not reloaded and the section changes
        const opt_id = Number($page.params.opt_id);
        const configuration = $selectedProblem!!.optimization_configurations.find((c) => Number(c.id) == opt_id);
        selectedConfiguration.set(configuration);
    });

    // Listener for the optimization status
    optStatus.subscribe(({status}) => {
        if (!browser) return;
        if (status === 'running' && !pollingInstance) {
            const problem = get(selectedProblem);
            const configuration = get(selectedConfiguration);

            if (problem === undefined || configuration === undefined) {
                console.error('Problem or configuration not selected');
                return;
            }

            pollingInstance = new Poller<OptimizationConfiguration>(
                `${env.PUBLIC_API_URL}/commission/${problem.id}/configuration/${configuration.id}`, 2 * 1000,
                (data) => {
                    // We have received the configuration from the server. The optimization may have ended or not.
                    // We want to update the store only if the optimization has ended.
                    const status = getOptimizationStatus(data);
                    if (status.status === 'ended') {
                        console.log("Optimization ended", data)
                        // todo check if this creates a new object or updates the existing one. might be a problem if it creates a new object
                        selectedConfiguration.set(data);
                        selectedProblem.update(p => {
                            if (p === undefined) return undefined;
                            // We update the configuration in the problem to reflect the found solution.
                            const new_c = p.optimization_configurations.map(c => c.id == data.id ? data : c);
                            console.log(new_c);

                            return {...p, optimization_configurations: new_c};
                        });
                        invalidateAll();
                    }
                },
                (error) => {
                    console.error(error);
                }
            );

            pollingInstance.start();
        } else {
            if (pollingInstance) {
                pollingInstance.stop();
                pollingInstance = null;
            }
        }
    });

    onDestroy(() => {
        if (pollingInstance) {
            pollingInstance.stop();
            pollingInstance = null;
        }
    });
</script>

{#if $selectedConfiguration}
    <div id="configuration-results">
        <div>
            <button class="mt-4 mb-4 text-xl flex items-center cursor-pointer"
                    on:click={() => resultsOpened = !resultsOpened}>
                <MdiData class="w-6 h-6 me-2 {($optStatus.status === 'running') ? 'animate-spin' : ''}"
                         style="animation-duration: 2s"/>
                <span>Risultati</span>
                <MdiChevronRight
                        class="w-6 h-6 ms-2 transition-transform duration-200 {resultsOpened ? 'rotate-90' : ''}"
                        aria-hidden="true"
                />
            </button>
        </div>


        <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {resultsOpened ? 'max-h-[20000px]' : 'max-h-0'}">

            {#if $optStatus.status === 'running'}
                <div class="flex items-center justify-center mt-4">
                    <MdiLoading class="w-6 h-6 ms-4 animate-spin" style="animation-duration: 2s"/>
                    <span class="ms-2">Ottimizzazione in corso</span>
                </div>
            {:else if $optStatus.status === 'ended'}
                {#if $optStatus.solutions.morning.length > 0}
                    <h3 class="border-b mb-4 pe-2 pb-1 pt-2">Commissioni Mattutine</h3>
                    <div class="flex flex-wrap gap-4 pb-2">
                        {#each $optStatus.solutions.morning as solution}
                            <CommissionCard commission={solution} problem={$selectedProblem}/>
                        {/each}
                    </div>
                {/if}

                {#if $optStatus.solutions.afternoon.length > 0}
                    <h3 class="border-b mb-4 pe-2 pb-1 pt-2">Commissioni Pomeridiane</h3>
                    <div class="flex flex-wrap gap-4">
                        {#each $optStatus.solutions.afternoon as solution}
                            <CommissionCard commission={solution} problem={$selectedProblem}/>
                        {/each}
                    </div>
                {/if}
            {:else}
                <!-- We still have to start the optimization -->
                <div class="flex items-center flex-col">
                    <div class="flex items-center self-center mt-4">
                        <MdiExclamation class="w-8 h-8"/>
                        <span>Ottimizzazione non ancora avviata</span>
                    </div>
                    <Button class="mt-2" on:click={startOptimization}>
                        <MdiCubeSend class="h-4 w-4 me-2"/>
                        <span>Avvia l'ottimizzazione</span>
                    </Button>
                </div>
            {/if}
        </div>
    </div>

    <div id="configuration-settings">
        <div class="flex items-center justify-between">
            <button class="mt-4 mb-4 text-xl flex items-center cursor-pointer"
                    on:click={() => settingsOpen = !settingsOpen}>
                <MdiCogPlayOutline class="w-6 h-6 me-2"/>
                <span>Impostazioni</span>
                <MdiChevronRight
                        class="w-6 h-6 ms-2 transition-transform duration-200 {settingsOpen ? 'rotate-90' : ''}"
                        aria-hidden="true"
                />
            </button>
            <div class="transition-all duration-150 ease-in-out {$tainted_fields_count > 0 ? 'opacity-100' : 'opacity-0 invisible'}"
                 role="group">
                <Button variant="ghost"
                        on:click={() => formComponent.reset()}
                        disabled={$tainted_fields_count === 0}>
                    <MdiUndoVariant class="h-4 w-4 me-2"/>
                    <span>Annulla le modifiche</span>
                </Button>

                <Button variant="ghost"
                        on:click={() => formComponent.submit()}
                        disabled={$tainted_fields_count === 0}>
                    <MdiCloudArrowUp class="h-4 w-4 me-2"/>
                    <span>Salva le modifiche</span>
                </Button>
            </div>
        </div>

        <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {settingsOpen ? 'max-h-[20000px]' : 'max-h-0'}">
            {#if $optStatus.configurationLocked || $optStatus.solutions.all.length > 0}
                <div class="flex items-center mt-2 mb-4 text-[0.8rem] text-yellow-600 group dark:text-yellow-400">
                    <MdiReminder class="w-5 h-5"/>
                    <!-- todo we are expecting that the optimization doesn't fail, but that could be the case sometimes -->
                    <span class="flex items-center justify-start ms-2">
                        {#if $optStatus.solutions.all.length > 0}
                            La configurazione è già stata usata per trovare una soluzione.
                        {:else}
                            La configurazione è stata inviata per l'ottimizzazione.
                        {/if}
                        Non è possibile modificarla.
                        Puoi sempre
                        <button class="flex ms-[2px] hover:underline">
                            <!--todo-->
                            <MdiContentDuplicate class="h-4 w-4 me-[2px]"/> duplicarla
                        </button>
                        .
                    </span>
                </div>
            {/if}
            {#key $selectedConfiguration}
                <ConfigurationForm
                        {optStatus}
                        selectedConfiguration={selectedConfiguration}
                        bind:tainted_fields_count
                        bind:this={formComponent}
                />
            {/key}
        </div>
    </div>

    <Separator decorative={true}/>
{/if}