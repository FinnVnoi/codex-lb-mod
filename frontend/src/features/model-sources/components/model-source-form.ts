import type { TFunction } from "i18next";
import { z } from "zod";

import type { ModelSource, ModelSourceModel, ModelSourceModelInput } from "@/features/model-sources/schemas";

const modelFormSchema = z.object({
  model: z.string().min(1, "Public model ID is required"),
  upstreamModel: z.string(),
  contextWindow: z.string(),
  maxOutputTokens: z.string(),
  inputPer1M: z.string(),
  cachedInputPer1M: z.string(),
  outputPer1M: z.string(),
  audioPerMinute: z.string(),
  supportsStreaming: z.boolean(),
  supportsTools: z.boolean(),
  supportsVision: z.boolean(),
  supportsReasoning: z.boolean(),
  isEnabled: z.boolean(),
});

export function createModelSourceFormSchema(t: TFunction) {
  return z.object({
    name: z.string().min(1, t("modelSources.validation.nameRequired")),
    baseUrl: z.string().min(1, t("modelSources.validation.baseUrlRequired")),
    apiKey: z.string(),
    supportsChatCompletions: z.boolean(),
    supportsResponses: z.boolean(),
    supportsAudioTranscriptions: z.boolean(),
    supportsEmbeddings: z.boolean(),
    estimateMissingStreamUsage: z.boolean(),
    routingPolicy: z.enum(["normal", "burn_first", "preserve", "fallback_only"]),
    models: z.array(modelFormSchema).min(1, t("modelSources.validation.modelsRequired")),
  });
}

export const modelSourceFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  baseUrl: z.string().min(1, "Base URL is required"),
  apiKey: z.string(),
  supportsChatCompletions: z.boolean(),
  supportsResponses: z.boolean(),
  supportsAudioTranscriptions: z.boolean(),
  supportsEmbeddings: z.boolean(),
  estimateMissingStreamUsage: z.boolean(),
  routingPolicy: z.enum(["normal", "burn_first", "preserve", "fallback_only"]),
  models: z.array(modelFormSchema).min(1, "At least one model is required"),
});

export type ModelSourceFormValues = z.infer<typeof modelSourceFormSchema>;
export type ModelSourceModelFormValue = ModelSourceFormValues["models"][number];

export const emptyModelFormValue: ModelSourceModelFormValue = {
  model: "",
  upstreamModel: "",
  contextWindow: "",
  maxOutputTokens: "",
  inputPer1M: "",
  cachedInputPer1M: "",
  outputPer1M: "",
  audioPerMinute: "",
  supportsStreaming: true,
  supportsTools: false,
  supportsVision: false,
  supportsReasoning: false,
  isEnabled: true,
};

function parsePositiveInt(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function parseNonNegativeFloat(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseFloat(trimmed);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function numberToInput(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

const DEFAULT_REASONING_EFFORTS = ["low", "medium", "high"];

function normalizeReasoningEffort(value: string): string {
  return value.trim();
}

function dedupeReasoningEfforts(values: Iterable<string>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = normalizeReasoningEffort(value);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

export function parseReasoningEffortsInput(value: string): string[] {
  return dedupeReasoningEfforts(value.split(/[\n,]/));
}

function normalizeDefaultReasoningEffort(
  reasoningEfforts: string[],
  defaultReasoningEffort: string,
): string {
  const normalizedDefault = normalizeReasoningEffort(defaultReasoningEffort);
  if (normalizedDefault && reasoningEfforts.includes(normalizedDefault)) {
    return normalizedDefault;
  }
  return reasoningEfforts[0] ?? "";
}

function parseReasoningMetadata(rawMetadataJson: string | null | undefined): {
  supportsReasoning: boolean;
  reasoningEfforts: string[];
  defaultReasoningEffort: string;
} {
  const fallback = { supportsReasoning: false, reasoningEfforts: [], defaultReasoningEffort: "" };
  if (!rawMetadataJson) return fallback;
  try {
    const parsed: unknown = JSON.parse(rawMetadataJson);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return fallback;
    const metadata = parsed as Record<string, unknown>;
    const supportsReasoning = metadata.supports_reasoning === true;
    const declaredLevels = Array.isArray(metadata.supported_reasoning_levels)
      ? dedupeReasoningEfforts(
          metadata.supported_reasoning_levels.flatMap((value): string[] => {
            if (typeof value === "string") return [value];
            if (typeof value !== "object" || value === null || Array.isArray(value)) return [];
            const effort = (value as Record<string, unknown>).effort;
            return typeof effort === "string" ? [effort] : [];
          }),
        )
      : [];
    const reasoningEfforts = supportsReasoning && declaredLevels.length === 0
      ? DEFAULT_REASONING_EFFORTS
      : declaredLevels;
    return {
      supportsReasoning,
      reasoningEfforts,
      defaultReasoningEffort: normalizeDefaultReasoningEffort(
        reasoningEfforts,
        typeof metadata.default_reasoning_level === "string" ? metadata.default_reasoning_level : "",
      ),
    };
  } catch {
    return fallback;
  }
}

export function mergeReasoningMetadata(
  existing: string | null | undefined,
  supportsReasoning: boolean,
  reasoningEfforts: string[] = [],
  defaultReasoningEffort = "",
): string | null {
  let metadata: Record<string, unknown> = {};
  if (existing) {
    try {
      const parsed: unknown = JSON.parse(existing);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        metadata = parsed as Record<string, unknown>;
      }
    } catch {
      metadata = {};
    }
  }
  if (supportsReasoning) {
    metadata.supports_reasoning = true;
    const normalizedEfforts = dedupeReasoningEfforts(reasoningEfforts);
    if (normalizedEfforts.length > 0) {
      metadata.supported_reasoning_levels = normalizedEfforts;
      metadata.default_reasoning_level = normalizeDefaultReasoningEffort(
        normalizedEfforts,
        defaultReasoningEffort,
      );
    }
  } else {
    delete metadata.supports_reasoning;
    delete metadata.supported_reasoning_levels;
    delete metadata.default_reasoning_level;
  }
  return Object.keys(metadata).length > 0 ? JSON.stringify(metadata) : null;
}

export function modelFormValueFromSource(model: ModelSourceModel): ModelSourceModelFormValue {
  return {
    model: model.model,
    upstreamModel: model.upstreamModel ?? model.model,
    contextWindow: numberToInput(model.contextWindow),
    maxOutputTokens: numberToInput(model.maxOutputTokens),
    inputPer1M: numberToInput(model.inputPer1M),
    cachedInputPer1M: numberToInput(model.cachedInputPer1M),
    outputPer1M: numberToInput(model.outputPer1M),
    audioPerMinute: numberToInput(model.audioPerMinute),
    supportsStreaming: model.supportsStreaming,
    supportsTools: model.supportsTools,
    supportsVision: model.supportsVision,
    supportsReasoning: parseReasoningMetadata(model.rawMetadataJson).supportsReasoning,
    isEnabled: model.isEnabled,
  };
}

export function formValuesFromSource(source: ModelSource): ModelSourceFormValues {
  return {
    name: source.name,
    baseUrl: source.baseUrl,
    apiKey: "",
    supportsChatCompletions: source.supportsChatCompletions,
    supportsResponses: source.supportsResponses,
    supportsAudioTranscriptions: source.supportsAudioTranscriptions,
    supportsEmbeddings: source.supportsEmbeddings,
    estimateMissingStreamUsage: source.estimateMissingStreamUsage ?? true,
    routingPolicy: source.routingPolicy,
    models: source.models.map(modelFormValueFromSource),
  };
}

export function modelInputsFromForm(
  values: ModelSourceFormValues,
  existingModels: ModelSourceModel[] = [],
): ModelSourceModelInput[] {
  const existingByPublicId = new Map(existingModels.map((model) => [model.model, model]));
  return values.models.map((model) => {
    const publicId = model.model.trim();
    const upstreamId = model.upstreamModel.trim();
    const existing = existingByPublicId.get(publicId);
    return {
      model: publicId,
      upstreamModel: upstreamId && upstreamId !== publicId ? upstreamId : null,
      displayName: existing?.displayName ?? publicId,
      contextWindow: parsePositiveInt(model.contextWindow),
      maxOutputTokens: parsePositiveInt(model.maxOutputTokens),
      supportsStreaming: model.supportsStreaming,
      supportsTools: model.supportsTools,
      supportsVision: model.supportsVision,
      inputPer1M: parseNonNegativeFloat(model.inputPer1M),
      cachedInputPer1M: parseNonNegativeFloat(model.cachedInputPer1M),
      outputPer1M: parseNonNegativeFloat(model.outputPer1M),
      audioPerMinute: parseNonNegativeFloat(model.audioPerMinute),
      rawMetadataJson: mergeReasoningMetadata(
        existing?.rawMetadataJson,
        model.supportsReasoning,
        parseReasoningMetadata(existing?.rawMetadataJson).reasoningEfforts,
        parseReasoningMetadata(existing?.rawMetadataJson).defaultReasoningEffort,
      ),
      isEnabled: model.isEnabled,
    };
  });
}
