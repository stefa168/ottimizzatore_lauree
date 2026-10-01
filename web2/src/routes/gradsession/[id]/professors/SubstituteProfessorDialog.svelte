<script lang="ts">
  // noinspection ES6UnusedImports
  import * as Dialog from "@/components/ui/dialog";
  import {Button} from "@/components/ui/button";
  import {Input} from "@/components/ui/input";
  import StyledFullName from "@/components/StyledFullName.svelte";
  import ProfessorAvailabilitySelector from "./ProfessorAvailabilitySelector.svelte";
  import type {SessionData} from "../../SessionData.svelte";
  import type {ApiErrorResponse, Professor, ProfessorAvailability, SessionProfessor} from "@/types";
  import {GradSessionApi} from "@/api/GradSesssionApi";
  import {ProfessorsApi} from "@/api/ProfessorsApi";
  import {fromRawList} from "@/api/RawTypes";
  import {fullName} from "@/utils";
  import {UniversityRoles} from "@/const";
  import {toast} from "svelte-sonner";
  import {untrack} from "svelte";
  import {LucideLoaderCircle, LucideSearch} from "@lucide/svelte";

  interface Props {
    sd: SessionData;
    // ORIGINAL or SPLIT to substitute, or an existing SUBSTITUTE to change; the dialog is open while it's set
    target: SessionProfessor | null;
    onClose: () => void;
  }

  let {sd, target, onClose}: Props = $props();

  let professors = $state<Professor[]>([]);
  let loading = $state(false);
  let search = $state("");
  let selected = $state<Professor | null>(null);
  let availability = $state<ProfessorAvailability>('always');
  let note = $state("");
  let saving = $state(false);

  const isChange = $derived(target?.relation === 'SUBSTITUTE');
  // The professor whose students are being reassigned (for a split, the original professor)
  const substituted = $derived.by(() => {
    if (!target) return undefined;
    let root = target;
    while (root.derived_from_id !== null) {
      const parent = sd.sessionProfessorsMap.get(root.derived_from_id);
      if (!parent) break;
      root = parent;
    }
    return root;
  });

  const load = async (t: SessionProfessor) => {
    search = "";
    selected = null;
    note = "";
    availability = t.availability;
    loading = true;
    try {
      professors = fromRawList<Professor>(await ProfessorsApi().getAll());
    } catch (err) {
      console.error(err);
      toast.error("Impossibile caricare l'elenco dei docenti", {description: (err as ApiErrorResponse)?.detail});
    } finally {
      loading = false;
    }
  };

  $effect(() => {
    const t = target;
    if (t) untrack(() => load(t));
  });

  const candidates = $derived.by(() => {
    const excluded = new Set([substituted?.professor.id, target?.professor.id]);
    const q = search.trim().toLowerCase();
    return professors
      .filter(p => !excluded.has(p.id))
      .filter(p => q === "" || fullName(p).toLowerCase().includes(q) || fullName(p, false).toLowerCase().includes(q));
  });

  const save = async () => {
    if (!target || !selected) return;
    saving = true;
    try {
      await GradSessionApi().substituteSessionProfessor(sd.session.id, target.id, selected.id, {
        availability,
        note: note.trim()
      });
      await sd.refresh();
      toast.success(isChange ? "Sostituto aggiornato." : "Sostituto assegnato correttamente.");
      onClose();
    } catch (err) {
      console.error(err);
      toast.error("Si è verificato un errore durante l'assegnazione del sostituto", {
        duration: Number.POSITIVE_INFINITY,
        description: (err as ApiErrorResponse)?.detail ?? JSON.stringify(err)
      });
    } finally {
      saving = false;
    }
  };
</script>

<Dialog.Root open={target !== null} onOpenChange={(open) => { if (!open) onClose(); }}>
  <Dialog.Content class="sm:max-w-xl max-h-[90vh] overflow-y-auto">
    <Dialog.Header>
      <Dialog.Title>
        {#if isChange}
          Cambia il sostituto di {fullName(substituted?.professor)}
        {:else}
          Sostituisci {fullName(substituted?.professor)}{target?.relation === 'SPLIT' ? ' (una parte)' : ''}
        {/if}
      </Dialog.Title>
      <Dialog.Description>
        Il docente scelto diventerà relatore dei laureandi
        {target?.relation === 'SPLIT' ? 'di questa parte' : 'del docente sostituito'}.
        Le controrelazioni restano assegnate al docente originale.
      </Dialog.Description>
    </Dialog.Header>

    <div class="relative">
      <Input placeholder="Cerca un docente..." class="h-8 pl-7" bind:value={search}/>
      <LucideSearch class="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 opacity-50"/>
    </div>

    <ul class="h-64 overflow-y-auto divide-y rounded-md border" role="listbox" aria-label="Docenti">
      {#if loading}
        <li class="flex items-center gap-2 p-3 text-sm text-muted-foreground">
          <LucideLoaderCircle class="size-4 animate-spin"/> Caricamento...
        </li>
      {:else}
        {#each candidates as prof (prof.id)}
          <li role="option" aria-selected={selected?.id === prof.id}>
            <button class={["flex w-full items-center justify-between px-3 py-1.5 text-left hover:bg-accent hover:cursor-pointer",
                            selected?.id === prof.id && "bg-primary/10"]}
                    onclick={() => selected = prof}>
              <StyledFullName fullName={prof}/>
              <span class="text-xs text-muted-foreground">{UniversityRoles.get(prof.role)?.label}</span>
            </button>
          </li>
        {:else}
          <li class="p-3 text-sm text-muted-foreground">Nessun docente trovato.</li>
        {/each}
      {/if}
    </ul>

    {#if !isChange}
      <div class="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-2 text-sm">
        <span class="font-medium">Disponibilità</span>
        <div class="w-48">
          <ProfessorAvailabilitySelector bind:value={availability}/>
        </div>
        <span class="font-medium">Nota</span>
        <Input class="h-8" placeholder="Nota (facoltativa)" bind:value={note} maxlength={256}/>
      </div>
    {/if}

    <Dialog.Footer class="items-center gap-2">
      <p class="text-sm text-muted-foreground me-auto">
        {#if selected}
          Selezionato: <span class="font-medium text-foreground">{fullName(selected)}</span>
        {:else}
          Seleziona un docente dall'elenco.
        {/if}
      </p>
      <Button variant="outline" onclick={onClose} disabled={saving}>Annulla</Button>
      <Button disabled={!selected || saving} onclick={save}>
        {#if saving}<LucideLoaderCircle class="animate-spin"/>{/if}
        {isChange ? 'Cambia sostituto' : 'Sostituisci'}
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
