import { z } from "zod";

export const LIMIT_TYPES = ["total_tokens", "input_tokens", "output_tokens", "cost_usd", "credits"] as const;
export const LIMIT_WINDOWS = ["1h", "5h", "daily", "7d", "weekly", "monthly", "lifetime"] as const;

export type LimitType = (typeof LIMIT_TYPES)[number];
export type LimitWindowType = (typeof LIMIT_WINDOWS)[number];

const LimitRuleSchema = z.object({
  id: z.number(),
  limitType: z.enum(LIMIT_TYPES),
  limitWindow: z.enum(LIMIT_WINDOWS),
  maxValue: z.number(),
  currentValue: z.number(),
  modelFilter: z.string().nullable(),
  resetAt: z.iso.datetime({ offset: true }).nullable(),
});

export const LimitRuleCreateSchema = z.object({
  limitType: z.enum(LIMIT_TYPES),
  limitWindow: z.enum(LIMIT_WINDOWS),
  maxValue: z.number().int().positive(),
  modelFilter: z.string().nullable().optional(),
});

const ApiKeyUsageSummarySchema = z.object({
  requestCount: z.number().int().nonnegative(),
  totalTokens: z.number().int().nonnegative(),
  cachedInputTokens: z.number().int().nonnegative(),
  totalCostUsd: z.number().nonnegative().default(0),
});

const SERVICE_TIERS = ["auto", "default", "priority", "flex", "ultrafast"] as const;
export type ServiceTierType = (typeof SERVICE_TIERS)[number];

export const ROUTING_MODES = ["balanced", "account_first", "provider_first"] as const;
export type RoutingMode = (typeof ROUTING_MODES)[number];
export const TRAFFIC_CLASSES = ["foreground", "opportunistic"] as const;
export type TrafficClass = (typeof TRAFFIC_CLASSES)[number];
export const TRANSPORT_POLICY_OVERRIDES = ["smart", "always_http", "always_websocket"] as const;
export type TransportPolicyOverride = (typeof TRANSPORT_POLICY_OVERRIDES)[number];
export const REASONING_EFFORTS = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"] as const;
export type ReasoningEffortType = (typeof REASONING_EFFORTS)[number];
export const ENFORCED_REASONING_EFFORTS = ["none", ...REASONING_EFFORTS] as const;

export const ApiKeySchema = z.object({
  id: z.string(),
  name: z.string(),
  keyPrefix: z.string(),
  allowedModels: z.array(z.string()).nullable(),
  applyToCodexModel: z.boolean().default(false),
  routingMode: z.enum(ROUTING_MODES).default("balanced"),
  enforcedModel: z.string().nullable().default(null),
  allowedReasoningEfforts: z.array(z.enum(REASONING_EFFORTS)).nullable().default(null),
  trafficClass: z
    .enum(TRAFFIC_CLASSES)
    .default("foreground"),
  transportPolicyOverride: z.enum(TRANSPORT_POLICY_OVERRIDES).nullable().default(null),
  enforcedReasoningEffort: z.enum(ENFORCED_REASONING_EFFORTS).nullable().default(null),
  enforcedServiceTier: z
    .enum(SERVICE_TIERS)
    .nullable()
    .default(null),
  usageSections: z.string().default("upstream_limits,account_pool_usage"),
  expiresAt: z.iso.datetime({ offset: true }).nullable(),
  autoExtendExpiry: z.boolean().default(false),
  autoExtendExpiryType: z.enum(["total_tokens", "cost_usd"]).nullable().default(null),
  autoExtendExpiryThreshold: z.number().int().positive().nullable().default(null),
  quotaShopEnabled: z.boolean().default(false),
  quotaShopMaxWindows: z.number().int().positive().default(1),
  quotaShopOptions: z.array(z.object({ limitType: z.string(), limitWindow: z.string() })).default([]),
  isActive: z.boolean(),
  accountAssignmentScopeEnabled: z.boolean().default(false),
  sourceAssignmentScopeEnabled: z.boolean().default(false),
  assignedAccountIds: z.array(z.string()).default([]),
  assignedSourceIds: z.array(z.string()).default([]),
  createdAt: z.iso.datetime({ offset: true }),
  lastUsedAt: z.iso.datetime({ offset: true }).nullable(),
  limits: z.array(LimitRuleSchema).default([]),
  usageSummary: ApiKeyUsageSummarySchema.nullable().default(null),
  pooledRemainingPercentPrimary: z.number().nullable().default(null),
  pooledRemainingPercentSecondary: z.number().nullable().default(null),
  pooledCapacityCreditsPrimary: z.number().default(0),
});

export const USAGE_SECTIONS = ["upstream_limits", "account_pool_usage"] as const;
export type UsageSection = (typeof USAGE_SECTIONS)[number];

export const USAGE_SECTION_LABELS: Record<UsageSection, string> = {
  upstream_limits: "Upstream limits",
  account_pool_usage: "Account pool usage",
};

export const ApiKeyCreateRequestSchema = z.object({
  name: z.string().min(1).max(128),
  allowedModels: z.array(z.string()).optional(),
  applyToCodexModel: z.boolean().optional(),
  routingMode: z.enum(ROUTING_MODES).optional(),
  trafficClass: z.enum(TRAFFIC_CLASSES).optional(),
  transportPolicyOverride: z.enum(TRANSPORT_POLICY_OVERRIDES).nullable().optional(),
  enforcedModel: z.string().min(1).nullable().optional(),
  allowedReasoningEfforts: z.array(z.enum(REASONING_EFFORTS)).min(1).nullable().optional(),
  enforcedReasoningEffort: z.enum(ENFORCED_REASONING_EFFORTS).nullable().optional(),
  enforcedServiceTier: z
    .enum(SERVICE_TIERS)
    .nullable()
    .optional(),
  usageSections: z.string().optional(),
  weeklyTokenLimit: z.number().int().positive().nullable().optional(),
  expiresAt: z.iso.datetime({ offset: true }).nullable().optional(),
  autoExtendExpiry: z.boolean().optional(),
  autoExtendExpiryType: z.enum(["total_tokens", "cost_usd"]).nullable().optional(),
  autoExtendExpiryThreshold: z.number().int().positive().nullable().optional(),
  quotaShopEnabled: z.boolean().optional(),
  quotaShopMaxWindows: z.number().int().positive().optional(),
  quotaShopOptions: z.array(z.object({ limitType: z.string(), limitWindow: z.string() })).optional(),
  assignedAccountIds: z.array(z.string()).optional(),
  assignedSourceIds: z.array(z.string()).optional(),
  limits: z.array(LimitRuleCreateSchema).optional(),
});

export const ApiKeyCreateResponseSchema = ApiKeySchema.extend({
  key: z.string(),
});

export const ApiKeyUpdateRequestSchema = z.object({
  name: z.string().min(1).max(128).optional(),
  allowedModels: z.array(z.string()).nullable().optional(),
  applyToCodexModel: z.boolean().optional(),
  routingMode: z.enum(ROUTING_MODES).optional(),
  trafficClass: z.enum(TRAFFIC_CLASSES).optional(),
  transportPolicyOverride: z.enum(TRANSPORT_POLICY_OVERRIDES).nullable().optional(),
  enforcedModel: z.string().min(1).nullable().optional(),
  allowedReasoningEfforts: z.array(z.enum(REASONING_EFFORTS)).min(1).nullable().optional(),
  enforcedReasoningEffort: z.enum(ENFORCED_REASONING_EFFORTS).nullable().optional(),
  enforcedServiceTier: z
    .enum(SERVICE_TIERS)
    .nullable()
    .optional(),
  usageSections: z.string().optional(),
  weeklyTokenLimit: z.number().int().positive().nullable().optional(),
  expiresAt: z.iso.datetime({ offset: true }).nullable().optional(),
  autoExtendExpiry: z.boolean().optional(),
  autoExtendExpiryType: z.enum(["total_tokens", "cost_usd"]).nullable().optional(),
  autoExtendExpiryThreshold: z.number().int().positive().nullable().optional(),
  quotaShopEnabled: z.boolean().optional(),
  quotaShopMaxWindows: z.number().int().positive().optional(),
  quotaShopOptions: z.array(z.object({ limitType: z.string(), limitWindow: z.string() })).optional(),
  isActive: z.boolean().optional(),
  assignedAccountIds: z.array(z.string()).optional(),
  assignedSourceIds: z.array(z.string()).optional(),
  limits: z.array(LimitRuleCreateSchema).optional(),
  resetUsage: z.boolean().optional(),
});

export const ApiKeyListSchema = z.array(ApiKeySchema);

export type LimitRule = z.infer<typeof LimitRuleSchema>;
export type LimitRuleCreate = z.infer<typeof LimitRuleCreateSchema>;
export type ApiKey = z.infer<typeof ApiKeySchema>;
export type ApiKeyCreateRequest = z.infer<typeof ApiKeyCreateRequestSchema>;
export type ApiKeyCreateResponse = z.infer<typeof ApiKeyCreateResponseSchema>;
export type ApiKeyUpdateRequest = z.infer<typeof ApiKeyUpdateRequestSchema>;

export const ModelItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  sourceOnly: z.boolean().default(false),
  supportedReasoningEfforts: z.array(z.enum(REASONING_EFFORTS)).default([]),
  defaultReasoningEffort: z.enum(REASONING_EFFORTS).nullable().optional(),
});
export const ModelsResponseSchema = z.object({ models: z.array(ModelItemSchema) });
export type ModelItem = z.infer<typeof ModelItemSchema>;
