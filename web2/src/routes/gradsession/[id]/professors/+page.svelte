<script lang="ts">
  import {columns} from "./columns";
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";

  let sessionData = getSessionData();
</script>

<DataTable data={sessionData.professors} columns={columns(sessionData)}/>