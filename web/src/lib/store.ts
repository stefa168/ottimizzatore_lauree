import {writable, readonly, type Writable} from "svelte/store";
import type {Commission} from "../routes/commission/[id]/commission_types";
import type {OptimizationConfiguration} from "../routes/commission/[id]/optimization/optimization_types";
import {persisted} from "svelte-persisted-store";

export const selectedProblem: Writable<Commission | undefined> = writable(undefined);
export const selectedConfiguration: Writable<OptimizationConfiguration | undefined> = writable(undefined);

export const debugEnabled = persisted("debugEnabled", false);

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

export const handleUploadSuccess = (newCommission: CommissionPreview) => {
    console.log(newCommission);
    commissionsPreview.update((data) => {
        return [...data, newCommission];
    })
}
