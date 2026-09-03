import { Network } from "lucide-react";
import { useTranslation } from "react-i18next";

import { ModelSourcesSettings } from "@/features/model-sources/components/model-sources-settings";
import { useAuthStore } from "@/features/auth/hooks/use-auth";
import { TrafficRoutingSettings } from "@/features/settings/components/traffic-routing-settings";
import { useSettings } from "@/features/settings/hooks/use-settings";

export function ModelSourcesPage() {
  const { t } = useTranslation();
  const canWrite = useAuthStore((state) => state.canWrite);
  const { settingsQuery, updateSettingsMutation } = useSettings();
  const settings = settingsQuery.data;
  const controlsDisabled = !canWrite || updateSettingsMutation.isPending || settingsQuery.isFetching;

  return (
    <div className="animate-fade-in-up space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <Network className="h-5 w-5 text-primary" />
          {t("modelSources.page.title")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("modelSources.page.subtitle")}</p>
      </div>
      {!canWrite ? (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs font-medium text-foreground">
          {t("settings.page.readOnlyNotice")}
        </div>
      ) : null}
      {settings ? (
        <TrafficRoutingSettings
          settings={settings}
          busy={controlsDisabled}
          onSave={async (payload) => {
            await updateSettingsMutation.mutateAsync(payload);
          }}
        />
      ) : null}
      <ModelSourcesSettings disabled={!canWrite} settings={settings} />
    </div>
  );
}
