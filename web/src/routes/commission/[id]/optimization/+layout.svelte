<script lang="ts">
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";
    import type {OptimizationConfiguration} from "./optimization_types";
    import {goto} from "$app/navigation";
    import {page} from "$app/stores";
    import {onMount} from "svelte";
    import {toast} from "svelte-sonner";

    export let data: { configurations: OptimizationConfiguration[]; };
    $: availableConfigurations = data.configurations;

    function c(id: number): Selected<number> | undefined {

        let config = availableConfigurations.find(c => c.id === id);
        if (!config) return undefined;

        return {value: config?.id, label: config?.title};
    }

    $: selectedConfiguration = c(Number($page.params.opt_id));

    onMount(() => {
        if (data.configurations.length === 0) {
            // This branch is only executed when there are no configurations available, so one is created by default
            fetch(`http://localhost:5000/commission/${$page.params.id}/configuration`, {method: 'POST'})
                .then(r => r.json())
                .then((d: { new_config: OptimizationConfiguration }) => {
                    console.log('no configuration found, created new one', d.new_config);
                    toast.info(`Nessuna configurazione trovata, ne è stata creata una nuova.`);
                    goto(`/commission/${$page.params.id}/optimization/${d.new_config.id}`);
                });
        } else if (data.configurations.length === 1 && $page.params.opt_id === undefined) {
            // This branch is only executed when there is only one configuration available and the user has not selected any
            console.log(`found only one configuration, redirecting to ${data.configurations[0].id} - ${data.configurations[0].title}`);
            toast.info(`Trovata solo una configurazione, la sto selezionando automaticamente.`);
            goto(`/commission/${$page.params.id}/optimization/${data.configurations[0].id}`);
        }
    })

    const handleConfigurationChoice = (v: Selected<number> | undefined) => {
        if (!v) return;
        goto(`/commission/${$page.params.id}/optimization/${v.value}`);
    }
</script>

<Select.Root selected={selectedConfiguration} onSelectedChange={handleConfigurationChoice}>
    <Select.Trigger>
        <Select.Value placeholder="Scegliere una configurazione"/>
    </Select.Trigger>
    <Select.Content>
        <Select.Group>
            <Select.Label>Configurazioni</Select.Label>
            {#each availableConfigurations as config}
                <Select.Item value={config.id} label={config.title}>{config.title}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="role"/>
</Select.Root>

<slot/>