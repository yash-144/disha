import { z } from 'zod';

export const InterventionsSchema = z.object({
  id: z.string(),
});
