<script lang="ts">
  import DataTable from "@/components/data-table.svelte";
  import {getSessionData} from "../../SessionData.svelte";
  import {columns, initialTableState} from "./columns";
  import type {GradSessionEntry} from "@/types";
  import {updateStudentBonus} from "@/api/sessions.remote";
  import {toApiError} from "@/errors";
  import {fullName} from "@/utils";
  import {toast} from "svelte-sonner";

  let sessionData = getSessionData();

  // The command sends back the refreshed students, so the table updates by itself
  const onBonusChange = (entry: GradSessionEntry, minutes: number) =>
    updateStudentBonus({sid: sessionData.session.id, entryId: entry.id, minutes})
      .then(() => {
        toast.success(`Tempo bonus di ${fullName(entry.candidate)}: ${minutes} minuti.`);
      })
      .catch((e) => {
        toast.error("Si è verificato un errore durante il salvataggio del tempo bonus", {description: toApiError(e).detail});
        throw e;
      });
</script>

<DataTable
    data={sessionData.student_entries}
    columns={columns(sessionData.sessionProfessorsMap, onBonusChange)}
    initialState={initialTableState()}
/>