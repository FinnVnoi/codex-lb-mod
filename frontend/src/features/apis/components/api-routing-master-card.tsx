import { Route } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { buildSettingsUpdateRequest } from "@/features/settings/payload";
import {
  GLOBAL_API_ROUTING_OVERRIDES,
  describeEffectiveApiRouting,
  globalApiRoutingOverrideLabel,
} from "@/features/settings/routing-policy-labels";
import type { DashboardSettings, SettingsUpdateRequest } from "@/features/settings/schemas";

export type ApiRoutingMasterCardProps = {
  settings: DashboardSettings;
  busy: boolean;
  onSave: (payload: SettingsUpdateRequest) => Promise<void>;
};

export function ApiRoutingMasterCard({ settings, busy, onSave }: ApiRoutingMasterCardProps) {
  const { t } = useTranslation();
  const saveGlobalOverride = (globalApiRoutingOverride: DashboardSettings["globalApiRoutingOverride"]) => {
    void onSave(buildSettingsUpdateRequest(settings, { globalApiRoutingOverride }));
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="api-routing-master-card">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Route className="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{t("apis.routingMaster.title")}</h3>
            <p className="text-xs text-muted-foreground">{t("apis.routingMaster.description")}</p>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:items-end">
          <Select value={settings.globalApiRoutingOverride} onValueChange={(value) => saveGlobalOverride(value as DashboardSettings["globalApiRoutingOverride"])}>
            <SelectTrigger className="h-8 w-full text-xs sm:w-52" disabled={busy} aria-label={t("apis.routingMaster.selectAria")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="end">
              {GLOBAL_API_ROUTING_OVERRIDES.map((value) => (
                <SelectItem key={value} value={value}>
                  {globalApiRoutingOverrideLabel(t, value)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Badge variant={settings.globalApiRoutingOverride === "normal" ? "secondary" : "default"}>
            {describeEffectiveApiRouting(t, settings.globalApiRoutingOverride, "balanced")}
          </Badge>
        </div>
      </div>
    </section>
  );
}
