import {z} from "zod";

export const commissionFormSchema = z.object({
    title: z
        .string()
        .min(3, {message: "Il titolo della commissione deve essere lungo almeno 3 caratteri"})
        .max(256, {message: "Il titolo della commissione deve essere lungo almeno 256 caratteri"}),
    excel: z
        .instanceof(File, {message: "E' necessario indicare il file della commissione."})
        .refine((f) => f.name.includes('xls') || f.name.includes('xlsx'), "Il file della commissione deve essere in formato xls o xlsx")
        .nullable()
});