<script lang="ts">
  import {Badge} from "@/components/ui/badge";
  import LucideSnowflake from '~icons/lucide/snowflake'
  import LucideCircleCheck from '~icons/lucide/circle-check'

  let {title, frozen, used = false}: { title: string, frozen: boolean, used?: boolean } = $props();
</script>

<span class="flex items-center gap-2">
  {title}
  {#if used}
    <Badge title="Soluzione utilizzata per la sessione"><LucideCircleCheck class="size-3"/> Utilizzata</Badge>
  {:else if frozen}
    <Badge variant="secondary" title="Soluzione finale"><LucideSnowflake class="size-3"/> Congelata</Badge>
  {/if}
</span>
