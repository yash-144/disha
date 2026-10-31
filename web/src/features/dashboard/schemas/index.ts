import { z } from 'zod';

export const DashboardSchema = z.object({
  id: z.string(),
});
