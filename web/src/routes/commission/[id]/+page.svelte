<script lang="ts">
    import {selectedProblem} from "$lib/store.js";
</script>

<h2 class="">Informazioni sulla commissione</h2>
<ul class="list-disc ms-4">
    <li>Sessione composta da {$selectedProblem?.entries.length} studenti</li>
<!--    <li>Commissione composta da {commissionProfessors.length} docenti</li>-->
</ul>
