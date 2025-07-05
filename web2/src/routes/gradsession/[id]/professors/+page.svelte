<script lang="ts">
  import {columns} from "./columns";
  import DataTable from "@/components/data-table.svelte";
  import {columns} from "./columns";
  import {getSessionData} from "../../SessionData.svelte";

  let sessionData = getSessionData();

  $inspect(data.professorsBurdens);
</script>

<DataTable data={data.professors} columns={columns(data.professorsBurdens)}/>
<DataTable data={sessionData.professors} columns={columns(sessionData)}/>