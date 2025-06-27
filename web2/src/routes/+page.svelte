<script lang="ts">
  import MdiRobotConfusedOutline from '~icons/mdi/robot-confused-outline'
  import {Button} from "@/components/ui/button";
</script>

<div class="flex flex-col items-center justify-center h-full">
  <MdiRobotConfusedOutline class="w-16 h-16"/>
  <div class="mt-4 text-center text-lg font-medium text-gray-600 dark:text-gray-400">
    <p>Non hai aperto alcuna Sessione di Laurea.</p>
    <p>Puoi
      <Button variant="outline" href="/gradsession">Aprirne</Button>
      una esistente, o
      <Button variant="outline" href="gradsession/new">Crearne</Button>
      una nuova.
    </p>
  </div>
</div>