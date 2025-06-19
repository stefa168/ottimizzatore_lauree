<script lang="ts">
    import type {PageProps} from "./$types";

    import {LucideSearch, LucideListFilter} from "@lucide/svelte";

    /* Shadcn components */
    import {Input} from '$lib/components/ui/input';
    import {Button, buttonVariants} from '$lib/components/ui/button';
    import {Badge} from '@/components/ui/badge';
    import * as Tabs from '@/components/ui/tabs';
    import * as Table from '@/components/ui/table';
    import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
    import * as Card from '$lib/components/ui/card';
    import {useQueryClient} from "@tanstack/svelte-query";
    import {GradSessionApiQueries} from "@/api/GradSesssionApi";

    let {data}: PageProps = $props();
    let searchText = $state('');

    const queryClient = useQueryClient();
    const gsApiQueries = GradSessionApiQueries(queryClient);

    const gsQuery = gsApiQueries.allSessionsQuery();

    let sessions = $derived($gsQuery.isSuccess ? $gsQuery.data : []);

    const dateFormatter = new Intl.DateTimeFormat('it-IT', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    function formatDate(dateString: string) {
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Invalid date';
            }
            return dateFormatter.format(date);
        } catch (error) {
            return 'Invalid date';
        }
    }


</script>


<Card.Root>
    <Card.Header class="flex flex-col pb-0">
        <div class="flex flex-row justify-between">
            <!-- Title and search row -->
            <div>
                <Card.Title>Remote Terminal Units</Card.Title>
                <Card.Description>
                    In this section you can manage the RTUs that are handled by the server.
                </Card.Description>
            </div>
        </div>
    </Card.Header>
    <Card.Content>
        {#if $gsQuery.isPending}
            Caricando le sessioni attive...
        {/if}

        {#if $gsQuery.isError}
            Errore: {JSON.stringify($gsQuery.error)}
        {/if}

        {#if $gsQuery.isSuccess}
            <ul class="list-disc list-inside">
                {#each sessions as s}
                    <li>{s.title} Creata il {dateFormatter.format(s.created_at)}</li>
                {/each}
            </ul>
        {/if}
    </Card.Content>
</Card.Root>