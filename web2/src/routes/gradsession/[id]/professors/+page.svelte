<script lang="ts">
  import type {PageProps} from "./$types";
  import {computeProfessorsBurdens} from "@/utils";
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";

  let {data}: PageProps = $props();

  $inspect(data.professorsBurdens);
</script>

<DataTable data={data.professors} columns={columns(data.professorsBurdens)}/>