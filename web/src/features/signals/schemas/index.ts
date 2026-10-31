import { z } from 'zod';

export const SignalsSchema = z.object({
  id: z.string(),
});
