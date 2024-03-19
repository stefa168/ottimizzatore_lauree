import {writable, readonly, type Writable} from "svelte/store";
import type {Commission} from "../routes/commission/[id]/commission_types";

export const isLoading = writable(false);
export const loaded = writable(false);
export const problemsData: Writable<Commission[]> = writable([]);

export const fetch_problems = async () => {
    isLoading.set(true);
    await fetch("http://localhost:5000/commissions")
        .then((res) => res.json())
        .then((data: Commission[]) => {
            // todo extract professors to have only one instance of each
            problemsData.set(data);
        })
        .catch((err) => console.error(err))
        .finally(() => isLoading.set(false))
        .finally(() => loaded.set(true));
}

export const handleUploadSuccess = (newCommission: Commission) => {
    console.log(newCommission);
    problemsData.update((data) => {
        // todo extract professors to have only one instance of each
        return [...data, newCommission];
    })
}

export const deleteCommission = async (comm: Commission) => {
    return fetch(`http://localhost:5000/commission/${comm.id}`, {
        method: 'DELETE'
    }).then(() => {
        problemsData.update((data) => {
            return data.filter((c) => c.id !== comm.id);
        });
    });
}