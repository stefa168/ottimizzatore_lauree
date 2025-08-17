import {z} from "zod";
import {EXCEL_MIME_TYPES} from "@/const";

export const commissionFormSchema = z.object({
  title: z
    .string()
    .min(3, {message: "Il titolo della sessione deve essere avere almeno 3 caratteri"})
    .max(256, {message: "Il titolo della sessione può avere al massimo 256 caratteri"}),
  excel: z
    .instanceof(File, {message: "E' necessario allegare il file della sessione."})
    .refine((file) => {
      return EXCEL_MIME_TYPES.includes(file.type)
    }, "Il file della sessione deve essere in formato xls, xlsx o ods")
    .nullable(),
  only: z.enum(['bachelors', 'masters', 'both']).default('both').optional()
});

export type CommissionFormData = z.infer<typeof commissionFormSchema>;

export interface UploadErrorDetails {
  error: string;
  details?: string;
  missing_columns?: string[];
}