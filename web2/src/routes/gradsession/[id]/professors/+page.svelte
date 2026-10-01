<script lang="ts">
  import {columns, initialTableState} from "./columns";
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";
  import {Input} from "@/components/ui/input";
  import type {SessionProfessor} from "@/types";
  import {Button} from "@/components/ui/button";
  // noinspection ES6UnusedImports
  import * as Dialog from "@/components/ui/dialog";
  import LucideSearch from '~icons/lucide/search'
  import TableTooltip from "@/components/TableTooltip.svelte";
  import SplitProfessorDialog from "./SplitProfessorDialog.svelte";
  import SubstituteProfessorDialog from "./SubstituteProfessorDialog.svelte";
  import type {ProfessorAction} from "./ProfessorRowActions.svelte";
  import {removeSubstitute, splitSessionProfessor} from "@/api/professors.remote";
  import {toApiError} from "@/errors";
  import {fullName} from "@/utils";
  import {toast} from "svelte-sonner";
  import {LucideLoaderCircle} from "@lucide/svelte";

  let sessionData = getSessionData();

  let initialState = $state(initialTableState());

  let t: DataTable<SessionProfessor, string> | undefined = $state();
  let table = $derived(t?.table)

  // Splits and substitutes are shown nested under the professor they derive from
  const topLevelProfessors = $derived(sessionData.sessionProfessors.filter(sp => sp.derived_from_id === null));
  const getSubRows = (sp: SessionProfessor) => sessionData.childrenOf.get(sp.id);
  const getRowId = (sp: SessionProfessor) => String(sp.id);

  let splitTarget = $state<SessionProfessor | null>(null);
  let substituteTarget = $state<SessionProfessor | null>(null);

  type Confirmation = { title: string, description: string, confirmLabel: string, run: () => Promise<void> };
  let confirmation = $state<Confirmation | null>(null);
  let confirming = $state(false);

  const onAction = (action: ProfessorAction, sp: SessionProfessor) => {
    switch (action) {
      case 'split':
      case 'edit-split':
        splitTarget = sp;
        break;
      case 'substitute':
      case 'change-substitute':
        substituteTarget = sp;
        break;
      case 'remove-split':
        confirmation = {
          title: `Rimuovere la divisione di ${fullName(sp.professor)}?`,
          description: "Tutte le parti (ed eventuali sostituti delle parti) verranno eliminate e i laureandi " +
            "torneranno al docente originale.",
          confirmLabel: "Rimuovi divisione",
          run: async () => {
            await splitSessionProfessor({sid: sessionData.session.id, spId: sp.id, parts: [], ignoreSubstitutes: true});
            toast.success("Divisione rimossa.");
          }
        };
        break;
      case 'remove-substitute': {
        const parent = sp.derived_from_id !== null ? sessionData.sessionProfessorsMap.get(sp.derived_from_id) : undefined;
        confirmation = {
          title: `Rimuovere il sostituto ${fullName(sp.professor)}?`,
          description: `I laureandi torneranno ${parent?.relation === 'SPLIT' ? 'alla parte' : 'al docente'} ` +
            `${fullName(parent?.professor)}.`,
          confirmLabel: "Rimuovi sostituto",
          run: async () => {
            await removeSubstitute({sid: sessionData.session.id, spId: sp.id});
            toast.success("Sostituto rimosso.");
          }
        };
        break;
      }
    }
  };

  const confirm = async () => {
    if (!confirmation) return;
    confirming = true;
    try {
      await confirmation.run();
      confirmation = null;
    } catch (err) {
      console.error(err);
      toast.error("Si è verificato un errore durante l'operazione", {
        duration: Number.POSITIVE_INFINITY,
        description: toApiError(err).detail
      });
    } finally {
      confirming = false;
    }
  };
</script>

<div class="flex pb-4">
  <div class="relative">
    <Input
        placeholder="Cerca un docente..."
        class="h-8 pl-7"
        value={table?.getColumn("surname")?.getFilterValue() ?? ""}
        onchange={(e) => {
          table?.getColumn("surname")?.setFilterValue(e.currentTarget.value);
        }}
        oninput={(e) => {
          table?.getColumn("surname")?.setFilterValue(e.currentTarget.value);
        }}
    />
    <LucideSearch class="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 select-none opacity-50"/>
  </div>
  <Button
      class="h-8 ms-2"
      variant="outline"
      onclick={() => {table?.resetSorting(); table?.resetColumnFilters();}}>
    Resetta la tabella
  </Button>

  <div class="place-self-end ms-auto me-2">
    <TableTooltip/>
  </div>
</div>

<DataTable
    bind:this={t}
    data={topLevelProfessors}
    columns={columns(sessionData, onAction)}
    {getSubRows}
    {getRowId}
    {initialState}
/>

<SplitProfessorDialog sd={sessionData} target={splitTarget} onClose={() => splitTarget = null}/>
<SubstituteProfessorDialog sd={sessionData} target={substituteTarget} onClose={() => substituteTarget = null}/>

<Dialog.Root open={confirmation !== null} onOpenChange={(open) => { if (!open && !confirming) confirmation = null; }}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>{confirmation?.title}</Dialog.Title>
      <Dialog.Description>{confirmation?.description}</Dialog.Description>
    </Dialog.Header>
    <Dialog.Footer>
      <Button variant="outline" onclick={() => confirmation = null} disabled={confirming}>Annulla</Button>
      <Button variant="destructive" onclick={confirm} disabled={confirming}>
        {#if confirming}<LucideLoaderCircle class="animate-spin"/>{/if}
        {confirmation?.confirmLabel}
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
