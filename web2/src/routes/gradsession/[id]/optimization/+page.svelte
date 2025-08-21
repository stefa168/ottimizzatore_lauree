<script lang="ts">
  import type {PageProps} from './$types';
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";

  let {data}: PageProps = $props();
</script>

<DataTable data={data.configurations} columns={columns(data.session_id)}/>