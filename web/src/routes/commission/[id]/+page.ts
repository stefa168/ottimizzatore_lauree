import type {Commission} from "./commission_types";

const delay = function (ms: number) {
    return new Promise(res => setTimeout(res, ms));
};

export async function load({fetch, params}) {
    let commission: Commission = await fetch(`http://localhost:5000/commission/${params.id}`)
        .then(response => response.json())

    await delay(3000);

    return {
        commissionId: params.id,
        commissionData: commission
    }
}