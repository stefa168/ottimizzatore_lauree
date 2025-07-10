<script>
  import LucideLightbulb from '~icons/lucide/lightbulb'
  import * as Tooltip from "@/components/ui/tooltip";

</script>

<Tooltip.Provider delayDuration={100}>
  <Tooltip.Root>
    <Tooltip.Trigger>
      <LucideLightbulb/>
    </Tooltip.Trigger>
    <Tooltip.Content side="left">
      <p>
        Suggerimento: tenendo premuto
        <code class="text-muted-foreground bg-muted relative rounded px-[0.3rem] py-[0.2rem] font-mono font-semibold">
          SHIFT
        </code>
        è possibile ordinare più colonne contemporaneamente.
      </p>
    </Tooltip.Content>
  </Tooltip.Root>
</Tooltip.Provider>