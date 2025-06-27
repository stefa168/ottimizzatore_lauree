import {types as mime_types} from "mime-types";

export const EXCEL_MIME_TYPES = ['xls', 'xlsx', 'ods'].map(x => mime_types[x])
export const EXCEL_MIME_STRING = EXCEL_MIME_TYPES.reduce((prev, cur) => prev.concat(", ", cur));