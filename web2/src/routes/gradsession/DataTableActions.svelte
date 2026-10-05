<script lang="ts">
  import {EllipsisIcon} from "@lucide/svelte";
  import {Button} from "@/components/ui/button";
  // noinspection ES6UnusedImports
  import * as DropdownMenu from "@/components/ui/dropdown-menu";
  import ButtonGroup from "@/components/ButtonGroup.svelte";
  import {deleteSession as deleteSessionCommand, setSessionArchived} from "@/api/sessions.remote";
  import {toApiError} from "@/errors";

  import LucideLoaderCircle from '~icons/lucide/loader-circle'
  import {toast} from "svelte-sonner";

  let {id, archived = false}: { id: number; archived?: boolean } = $props();

  let isDeleting = $state(false);

  // The command also refreshes the list of sessions, so the row moves to the other list
  const toggleArchived = async () => {
    await setSessionArchived({sid: id, archived: !archived})
      .then(() => toast.success(archived ? "La sessione è stata ripristinata tra le sessioni attive." : "La sessione è stata archiviata."))
      .catch((e) => toast.error("Si è verificato un errore durante l'archiviazione della sessione", {
        description: toApiError(e).detail
      }));
  }

  // The command also refreshes the list of sessions
  const deleteSession = async () => {
    isDeleting = true;
    await deleteSessionCommand(id)
      .then(() => toast.success("La sessione è stata eliminata con successo."))
      .catch((e) => toast.error("Si è verificato un errore durante la cancellazione della sessione", {
        description: toApiError(e).detail
      }))
      .finally(() => isDeleting = false);
  }
</script>

{#if !isDeleting}
  <ButtonGroup>
    <Button
        variant="ghost"
        style="height: calc(var(--spacing) * 8)"
        href={`/gradsession/${id}`}
        disabled={isDeleting}
    >
      Visualizza
    </Button>
    <DropdownMenu.Root>
      <DropdownMenu.Trigger disabled={isDeleting}>
        {#snippet child({props})}
          <Button
              {...props}
              variant="ghost"
              size="icon"
              class="relative size-8 p-0"
          >
            <span class="sr-only">Apri menu azioni</span>
            <EllipsisIcon/>
          </Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content>
        <DropdownMenu.Group>
          <DropdownMenu.Label>Azioni</DropdownMenu.Label>
          <DropdownMenu.Item onclick={toggleArchived}>{archived ? "Ripristina" : "Archivia"}</DropdownMenu.Item>
          <DropdownMenu.Separator/>
          <DropdownMenu.Item
              onclick={deleteSession}
              disabled={isDeleting}
              class="text-destructive"
          >
            Elimina
          </DropdownMenu.Item>
        </DropdownMenu.Group>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </ButtonGroup>
{:else}
  <Button
      variant="ghost"
      style="height: calc(var(--spacing) * 8)"
      disabled={isDeleting}
  >
    Cancellando...
    <LucideLoaderCircle class="animate-spin"/>
  </Button>
{/if}