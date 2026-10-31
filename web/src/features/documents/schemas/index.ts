import { z } from 'zod';

export const DocumentsSchema = z.object({
  id: z.string(),
});
