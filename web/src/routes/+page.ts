import {superValidate} from "sveltekit-superforms";
import {zod} from "sveltekit-superforms/adapters";
import {commissionFormSchema} from "./schema";

export const load = (async () => {
    const form = await superValidate(zod(commissionFormSchema));
    return {form};
});