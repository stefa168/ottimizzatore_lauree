<script lang="ts" module>
  export type ProfessorAction =
    'split' | 'edit-split' | 'remove-split' |
    'substitute' | 'change-substitute' | 'remove-substitute';
</script>

<script lang="ts">
  import type {SessionProfessor} from "@/types";
  import {EllipsisIcon} from "@lucide/svelte";
  import {Button} from "@/components/ui/button";
  // noinspection ES6UnusedImports
  import * as DropdownMenu from "@/components/ui/dropdown-menu";

  interface Props {
    sp: SessionProfessor;
    children?: SessionProfessor[];
    onAction: (action: ProfessorAction, sp: SessionProfessor) => void;
  }

  let {sp, children = [], onAction}: Props = $props();

  const isSplit = $derived(children.some(c => c.relation === 'SPLIT'));
  const hasSubstitute = $derived(children.some(c => c.relation === 'SUBSTITUTE'));

  // The database allows: splitting only ORIGINAL professors, substituting an ORIGINAL without splits or a SPLIT,
  // and no substitute of a substitute.
  type Entry = { action: ProfessorAction, label: string, destructive?: boolean };
  const entries: Entry[] = $derived.by(() => {
    switch (sp.relation) {
      case 'ORIGINAL':
        if (isSplit) return [
          {action: 'edit-split', label: 'Modifica divisione'},
          {action: 'remove-split', label: 'Rimuovi divisione', destructive: true},
        ];
        return [
          {action: 'split', label: 'Dividi docente'},
          ...(hasSubstitute ? [] : [{action: 'substitute', label: 'Sostituisci docente'} as Entry]),
        ];
      case 'SPLIT':
        return hasSubstitute ? [] : [{action: 'substitute', label: 'Sostituisci questa parte'}];
      case 'SUBSTITUTE':
        return [
          {action: 'change-substitute', label: 'Cambia sostituto'},
          {action: 'remove-substitute', label: 'Rimuovi sostituto', destructive: true},
        ];
    }
  });
</script>

{#if entries.length > 0}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger>
      {#snippet child({props})}
        <Button {...props} variant="ghost" size="icon" class="relative size-8 p-0">
          <span class="sr-only">Apri menu azioni</span>
          <EllipsisIcon/>
        </Button>
      {/snippet}
    </DropdownMenu.Trigger>
    <DropdownMenu.Content align="end">
      <DropdownMenu.Group>
        <DropdownMenu.Label>Azioni</DropdownMenu.Label>
        {#each entries as entry (entry.action)}
          {#if entry.destructive}
            <DropdownMenu.Separator/>
          {/if}
          <DropdownMenu.Item class={[entry.destructive && "text-destructive"]}
                             onclick={() => onAction(entry.action, sp)}>
            {entry.label}
          </DropdownMenu.Item>
        {/each}
      </DropdownMenu.Group>
    </DropdownMenu.Content>
  </DropdownMenu.Root>
{/if}
