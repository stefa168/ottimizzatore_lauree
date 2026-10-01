<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Dialog from "@/components/ui/dialog";
  import {Button} from "@/components/ui/button";
  import {Input} from "@/components/ui/input";
  import StyledFullName from "@/components/StyledFullName.svelte";
  import ProfessorAvailabilitySelector from "./ProfessorAvailabilitySelector.svelte";
  import type {SessionData} from "../../SessionData.svelte";
  import type {
    ApiErrorResponse,
    GradSessionEntry,
    ProfessorAvailability,
    SessionProfessor,
    SessionProfessorSplitConflict
  } from "@/types";
  import {GradSessionApi} from "@/api/GradSesssionApi";
  import {fullName, getDegreeLevelString} from "@/utils";
  import {toast} from "svelte-sonner";
  import {untrack} from "svelte";
  import {LucideLoaderCircle, LucidePlus, LucideTrash2, LucideTriangleAlert} from "@lucide/svelte";

  interface Props {
    sd: SessionData;
    // The ORIGINAL Session Professor to split; the dialog is open while it's set
    target: SessionProfessor | null;
    onClose: () => void;
  }

  let {sd, target, onClose}: Props = $props();

  type Part = { when: ProfessorAvailability, note: string };

  let parts = $state<Part[]>([]);
  // Student entry id -> index of the part it's assigned to
  let assignment = $state<Record<number, number | undefined>>({});
  let entries = $state<GradSessionEntry[]>([]);
  let saving = $state(false);
  // Set when the professor has substitutes that the split would remove
  let substituteConflict = $state(false);

  const isEdit = $derived(target !== null && (sd.childrenOf.get(target.id) ?? []).some(c => c.relation === 'SPLIT'));

  const init = (t: SessionProfessor) => {
    const existingSplits = (sd.childrenOf.get(t.id) ?? [])
      .filter(c => c.relation === 'SPLIT')
      .toSorted((a, b) => a.id - b.id);

    const supervised = sd.supervisedEntries(t.id)
      .toSorted((a, b) => fullName(a.candidate).localeCompare(fullName(b.candidate)));
    entries = supervised;
    substituteConflict = false;

    if (existingSplits.length >= 2) {
      parts = existingSplits.map(s => ({when: s.availability, note: s.user_note ?? ''}));
      // A student supervised by the substitute of a split belongs to that split
      const partOf = new Map<number, number>();
      existingSplits.forEach((s, i) => sd.subtreeIds(s.id).forEach(id => partOf.set(id, i)));
      assignment = Object.fromEntries(supervised.map(e => [e.id, partOf.get(e.supervisor_id)]));
    } else {
      parts = [{when: 'morning', note: ''}, {when: 'afternoon', note: ''}];
      assignment = {};
    }
  };

  // Initialise the form every time the dialog is opened for a professor
  $effect(() => {
    const t = target;
    if (t) untrack(() => init(t));
  });

  const unassigned = $derived(entries.filter(e => assignment[e.id] === undefined).length);
  const emptyParts = $derived(parts
    .map((_, i) => i)
    .filter(i => !entries.some(e => assignment[e.id] === i)));
  const valid = $derived(parts.length >= 2 && unassigned === 0 && emptyParts.length === 0);

  const addPart = () => {
    parts.push({when: 'always', note: ''});
  };

  const removePart = (index: number) => {
    parts.splice(index, 1);
    // Students of the removed part become unassigned; the following parts shift down by one
    assignment = Object.fromEntries(Object.entries(assignment).map(([id, p]) => [
      id, p === undefined || p === index ? undefined : p > index ? p - 1 : p
    ]));
  };

  const save = async (ignoreSubstitutes = false) => {
    if (!target || !valid) return;
    saving = true;
    try {
      await GradSessionApi().splitSessionProfessor(sd.session.id, target.id, parts.map((p, i) => ({
        when: p.when,
        note: p.note.trim() || null,
        students: entries.filter(e => assignment[e.id] === i).map(e => e.id)
      })), ignoreSubstitutes);
      await sd.refresh();
      toast.success(isEdit ? "Divisione del docente aggiornata." : "Docente diviso correttamente.");
      onClose();
    } catch (err) {
      const apiError = err as ApiErrorResponse<SessionProfessorSplitConflict>;
      if (apiError?.status_code === 409 && apiError.extra?.had_substitutes) {
        substituteConflict = true;
        return;
      }
      console.error(err);
      toast.error("Si è verificato un errore durante la divisione del docente", {
        duration: Number.POSITIVE_INFINITY,
        description: apiError?.detail ?? JSON.stringify(err)
      });
    } finally {
      saving = false;
    }
  };
</script>

<Dialog.Root open={target !== null} onOpenChange={(open) => { if (!open) onClose(); }}>
  <Dialog.Content class="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
    <Dialog.Header>
      <Dialog.Title>
        {isEdit ? 'Modifica la divisione di' : 'Dividi'} {fullName(target?.professor)}
      </Dialog.Title>
      <Dialog.Description>
        Il docente verrà trattato come più docenti distinti, ognuno con la propria disponibilità e i propri
        laureandi. Ogni laureando deve essere assegnato a una delle parti.
      </Dialog.Description>
    </Dialog.Header>

    <section class="space-y-2">
      <h3 class="text-sm font-medium">Parti</h3>
      {#each parts as part, i (i)}
        <div class="flex items-center gap-2" data-testid="split-part">
          <span class="w-16 text-sm font-medium shrink-0">Parte {i + 1}</span>
          <div class="w-48 shrink-0">
            <ProfessorAvailabilitySelector bind:value={part.when}/>
          </div>
          <Input class="h-8" placeholder="Nota (facoltativa)" bind:value={part.note} maxlength={256}/>
          <Button variant="ghost" size="icon" class="size-8 shrink-0" disabled={parts.length <= 2}
                  onclick={() => removePart(i)} aria-label={`Rimuovi la parte ${i + 1}`}>
            <LucideTrash2/>
          </Button>
        </div>
      {/each}
      <Button variant="outline" size="sm" onclick={addPart}>
        <LucidePlus/>
        Aggiungi parte
      </Button>
    </section>

    <section class="space-y-2">
      <h3 class="text-sm font-medium">Laureandi ({entries.length})</h3>
      {#if entries.length === 0}
        <p class="text-sm text-muted-foreground">Il docente non è relatore di alcun laureando.</p>
      {/if}
      <ul class="divide-y rounded-md border">
        {#each entries as entry (entry.id)}
          <li class="flex items-center justify-between gap-4 px-3 py-1.5" data-testid="split-student">
            <div class="flex items-center gap-2 min-w-0">
              <StyledFullName fullName={entry.candidate}/>
              <span class="text-xs text-muted-foreground">{getDegreeLevelString(entry)}</span>
            </div>
            <div class="flex gap-1 shrink-0" role="radiogroup" aria-label={`Parte di ${fullName(entry.candidate)}`}>
              {#each parts as _, i (i)}
                <Button size="sm" class="h-7 w-9"
                        variant={assignment[entry.id] === i ? 'default' : 'outline'}
                        role="radio" aria-checked={assignment[entry.id] === i}
                        onclick={() => assignment[entry.id] = i}>
                  {i + 1}
                </Button>
              {/each}
            </div>
          </li>
        {/each}
      </ul>
    </section>

    {#if substituteConflict}
      <div class="flex gap-2 rounded-md border border-destructive/50 p-3 text-sm" role="alert">
        <LucideTriangleAlert class="size-4 text-destructive shrink-0 mt-0.5"/>
        <div>
          Il docente (o una delle sue parti) ha un sostituto. Proseguendo, i sostituti verranno rimossi e i loro
          laureandi assegnati alle nuove parti.
        </div>
      </div>
    {/if}

    <Dialog.Footer class="items-center gap-2">
      <p class="text-sm text-muted-foreground me-auto">
        {#if unassigned > 0}
          {unassigned === 1 ? '1 laureando non è assegnato' : `${unassigned} laureandi non sono assegnati`} a una parte.
        {:else if emptyParts.length > 0}
          Ogni parte deve avere almeno un laureando (vuota: {emptyParts.map(i => `Parte ${i + 1}`).join(', ')}).
        {/if}
      </p>
      <Button variant="outline" onclick={onClose} disabled={saving}>Annulla</Button>
      {#if substituteConflict}
        <Button variant="destructive" disabled={!valid || saving} onclick={() => save(true)}>
          {#if saving}<LucideLoaderCircle class="animate-spin"/>{/if}
          Rimuovi i sostituti e salva
        </Button>
      {:else}
        <Button disabled={!valid || saving} onclick={() => save()}>
          {#if saving}<LucideLoaderCircle class="animate-spin"/>{/if}
          Salva
        </Button>
      {/if}
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
