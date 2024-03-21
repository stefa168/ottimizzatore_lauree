import {selectedConfiguration, selectedProblem} from "$lib/store";
import {error} from "@sveltejs/kit";
import {get} from "svelte/store";

export async function load({params, parent}) {
    // Absolutely necessary! Race condition with selectedProblem being undefined and set too late
    await parent();
    const opt_id = Number(params.opt_id);

    // try to get the configuration from selectedProblem
    const problem = get(selectedProblem);
    if (problem === undefined) {
        throw error(500, "No problem selected");
    }

    const configuration = problem.optimization_configurations.find((c) => c.id === opt_id);
    if (configuration === undefined) {
        throw error(404, "Configuration not found");
    }

    selectedConfiguration.set(configuration);
}