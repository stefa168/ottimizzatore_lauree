<script lang="ts">
    import * as Card from "$lib/components/ui/card";
    import * as HoverCard from "$lib/components/ui/hover-card";

    import type {SolutionCommission} from "../optimization_types";
    import type {Commission} from "../../commission_types";
    import {formatTime} from "$lib/utils";

    export let problem: Commission | undefined;
    export let commission: SolutionCommission;

    $: commissionDetails = () => {
        const students = commission.students
            .map(student => student.id)
            // Get only the students of this commission
            .map(id => problem?.entries.find(student => student.id === id))
            .filter(s => s !== undefined);

        const bachelor = students.filter(student => student?.degree_level === "bachelors").length;
        const masters = students.filter(student => student?.degree_level === "masters").length;

        let result = "";

        if (bachelor > 0)
            result += `${bachelor}T`;

        if (masters > 0)
            if (result.length > 0)
                result += `, ${masters}M`;
            else
                result += `${masters}M`;

        return result;
    };
</script>

<Card.Root class="w-fit">
    <Card.Header class="pb-1.5">
        <Card.Title>Commissione {commission.order + 1}</Card.Title>
        <Card.Description>
            <p>{commission.students.length} Candidati (<abbr><strong>{commissionDetails()}</strong></abbr>)</p>
            <p>Durata: {formatTime(commission.duration)}</p>
        </Card.Description>
    </Card.Header>
    <Card.Content>
        <ul class="list-inside list-disc">
            {#each commission.professors as professor}
                <li class="{professor.role === 'ordinary' ? 'underline' : ''}">
                    {professor.surname} {professor.name[0]}.
                </li>
            {/each}
        </ul>
    </Card.Content>
</Card.Root>