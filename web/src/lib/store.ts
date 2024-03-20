import {writable, readonly, type Writable} from "svelte/store";
import type {Commission} from "../routes/commission/[id]/commission_types";

export const isLoading = writable(false);
export const loaded = writable(false);
export const selectedProblem: Writable<Commission | undefined> = writable(undefined);

export const fetch_problem = async (id: number) => {
    isLoading.set(true);
    await fetch(`http://localhost:5000/commission/${id}`)
        .then((res) => res.json())
        .then((data: Commission) => {
            selectedProblem.set(data);
        })
        .catch((err) => console.error(err))
        .finally(() => isLoading.set(false))
        .finally(() => loaded.set(true));
}

export const deleteCommission = async (comm: Commission | CommissionPreview) => {
    // todo return true if the deleted commission was the one currently selected to signal the router to close viewer
    return fetch(`http://localhost:5000/commission/${comm.id}`, {
        method: 'DELETE'
    }).then(() => {
        commissionsPreview.update((data) => {
            return data.filter((c) => c.id !== comm.id);
        });
    });
}

/* Commission Problems Preview */
export type CommissionPreview = {
    id: number;
    title: string;
}

export const commissionsPreview: Writable<CommissionPreview[]> = writable([]);
export const commissionsPreviewLoaded = writable(false);
export const commissionPreviewsLoading = writable(false);

export const fetchCommissionPreviews = async () => {
    commissionPreviewsLoading.set(true);
    await fetch("http://localhost:5000/commission")
        .then((res) => res.json())
        .then((data: CommissionPreview[]) => {
            commissionsPreview.set(data);
        })
        .then(() => commissionsPreviewLoaded.set(true))
        .then(() => commissionPreviewsLoading.set(false))
        .catch((err) => console.error(err));
}

export const handleUploadSuccess = (newCommission: CommissionPreview) => {
    console.log(newCommission);
    commissionsPreview.update((data) => {
        return [...data, newCommission];
    })
}
