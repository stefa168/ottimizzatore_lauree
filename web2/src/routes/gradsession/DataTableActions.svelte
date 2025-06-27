<script lang="ts">
  import {EllipsisIcon} from "@lucide/svelte";
  import {Button} from "@/components/ui/button";
  import * as DropdownMenu from "@/components/ui/dropdown-menu";
  import {goto} from "$app/navigation";
  import ButtonGroup from "@/components/ButtonGroup.svelte";

  let {id}: { id: number; } = $props();
</script>

<ButtonGroup>
  <Button
    variant="ghost"
    style="height: calc(var(--spacing) * 8)"
    href={`/gradsession/${id}`}
  >
    Visualizza
  </Button>
  <DropdownMenu.Root>
    <DropdownMenu.Trigger>
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
        <DropdownMenu.Item>Elimina</DropdownMenu.Item>
      </DropdownMenu.Group>
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</ButtonGroup>