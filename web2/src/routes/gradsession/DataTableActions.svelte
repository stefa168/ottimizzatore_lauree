<script lang="ts">
  import {EllipsisIcon} from "@lucide/svelte";
  import {Button} from "@/components/ui/button";
  // noinspection ES6UnusedImports
  import * as DropdownMenu from "@/components/ui/dropdown-menu";
  import {goto, invalidate, invalidateAll} from "$app/navigation";
  import ButtonGroup from "@/components/ButtonGroup.svelte";
  import {useQueryClient} from "@tanstack/svelte-query";
  import {GradSessionApi, GradSessionApiQueries} from "@/api/GradSesssionApi";

  import LucideLoaderCircle from '~icons/lucide/loader-circle'
  import {toast} from "svelte-sonner";

  let {id}: { id: number; } = $props();

  const queryClient = useQueryClient();
  const gradSessionApiQueries = GradSessionApiQueries(queryClient);
  const deleteSessionMutation = gradSessionApiQueries.deleteSessionMutation()

  const isDeleting = $derived($deleteSessionMutation.isPending)

  const deleteSession = async () => {
    await GradSessionApi().delete(id)
      .then(() => invalidate((url) => url.href.includes("sessions")))
      .then(() => toast.success("La sessione è stata eliminata con successo."))
      .catch((e) => toast.error("Si è verificato un errore durante la cancellazione della sessione", e));
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
          <DropdownMenu.Item>Archivia</DropdownMenu.Item>
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