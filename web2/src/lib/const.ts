import {types as mime_types} from "mime-types";
import type {ValueLabelStructure} from "@/types";

export const EXCEL_MIME_TYPES = ['xls', 'xlsx', 'ods'].map(x => mime_types[x])
export const EXCEL_MIME_STRING = EXCEL_MIME_TYPES.reduce((prev, cur) => prev.concat(", ", cur));
export const PUBLIC_BACKEND_URL = "http://127.0.0.1:8000/api/v1";

export const UniversityRoles = new Map<string, ValueLabelStructure>([
  ["ordinary", {value: 'ordinary', label: 'Professore Ordinario'}],
  ["associate", {value: 'associate', label: 'Professore Associato'}],
  ["researcher", {value: 'researcher', label: 'Ricercatore'}],
  // Disabled to avoid users removing a role from a Professor
  ["unspecified", {value: 'unspecified', label: 'Non Specificato', disabled: true}]
]);

export const AvailabilityOptions = new Map<string, ValueLabelStructure>([
  ["always", {value: 'always', label: 'Tutto il giorno'}],
  ["morning", {value: 'morning', label: 'Solo la Mattina'}],
  ["afternoon", {value: 'afternoon', label: 'Solo il Pomeriggio'}],
  ["split", {value: 'split', label: 'Sdoppia il docente'}],
]);