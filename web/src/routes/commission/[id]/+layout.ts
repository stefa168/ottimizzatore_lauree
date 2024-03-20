import type {Commission} from "./commission_types";
import {selectedProblem} from "$lib/store";

export async function load({fetch, params}) {
    console.log("1", params.id);

    let commission: Commission = await fetch(`http://localhost:5000/commission/${params.id}`)
        .then(response => response.json());

    selectedProblem.update((p) => {
        if(p === undefined)
            return commission;
        else
            return p;
    })

    return {
        'commission': commission,
    }
}