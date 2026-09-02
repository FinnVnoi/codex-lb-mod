import { Route, ShieldAlert } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { buildSettingsUpdateRequest } from "@/features/settings/payload";
import {
  ACCOUNT_FAILURE_POLICIES,
  GLOBAL_API_ROUTING_OVERRIDES,
  PROVIDER_FAILURE_POLICIES,
  accountFailurePolicyLabel,
  globalApiRoutingOverrideLabel,
  providerFailurePolicyLabel,
} from "@/features/settings/routing-policy-labels";
import type { DashboardSettings, SettingsUpdateRequest } from "@/features/settings/schemas";

export type TrafficRoutingSettingsProps = {
  settings: DashboardSettings;
  busy: boolean;
  compact?: boolean;
  onSave: (payload: SettingsUpdateRequest) => Promise<void>;
};

function clampAttempts(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.max(1, Math.min(10, Math.trunc(value)));
}

export function TrafficRoutingSettings({
  settings,
  busy,
  compact = false,
  onSave,
}: TrafficRoutingSettingsProps) {
  const { t } = useTranslation();
  const save = (patch: Partial<SettingsUpdateRequest>) =>
    void onSave(buildSettingsUpdateRequest(settings, patch));

  return (
    <section className="space-y-4 rounded-xl border bg-card p-5" data-testid="traffic-routing-settings">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Route className="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{t("settings.trafficRouting.title")}</h3>
            <p className="text-xs text-muted-foreground">{t("settings.trafficRouting.description")}</p>
          </div>
        </div>
        <Badge variant={settings.globalApiRoutingOverride === "normal" ? "secondary" : "default"}>
          {globalApiRoutingOverrideLabel(t, settings.globalApiRoutingOverride)}
        </Badge>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="space-y-2 rounded-lg border p-3">
          <div>
            <p className="text-sm font-medium">{t("settings.trafficRouting.globalOverride.label")}</p>
            <p className="text-xs text-muted-foreground">
              {t("settings.trafficRouting.globalOverride.description")}
            </p>
          </div>
          <Select
            value={settings.globalApiRoutingOverride}
            onValueChange={(value) =>
              save({ globalApiRoutingOverride: value as DashboardSettings["globalApiRoutingOverride"] })
            }
          >
            <SelectTrigger className="h-8 text-xs" disabled={busy} aria-label={t("settings.trafficRouting.globalOverride.label")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {GLOBAL_API_ROUTING_OVERRIDES.map((value) => (
                <SelectItem key={value} value={value}>
                  {globalApiRoutingOverrideLabel(t, value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2 rounded-lg border p-3">
          <div>
            <p className="text-sm font-medium">{t("settings.trafficRouting.providerFailure.label")}</p>
            <p className="text-xs text-muted-foreground">
              {t("settings.trafficRouting.providerFailure.description")}
            </p>
          </div>
          <Select
            value={settings.providerFailurePolicy}
            onValueChange={(value) =>
              save({ providerFailurePolicy: value as DashboardSettings["providerFailurePolicy"] })
            }
          >
            <SelectTrigger className="h-8 text-xs" disabled={busy} aria-label={t("settings.trafficRouting.providerFailure.label")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PROVIDER_FAILURE_POLICIES.map((value) => (
                <SelectItem key={value} value={value}>
                  {providerFailurePolicyLabel(t, value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2 rounded-lg border p-3">
          <div>
            <p className="text-sm font-medium">{t("settings.trafficRouting.accountFailure.label")}</p>
            <p className="text-xs text-muted-foreground">
              {t("settings.trafficRouting.accountFailure.description")}
            </p>
          </div>
          <Select
            value={settings.accountFailurePolicy}
            onValueChange={(value) =>
              save({ accountFailurePolicy: value as DashboardSettings["accountFailurePolicy"] })
            }
          >
            <SelectTrigger className="h-8 text-xs" disabled={busy} aria-label={t("settings.trafficRouting.accountFailure.label")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACCOUNT_FAILURE_POLICIES.map((value) => (
                <SelectItem key={value} value={value}>
                  {accountFailurePolicyLabel(t, value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 rounded-lg border p-3 text-xs font-medium">
          {t("settings.trafficRouting.providerMaxAttempts.label")}
          <Input
            aria-label={t("settings.trafficRouting.providerMaxAttempts.label")}
            type="number"
            min={1}
            max={10}
            step={1}
            inputMode="numeric"
            value={settings.providerMaxAttempts}
            disabled={busy}
            onChange={(event) =>
              save({ providerMaxAttempts: clampAttempts(Number(event.target.value)) })
            }
            className="h-8 text-xs"
          />
          <span className="block text-[11px] text-muted-foreground">
            {t("settings.trafficRouting.providerMaxAttempts.description")}
          </span>
        </label>
        <label className="space-y-1 rounded-lg border p-3 text-xs font-medium">
          {t("settings.trafficRouting.accountMaxAttempts.label")}
          <Input
            aria-label={t("settings.trafficRouting.accountMaxAttempts.label")}
            type="number"
            min={1}
            max={10}
            step={1}
            inputMode="numeric"
            value={settings.accountMaxAttempts}
            disabled={busy}
            onChange={(event) =>
              save({ accountMaxAttempts: clampAttempts(Number(event.target.value)) })
            }
            className="h-8 text-xs"
          />
          <span className="block text-[11px] text-muted-foreground">
            {t("settings.trafficRouting.accountMaxAttempts.description")}
          </span>
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex items-center justify-between gap-3 rounded-lg border p-3 text-xs font-medium">
          <span>
            <span className="block text-sm">{t("settings.trafficRouting.autoPause.label")}</span>
            <span className="block text-[11px] font-normal text-muted-foreground">
              {t("settings.trafficRouting.autoPause.description")}
            </span>
          </span>
          <Switch
            checked={settings.modelSourceAutoPauseEnabled}
            disabled={busy}
            onCheckedChange={(checked) => save({ modelSourceAutoPauseEnabled: checked })}
          />
        </label>
        <label className="space-y-1 rounded-lg border p-3 text-xs font-medium">
          {t("settings.trafficRouting.autoPauseThreshold.label")}
          <Input
            type="number"
            min={1}
            max={10}
            step={1}
            value={settings.modelSourceAutoPauseThreshold}
            disabled={busy || !settings.modelSourceAutoPauseEnabled}
            onChange={(event) => save({ modelSourceAutoPauseThreshold: clampAttempts(Number(event.target.value)) })}
            className="h-8 text-xs"
          />
          <span className="block text-[11px] text-muted-foreground">
            {t("settings.trafficRouting.autoPauseThreshold.description")}
          </span>
        </label>
      </div>

      {!compact ? (
        <div className="flex gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-muted-foreground">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
          <p>{t("settings.trafficRouting.note")}</p>
        </div>
      ) : null}
    </section>
  );
}
