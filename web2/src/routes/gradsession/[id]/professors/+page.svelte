<script lang="ts">
  import {columns, initialTableState} from "./columns";
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";

  let sessionData = getSessionData();

  let initialState = $state(initialTableState());
</script>

<DataTable
    data={sessionData.professors}
    columns={columns(sessionData)}
    {initialState}
/>