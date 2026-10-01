<script lang="ts">
  import type {SessionProfessor} from "@/types";
  import StyledFullName from "@/components/StyledFullName.svelte";
  import {Badge} from "@/components/ui/badge";
  import {LucideChevronDown, LucideChevronRight, LucideCornerDownRight} from "@lucide/svelte";

  interface Props {
    sp: SessionProfessor;
    depth: number;
    // Position of a split among its siblings (1-based), used to label it
    partNumber?: number;
    children?: SessionProfessor[];
    canExpand?: boolean;
    expanded?: boolean;
    toggle?: () => void;
  }

  let {sp, depth, partNumber, children = [], canExpand = false, expanded = false, toggle}: Props = $props();

  const splits = $derived(children.filter(c => c.relation === 'SPLIT'));
  const substitute = $derived(children.find(c => c.relation === 'SUBSTITUTE'));
</script>

<div class="flex items-center gap-1" style={`padding-left: ${depth * 1.25}rem`}>
  {#if canExpand}
    <button class="text-muted-foreground hover:text-foreground hover:cursor-pointer -ms-1"
            onclick={toggle}
            aria-label={expanded ? "Nascondi dettagli" : "Mostra dettagli"}
            aria-expanded={expanded}>
      {#if expanded}
        <LucideChevronDown class="size-4"/>
      {:else}
        <LucideChevronRight class="size-4"/>
      {/if}
    </button>
  {:else if depth > 0}
    <LucideCornerDownRight class="size-4 text-muted-foreground shrink-0"/>
  {:else}
    <span class="w-3"></span>
  {/if}

  {#if sp.relation === 'SPLIT'}
    <span class="font-medium">Parte {partNumber ?? ''}</span>
  {:else if sp.relation === 'SUBSTITUTE'}
    <span class="text-muted-foreground text-xs me-1">Sostituto:</span>
    <StyledFullName fullName={sp.professor} show="surname"/>
  {:else}
    <StyledFullName fullName={sp.professor} show="surname"/>
  {/if}

  {#if splits.length > 0}
    <Badge variant="secondary" class="ms-2">Diviso in {splits.length}</Badge>
  {:else if substitute}
    <Badge variant="outline" class="ms-2">Sostituito</Badge>
  {/if}
</div>
