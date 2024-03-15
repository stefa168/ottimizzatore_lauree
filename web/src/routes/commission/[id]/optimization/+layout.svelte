<script lang="ts">
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";
    import type {OptimizationConfiguration} from "./optimization_types";
    import {goto} from "$app/navigation";
    import {page} from "$app/stores";

    const handleSubmit = (v: Selected<number> | undefined) => {
        if(!v) return;

        goto(`/commission/${$page.params.id}/optimization/${v.value}`);
    }

    export let data: { configurations: OptimizationConfiguration[]; };
    $: availableConfigurations = data.configurations;
</script>

<Select.Root onSelectedChange={handleSubmit}>
    <Select.Trigger>
        <Select.Value placeholder="Scegliere una configurazione"/>
    </Select.Trigger>
    <Select.Content>
        <Select.Group>
            <Select.Label>Configurazioni</Select.Label>
            {#each availableConfigurations as config}
                <Select.Item value={config.id} label={`Configurazione ${config.id}`}>Configurazione {config.id}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="role"/>
</Select.Root>

<slot/>