import { z } from 'zod';

export const AnalyticsSchema = z.object({
  id: z.string(),
});
