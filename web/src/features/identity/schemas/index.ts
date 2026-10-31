import { z } from 'zod';

export const IdentitySchema = z.object({
  id: z.string(),
});
