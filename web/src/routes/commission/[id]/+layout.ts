import type {Commission} from "./commission_types";

export async function load({fetch, params}) {
    let commission: Commission = await fetch(`http://localhost:5000/commission/${params.id}`)
        .then(response => response.json())

    return {
        commissionId: params.id,
        commissionData: commission
    }
}