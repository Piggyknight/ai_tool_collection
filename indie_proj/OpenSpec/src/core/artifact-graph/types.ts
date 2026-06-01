import { z } from 'zod';

// Artifact definition schema
export const ArtifactSchema = z.object({
  id: z.string().min(1, { error: 'Artifact ID is required' }),
  generates: z.string().min(1, { error: 'generates field is required' }),
  description: z.string(),
  template: z.string().min(1, { error: 'template field is required' }),
  instruction: z.string().optional(),
  requires: z.array(z.string()).default([]),
});

// Apply phase configuration for schema-aware apply instructions
export const ApplyPhaseSchema = z.object({
  // Artifact IDs that must exist before apply is available
  requires: z.array(z.string()).min(1, { error: 'At least one required artifact' }),
  // Path to file with checkboxes for progress (relative to change dir), or null if no tracking
  tracks: z.string().nullable().optional(),
  // Custom guidance for the apply phase
  instruction: z.string().optional(),
});

// Full schema YAML structure
export const SchemaYamlSchema = z.object({
  name: z.string().min(1, { error: 'Schema name is required' }),
  version: z.number().int().positive({ error: 'Version must be a positive integer' }),
  description: z.string().optional(),
  artifacts: z.array(ArtifactSchema).min(1, { error: 'At least one artifact required' }),
  // Optional apply phase configuration (for schema-aware apply instructions)
  apply: ApplyPhaseSchema.optional(),
});

// Derived TypeScript types
export type Artifact = z.infer<typeof ArtifactSchema>;
export type ApplyPhase = z.infer<typeof ApplyPhaseSchema>;
export type SchemaYaml = z.infer<typeof SchemaYamlSchema>;

// Per-change metadata used by Redmine-aware workflow helpers.
export const ChangeMetadataSchema = z.object({
  schema: z.string().min(1, { message: 'schema is required' }),
  created: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'created must be YYYY-MM-DD format',
    })
    .optional(),
  redmine: z
    .object({
      instance: z.string().optional(),
      issueId: z.number().optional(),
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

export const SprintMetadataSchema = z.object({
  name: z.string().min(1),
  created: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'created must be YYYY-MM-DD format',
    })
    .optional(),
  status: z.enum(['active', 'closed', 'archived']).default('active'),
  dueDate: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'dueDate must be YYYY-MM-DD format',
    })
    .optional(),
  redmine: z
    .object({
      instance: z.string().optional(),
      versionId: z.number().optional(),
      projectId: z.number().optional(),
    })
    .optional(),
  changes: z
    .array(
      z.object({
        name: z.string(),
        issueId: z.number().optional(),
      })
    )
    .optional(),
});

export type SprintMetadata = z.infer<typeof SprintMetadataSchema>;

export const BugMetadataSchema = z.object({
  title: z.string().min(1),
  severity: z.enum(['critical', 'major', 'minor', 'trivial']).default('major'),
  status: z.enum(['new', 'in-progress', 'fixed', 'verified']).default('new'),
  created: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'created must be YYYY-MM-DD format',
    })
    .optional(),
  resolved: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'resolved must be YYYY-MM-DD format',
    })
    .optional(),
  relatedChange: z.string().optional(),
  relatedTask: z.string().optional(),
  redmine: z
    .object({
      instance: z.string().optional(),
      issueId: z.number().optional(),
    })
    .optional(),
});

export type BugMetadata = z.infer<typeof BugMetadataSchema>;

// Runtime state types (not Zod - internal only)

// Slice 1: Simple completion tracking via filesystem
export type CompletedSet = Set<string>;

// Return type for blocked query
export interface BlockedArtifacts {
  [artifactId: string]: string[];
}
