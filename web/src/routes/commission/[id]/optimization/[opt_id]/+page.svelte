<script lang="ts">
    // Svelte
    import {selectedConfiguration, selectedProblem} from "$lib/store";
    import {derived, get, readonly, type Readable} from "svelte/store";

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

    // Components
    import CommissionCard from "./CommissionCard.svelte";
    import ConfigurationForm from "./ConfigurationForm.svelte";

    // Project modules
    import type {OptimizationStatus, PossibleOptimizationStatuses} from "./types";

    let optStatus: OptimizationStatus = derived([selectedConfiguration], ([conf]) => {
        let status: PossibleOptimizationStatuses = 'not_started';

        if (!conf)
            return {
                configurationLocked: false,
                running: false,
                solutions: {
                    all: [],
                    morning: [],
                    afternoon: []
                },
                status
            };

        let solutions = conf.solution_commissions;

        if (conf.run_lock) {
            if (conf.execution_details.length > 0) {
                status = 'ended';
            } else {
                status = 'running';
            }
        }

        return {
            configurationLocked: conf.run_lock,
            /*
            * The list isn't used outside the first element, it has been implemented this way to be able to hold
            * multiple logs if necessary for further functionalities.
            */
            running: conf.execution_details.length > 0,
            solutions: {
                all: solutions,
                morning: solutions.filter(s => s.morning),
                afternoon: solutions.filter(s => !s.morning)
            },
            status
        };
    });

    let settingsOpened = false;
    let tainted_fields_count: Readable<number>;
    let formComponent: ConfigurationForm;

    let resultsOpened = true;
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
                <div class="flex items-center justify-center mt-4">
                    <MdiData class="w-8 h-8"/>
                    <span class="ms-2">Ottimizzazione non ancora avviata</span>
                </div>
            {/if}
        </div>
    </div>

    <div id="configuration-settings">
        <div class="flex items-center justify-between">
            <button class="mt-4 mb-4 text-xl flex items-center cursor-pointer"
                    on:click={() => settingsOpened = !settingsOpened}>
                <MdiCogPlayOutline class="w-6 h-6 me-2"/>
                <span>Impostazioni</span>
                <MdiChevronRight
                        class="w-6 h-6 ms-2 transition-transform duration-200 {settingsOpened ? 'rotate-90' : ''}"
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

        <div class="transition-all duration-300 ease-in-out overflow-hidden max-w-full {settingsOpened ? 'max-h-[20000px]' : 'max-h-0'}">
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