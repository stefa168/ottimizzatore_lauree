import type {Commission} from "./commission_types";
import {redirect} from "@sveltejs/kit";

export async function load({params}) {
    throw redirect(302, '/commission/' + params.id + '/info');
}