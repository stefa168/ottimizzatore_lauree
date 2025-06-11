<script lang="ts">
    import {BodyRow, type DataBodyRow, DataColumn} from "svelte-headless-table";
    import type {Professor, UniversityRole} from "./commission_types";
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";

    interface Props {
        row: BodyRow<Professor>;
        value: UniversityRole | string;
        onUpdateValue: <T extends keyof Professor>(p: Professor, field: T, newValue: Professor[T]) => void;
    }

    let {row, value = $bindable(), onUpdateValue}: Props = $props();

    const UniversityRoles = [
        {value: 'ordinary', label: 'Professore Ordinario'},
        {value: 'associate', label: 'Professore Associato'},
        {value: 'researcher', label: 'Ricercatore'},
        // Disabled to avoid confusion
        {value: 'unspecified', label: 'Non Specificato', disabled: true}
    ];

    let selected = $derived(UniversityRoles.find(role => role.value === value))

    const handleSubmit = (v: Selected<string> | undefined) => {
        if (row.isData()) {
            onUpdateValue(row.original, "role", (v?.value ?? 'unspecified') as UniversityRole);
        }
        value = v?.value ?? 'unspecified';
    }

</script>

<Select.Root {selected} onSelectedChange={handleSubmit}>
    <Select.Trigger class="{value === 'unspecified' ? 'bg-destructive/25' : ''}">
        <Select.Value class="{value === 'unspecified' ? 'text-destructive' : ''}" placeholder="Indicare il ruolo"/>
    </Select.Trigger>
    <Select.Content>
        <Select.Group>
            <Select.Label>Ruoli</Select.Label>
            {#each UniversityRoles as role}
                <Select.Item value={role.value} label={role.label} disabled={role.disabled}>{role.label}</Select.Item>
            {/each}
        </Select.Group>
    </Select.Content>
    <Select.Input name="role"/>
</Select.Root>