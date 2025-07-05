<script lang="ts">
  import * as Select from '@/components/ui/select'
  import type {SessionProfessor, UniversityRole} from "@/types";

  interface Props {
    // row: BodyRow<Professor>;
    value: UniversityRole | string;
    onUpdateValue?: (newRole: UniversityRole) => Promise<void>;
  }

  let {value = $bindable(), onUpdateValue}: Props = $props();

  const UniversityRoles: { value: string, label: string, disabled?: boolean }[] = [
    {value: 'ordinary', label: 'Professore Ordinario'},
    {value: 'associate', label: 'Professore Associato'},
    {value: 'researcher', label: 'Ricercatore'},
    // Disabled to avoid users removing a role from a Professor
    {value: 'unspecified', label: 'Non Specificato', disabled: true}
  ];

  let selectedLabel = $derived(UniversityRoles.find(role => role.value === value) ?? {
    value: '',
    label: "Seleziona un ruolo"
  })

  const onValueChange = async (v: string) => {
    if(!onUpdateValue)
      return;

    return await onUpdateValue(v as UniversityRole);
  };
</script>

<Select.Root type="single" bind:value={value} {onValueChange}>
  <Select.Trigger style="height: 1.6rem">
    {selectedLabel.label}
  </Select.Trigger>
  <Select.Content>
    <Select.Group>
      <Select.Label>Ruoli</Select.Label>
      {#each UniversityRoles as role}
        <Select.Item value={role.value} label={role.label} disabled={role.disabled}>{role.label}</Select.Item>
      {/each}
    </Select.Group>
  </Select.Content>
  <!--  <Select.Input name="role"/>-->
</Select.Root>