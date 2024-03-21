import type {Commission} from "./commission_types";
import {selectedProblem} from "$lib/store";
import {get} from "svelte/store";
import {error} from "@sveltejs/kit";

export async function load({fetch, params}) {
    // We load the problem here to avoid the need to load it in the layout.
    // This way we can ensure that the problem is loaded before the layout is rendered.
    // This simplifies the layout code a lot.
    let response = await fetch(`http://localhost:5000/commission/${params.id}`);

    if (!response.ok) {
        switch (response.status) {
            case 404: {
                throw error(404,
                    `La commissione con ID ${params.id} non esiste. 
                     Dettagli: ${await response.text()}`
                );
            }
            default: {
                // @ts-ignore
                throw error(response.status, await response.text());
            }
        }
    }

    let commission: Commission = await response.json()

    if (get(selectedProblem) === undefined)
        selectedProblem.set(commission);

    return {
        'commission': commission,
    }
}