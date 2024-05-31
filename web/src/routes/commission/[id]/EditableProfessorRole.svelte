<script lang="ts">
    import {BodyRow, DataColumn} from "svelte-headless-table";
    import type {Professor, UniversityRole} from "./commission_types";
    import * as Select from '$lib/components/ui/select'
    import type {Selected} from "bits-ui";

    export let row: BodyRow<Professor>;
    export let column: DataColumn<Professor>;
    export let value: UniversityRole | string;
    export let onUpdateValue: (rowDataId: string, columnId: string, newValue: UniversityRole) => void;

    const UniversityRoles = [
        {value: 'ordinary', label: 'Professore Ordinario'},
        {value: 'associate', label: 'Professore Associato'},
        {value: 'researcher', label: 'Ricercatore'},
        // Disabled to avoid confusion
        {value: 'unspecified', label: 'Non Specificato', disabled: true}
    ];

    $: selected = UniversityRoles.find(role => role.value === value)

    const handleSubmit = (v: Selected<string> | undefined) => {
        if (row.isData()) {
            onUpdateValue(row.dataId, column.id, (v?.value ?? 'unspecified') as UniversityRole);
        }
        console.log(value);
        value = v?.value ?? 'unspecified';
        console.log(value);
    }

</script>

<Select.Root {selected} onSelectedChange={handleSubmit}>
    <Select.Trigger>
        <Select.Value class="{value === 'unspecified' ? 'text-red-600' : ''}" placeholder="Indicare il ruolo"/>
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