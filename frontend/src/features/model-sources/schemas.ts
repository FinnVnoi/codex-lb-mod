import { z } from "zod";

export const ModelSourceModelSchema = z.object({
  id: z.number(),
  sourceId: z.string(),
  model: z.string(),
  upstreamModel: z.string().nullable().optional().default(null),
  displayName: z.string().nullable().default(null),
  contextWindow: z.number().int().positive().nullable().default(null),
  maxOutputTokens: z.number().int().positive().nullable().default(null),
  supportsStreaming: z.boolean().default(true),
  supportsTools: z.boolean().default(false),
  supportsVision: z.boolean().default(false),
  inputPer1M: z.number().nullable().default(null),
  cachedInputPer1M: z.number().nullable().default(null),
  outputPer1M: z.number().nullable().default(null),
  audioPerMinute: z.number().nullable().default(null),
  rawMetadataJson: z.string().nullable().default(null),
  isEnabled: z.boolean().default(true),
  createdAt: z.iso.datetime({ offset: true }),
  updatedAt: z.iso.datetime({ offset: true }),
});

export const ModelSourceSchema = z.object({
  id: z.string(),
  name: z.string(),
  kind: z.string(),
  baseUrl: z.string(),
  isEnabled: z.boolean(),
  healthStatus: z.string(),
  pausedAt: z.string().nullable().optional().default(null),
  pauseReason: z.string().nullable().optional().default(null),
  consecutiveAutoPauseFailures: z.number().int().min(0).optional().default(0),
  supportsChatCompletions: z.boolean(),
  supportsResponses: z.boolean(),
  supportsAudioTranscriptions: z.boolean().default(false),
  supportsEmbeddings: z.boolean().default(false),
  estimateMissingStreamUsage: z.boolean().default(true),
  timeoutSeconds: z.number().int().positive().nullable().default(null),
  maxConcurrency: z.number().int().positive().nullable().default(null),
  routingPolicy: z.enum(["normal", "burn_first", "preserve", "fallback_only"]).default("normal"),
  createdAt: z.iso.datetime({ offset: true }),
  updatedAt: z.iso.datetime({ offset: true }),
  models: z.array(ModelSourceModelSchema).default([]),
});

export const ModelSourcesResponseSchema = z.object({
  sources: z.array(ModelSourceSchema).default([]),
});

export const ModelSourceModelInputSchema = z.object({
  model: z.string().min(1).max(255),
  upstreamModel: z.string().max(255).nullable().optional(),
  displayName: z.string().max(255).nullable().optional(),
  contextWindow: z.number().int().positive().nullable().optional(),
  maxOutputTokens: z.number().int().positive().nullable().optional(),
  supportsStreaming: z.boolean().optional(),
  supportsTools: z.boolean().optional(),
  supportsVision: z.boolean().optional(),
  inputPer1M: z.number().nonnegative().nullable().optional(),
  cachedInputPer1M: z.number().nonnegative().nullable().optional(),
  outputPer1M: z.number().nonnegative().nullable().optional(),
  audioPerMinute: z.number().nonnegative().nullable().optional(),
  rawMetadataJson: z.string().nullable().optional(),
  isEnabled: z.boolean().optional(),
});

export const ModelSourceCreateRequestSchema = z.object({
  name: z.string().min(1).max(128),
  baseUrl: z.string().min(1).max(2048),
  apiKey: z.string().min(1).nullable().optional(),
  supportsChatCompletions: z.boolean().optional(),
  supportsResponses: z.boolean().optional(),
  supportsAudioTranscriptions: z.boolean().optional(),
  supportsEmbeddings: z.boolean().optional(),
  estimateMissingStreamUsage: z.boolean().optional(),
  timeoutSeconds: z.number().int().positive().nullable().optional(),
  maxConcurrency: z.number().int().positive().nullable().optional(),
  routingPolicy: z.enum(["normal", "burn_first", "preserve", "fallback_only"]).optional(),
  models: z.array(ModelSourceModelInputSchema).default([]),
});

export const ModelSourceUpdateRequestSchema = z.object({
  name: z.string().min(1).max(128).optional(),
  baseUrl: z.string().min(1).max(2048).optional(),
  apiKey: z.string().min(1).nullable().optional(),
  isEnabled: z.boolean().optional(),
  supportsChatCompletions: z.boolean().optional(),
  supportsResponses: z.boolean().optional(),
  supportsAudioTranscriptions: z.boolean().optional(),
  supportsEmbeddings: z.boolean().optional(),
  estimateMissingStreamUsage: z.boolean().optional(),
  timeoutSeconds: z.number().int().positive().nullable().optional(),
  maxConcurrency: z.number().int().positive().nullable().optional(),
  routingPolicy: z.enum(["normal", "burn_first", "preserve", "fallback_only"]).optional(),
  models: z.array(ModelSourceModelInputSchema).optional(),
});

export const ModelSourceProbeRequestSchema = z.object({
  sourceId: z.string().nullable().optional(),
  baseUrl: z.string().min(1).max(2048),
  apiKey: z.string().nullable().optional(),
  model: z.string().min(1).max(255),
  upstreamModel: z.string().max(255).nullable().optional(),
  useResponses: z.boolean().optional().default(false),
});

export const ModelSourceProbeResponseSchema = z.object({
  ok: z.boolean(),
  statusCode: z.number().int().nullable().optional(),
  model: z.string(),
  message: z.string(),
});

export type ModelSourceProbeRequest = z.infer<typeof ModelSourceProbeRequestSchema>;
export type ModelSourceProbeResponse = z.infer<typeof ModelSourceProbeResponseSchema>;
export type ModelSource = z.infer<typeof ModelSourceSchema>;
export type ModelSourceModel = z.infer<typeof ModelSourceModelSchema>;
export type ModelSourceModelInput = z.infer<typeof ModelSourceModelInputSchema>;
export type ModelSourceCreateRequest = z.infer<typeof ModelSourceCreateRequestSchema>;
export type ModelSourceUpdateRequest = z.infer<typeof ModelSourceUpdateRequestSchema>;
