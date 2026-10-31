import { z } from 'zod';

export const AuthSchema = z.object({
  id: z.string(),
});
