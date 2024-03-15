import type {Commission} from "../commission_types";
import type {OptimizationConfiguration} from "./optimization_types";

export async function load({fetch, params}) {
    let configs: OptimizationConfiguration[] = await fetch(`http://localhost:5000/commission/${params.id}/configuration`)
        .then(response => response.json())

    return {
        configurations: configs
    }
}