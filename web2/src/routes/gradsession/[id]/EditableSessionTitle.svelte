<script lang="ts">
  import LucidePencil from '~icons/lucide/pencil'
  import LucideCheck from '~icons/lucide/check'
  import LucideX from '~icons/lucide/x'

  import type {SessionData} from "../SessionData.svelte";
  import {Button} from "@/components/ui/button";
  import {onDestroy, tick} from "svelte";
  import {GradSessionApi} from "@/api/GradSesssionApi";
  import {fromRawDates} from "@/api/RawTypes";
  import type {GradSession} from "@/types";

  interface Props {
    sessionData: SessionData
  }

  let {sessionData}: Props = $props();

  let editingTitle = $state(false);
  let draftTitle = $state<string>(sessionData.session.title ?? '');
  let titleInputEl: HTMLInputElement | null = $state(null);

  let showUpdated = $state(false);
  let updateHideTimer: number | null = $state(null);

  function resetHideTimer(show = false) {
    if (updateHideTimer) clearTimeout(updateHideTimer);
    showUpdated = show;
  }

  onDestroy(() => {
    resetHideTimer();
    updateHideTimer = null;
  });

  function resetInputField() {
    draftTitle = sessionData.session.title ?? '';
  }

  const startEdit = async () => {
    resetInputField();
    resetHideTimer();
    editingTitle = true;
    await tick();
    titleInputEl?.focus();
    titleInputEl?.select();
  };

  const cancelEdit = () => {
    editingTitle = false;
    resetInputField();
    resetHideTimer()
  };

  const saveTitle = async () => {
    const newTitle = draftTitle.trim();
    if (!newTitle) return;

    await GradSessionApi(fetch)
      .changeTitle(sessionData.session.id, newTitle)
      .then(fromRawDates<GradSession>)
      .then((newSessionData) => {
        // Update local data
        sessionData.session = newSessionData;
        editingTitle = false;

        showUpdated = true;
        resetHideTimer(true);
        updateHideTimer = window.setTimeout(() => {
          showUpdated = false;
        }, 2500);
      });
  };

  const onTitleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveTitle();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  };
</script>

<div class="container mx-auto">
  <div class="flex mb-4 flex-row items-center">
    {#if !editingTitle}
      <h1 class="text-2xl font-medium w-fit truncate">{sessionData.session.title}</h1>
      <Button
          type="button"
          variant="ghost"
          aria-label="Edit title"
          title="Modifica il titolo della sessione"
          onclick={startEdit}
      >
        <LucidePencil class="size-4"/>
      </Button>
      <span class={[
          "text-green-600 transform origin-left transition-transform duration-300",
          showUpdated ? 'scale-x-100 w-fit' : 'scale-x-0 w-0'
        ]}>
          Aggiornato!
        </span>
    {:else}
      <div class="flex items-center gap-2 w-full">
        <input
            bind:this={titleInputEl}
            class="flex-1 bg-transparent text-2xl font-medium border-b border-gray-300 focus:outline-none focus:border-primary dark:border-gray-700 px-1 py-0.5"
            type="text"
            aria-label="Session title"
            bind:value={draftTitle}
            onkeydown={onTitleKeyDown}
        />
        <Button
            type="button"
            variant="ghost"
            aria-label="Save title"
            title="Salva"
            onclick={saveTitle}
            class="text-green-600"
        >
          <LucideCheck class="size-4"/>
        </Button>
        <Button
            type="button"
            variant="ghost"
            aria-label="Cancel editing title"
            title="Annulla"
            onclick={cancelEdit}
            class="text-destructive"
        >
          <LucideX class="size-4"/>
        </Button>
      </div>
    {/if}
  </div>
</div>