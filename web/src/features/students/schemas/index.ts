import { z } from 'zod';

export const StudentsSchema = z.object({
  id: z.string(),
});
