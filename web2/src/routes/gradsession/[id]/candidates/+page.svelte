<script lang="ts">
  import DataTable from "@/components/data-table.svelte";

  import type {PageProps} from "./$types";
  import {columns} from "./columns";

  let {data}: PageProps = $props();
</script>

<DataTable data={data.student_entries} columns={columns(data.professorsMap)}/>