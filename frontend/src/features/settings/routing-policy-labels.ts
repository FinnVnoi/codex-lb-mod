import type { TFunction } from "i18next";

import type { DashboardSettings } from "@/features/settings/schemas";

export const GLOBAL_API_ROUTING_OVERRIDES = ["normal", "provider_first", "account_first"] as const;
export const PROVIDER_FAILURE_POLICIES = [
  "account_after_first_failure",
  "providers_before_accounts",
  "provider_only",
] as const;
export const ACCOUNT_FAILURE_POLICIES = [
  "accounts_before_providers",
  "provider_after_first_failure",
  "account_only",
] as const;

export type GlobalApiRoutingOverride = (typeof GLOBAL_API_ROUTING_OVERRIDES)[number];
export type ProviderFailurePolicy = (typeof PROVIDER_FAILURE_POLICIES)[number];
export type AccountFailurePolicy = (typeof ACCOUNT_FAILURE_POLICIES)[number];

export function globalApiRoutingOverrideLabel(
  t: TFunction,
  value: DashboardSettings["globalApiRoutingOverride"],
): string {
  return t(`settings.trafficRouting.globalOverride.options.${value}`);
}

export function providerFailurePolicyLabel(
  t: TFunction,
  value: DashboardSettings["providerFailurePolicy"],
): string {
  return t(`settings.trafficRouting.providerFailure.options.${value}`);
}

export function accountFailurePolicyLabel(
  t: TFunction,
  value: DashboardSettings["accountFailurePolicy"],
): string {
  return t(`settings.trafficRouting.accountFailure.options.${value}`);
}

export function describeEffectiveApiRouting(
  t: TFunction,
  globalOverride: DashboardSettings["globalApiRoutingOverride"],
  apiRoutingMode?: "balanced" | "account_first" | "provider_first" | null,
): string {
  if (globalOverride !== "normal") {
    return t("settings.trafficRouting.effective.global", {
      policy: globalApiRoutingOverrideLabel(t, globalOverride),
    });
  }
  if (apiRoutingMode === "provider_first") {
    return t("settings.trafficRouting.effective.api", {
      policy: globalApiRoutingOverrideLabel(t, "provider_first"),
    });
  }
  if (apiRoutingMode === "account_first") {
    return t("settings.trafficRouting.effective.api", {
      policy: globalApiRoutingOverrideLabel(t, "account_first"),
    });
  }
  return t("settings.trafficRouting.effective.normal");
}
