<script lang="ts">
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";
  import {columns} from "./columns";

  let sessionData = getSessionData();
</script>

<DataTable data={sessionData.student_entries} columns={columns(sessionData.sessionProfessorsMap)}/>