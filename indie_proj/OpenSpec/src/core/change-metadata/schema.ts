import { z } from 'zod';

const KebabIdentifierSchema = (label: string): z.ZodString =>
  z.string().superRefine((value, ctx) => {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(value)) {
      ctx.addIssue({
        code: 'custom',
        message: `${label} must be kebab-case with lowercase letters, numbers, and single hyphen separators`,
      });
    }
  });

export const InitiativeLinkSchema = z.object({
  store: KebabIdentifierSchema('Context store id'),
  id: KebabIdentifierSchema('Initiative id'),
}).strict();

export type InitiativeLink = z.infer<typeof InitiativeLinkSchema>;

// Per-change metadata schema. The schema field is validated against available
// workflow schemas when metadata is read or written.
export const ChangeMetadataSchema = z.object({
  schema: z.string().min(1, { message: 'schema is required' }),
  created: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'created must be YYYY-MM-DD format',
    })
    .optional(),
  goal: z.string().min(1).optional(),
  affected_areas: z.array(z.string().min(1)).optional(),
  initiative: InitiativeLinkSchema.optional(),
  redmine: z
    .object({
      instance: z.string().optional(),
      issueId: z.union([z.number(), z.string()]).optional(),
      versionId: z.number().optional(),
      syncStatus: z.enum(['pending', 'synced', 'failed', 'outdated']).optional(),
      lastSync: z.string().optional(),
      lastSyncBy: z.string().optional(),
      tasks: z
        .array(
          z.object({
            name: z.string(),
            issueId: z.number().optional(),
            status: z.string(),
            order: z.number(),
          })
        )
        .optional(),
    })
    .optional(),
});

export type ChangeMetadata = z.infer<typeof ChangeMetadataSchema>;
