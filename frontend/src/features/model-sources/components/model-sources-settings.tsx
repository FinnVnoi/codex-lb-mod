import { Database, Pencil, Plus, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { AlertMessage } from "@/components/alert-message";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { ModelSourceCreateDialog } from "@/features/model-sources/components/model-source-create-dialog";
import { ModelSourceEditDialog } from "@/features/model-sources/components/model-source-edit-dialog";
import { useModelSources } from "@/features/model-sources/hooks/use-model-sources";
import { globalApiRoutingOverrideLabel, providerFailurePolicyLabel } from "@/features/settings/routing-policy-labels";
import type { DashboardSettings } from "@/features/settings/schemas";
import type {
  ModelSource,
  ModelSourceCreateRequest,
  ModelSourceUpdateRequest,
} from "@/features/model-sources/schemas";
import { useDialogState } from "@/hooks/use-dialog-state";
import { getErrorMessageOrNull } from "@/utils/errors";

function modelPriceLabel(model: ModelSource["models"][number]): string | null {
  if (model.inputPer1M === null && model.outputPer1M === null) return null;
  return `$${model.inputPer1M ?? 0}/$${model.outputPer1M ?? 0} per 1M`;
}

export type ModelSourcesSettingsProps = {
  disabled?: boolean;
  settings?: DashboardSettings | null;
};

function routingPolicyTone(policy: ModelSource["routingPolicy"]): "default" | "secondary" | "outline" | "destructive" {
  if (policy === "burn_first") return "default";
  if (policy === "fallback_only") return "destructive";
  if (policy === "preserve") return "outline";
  return "secondary";
}

function protocolBadges(source: ModelSource) {
  return [
    source.supportsChatCompletions ? "chat" : null,
    source.supportsResponses ? "responses" : null,
    source.supportsAudioTranscriptions ? "audio" : null,
  ].filter((value): value is string => value !== null);
}

export function ModelSourcesSettings({ disabled = false, settings = null }: ModelSourcesSettingsProps) {
  const { t } = useTranslation();
  const {
    modelSourcesQuery,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useModelSources();
  const createDialog = useDialogState();
  const editDialog = useDialogState<ModelSource>();
  const deleteDialog = useDialogState<ModelSource>();
  const sources = modelSourcesQuery.data?.sources ?? [];
  const busy =
    disabled ||
    modelSourcesQuery.isFetching ||
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;
  const error =
    getErrorMessageOrNull(modelSourcesQuery.error) ||
    getErrorMessageOrNull(createMutation.error) ||
    getErrorMessageOrNull(updateMutation.error) ||
    getErrorMessageOrNull(deleteMutation.error);

  const createSource = async (payload: ModelSourceCreateRequest) => {
    await createMutation.mutateAsync(payload);
  };

  const updateSource = async (sourceId: string, payload: ModelSourceUpdateRequest) => {
    await updateMutation.mutateAsync({ sourceId, payload });
  };

  return (
    <section className="space-y-4 rounded-xl border bg-card p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Database className="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <div>
	            <h3 className="text-sm font-semibold">{t("modelSources.title")}</h3>
	            <p className="text-xs text-muted-foreground">{t("modelSources.description")}</p>
          </div>
        </div>
        <Button
          type="button"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          disabled={busy}
          onClick={() => createDialog.show()}
        >
          <Plus className="h-3.5 w-3.5" />
	          {t("modelSources.actions.addSource")}
        </Button>
      </div>

      {error ? <AlertMessage variant="error">{error}</AlertMessage> : null}

      <div className="space-y-2">
        {sources.length > 0 ? (
          sources.map((source) => (
            <div key={source.id} className="rounded-lg border p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{source.name}</span>
                    <Badge variant={!source.isEnabled || source.pausedAt ? "secondary" : "default"}>
                      {!source.isEnabled
                        ? t("common.states.disabled")
                        : source.pausedAt
                          ? t("common.states.paused")
                          : t("common.states.enabled")}
                    </Badge>
                    {source.pausedAt ? (
                      <Badge variant="outline">
                        {t("modelSources.autoPaused", { reason: source.pauseReason ?? "unknown" })}
                      </Badge>
                    ) : null}
                    {protocolBadges(source).map((protocol) => (
                      <Badge key={protocol} variant="secondary">
                        {protocol}
                      </Badge>
                    ))}
                    <Badge variant={routingPolicyTone(source.routingPolicy)}>
                      {t(
                        `common.routingPolicies.${
                          source.routingPolicy === "burn_first"
                            ? "burnFirst"
                            : source.routingPolicy === "fallback_only"
                              ? "fallbackOnly"
                              : source.routingPolicy
                        }`,
                      )}
                    </Badge>
                  </div>
                  <div className="truncate text-xs text-muted-foreground">{source.baseUrl}</div>
                  <div className="flex flex-wrap items-center gap-1 pt-1">
                    {source.models.map((model) => {
                      const price = modelPriceLabel(model);
                      return (
                        <div key={model.id} className="flex items-center gap-1">
                          <Badge variant={model.isEnabled ? "outline" : "secondary"}>
                            {model.upstreamModel && model.upstreamModel !== model.model
                              ? `${model.model} → ${model.upstreamModel}`
                              : model.model}
                          </Badge>
                          {price ? <Badge variant="secondary">{price}</Badge> : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Switch
	                    aria-label={t("modelSources.actions.toggleAria", { name: source.name })}
                    checked={source.isEnabled && !source.pausedAt}
                    disabled={busy}
                    onCheckedChange={(checked) =>
                      void updateMutation.mutateAsync({
                        sourceId: source.id,
                        payload: { isEnabled: checked },
                      })
                    }
                  />
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="ghost"
                    disabled={busy}
                    onClick={() => editDialog.show(source)}
                  >
                    <Pencil className="size-4" />
	                    <span className="sr-only">{t("modelSources.actions.editAria", { name: source.name })}</span>
                  </Button>
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="ghost"
                    disabled={busy}
                    onClick={() => deleteDialog.show(source)}
                  >
                    <Trash2 className="size-4" />
	                    <span className="sr-only">{t("modelSources.actions.deleteAria", { name: source.name })}</span>
                  </Button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
	            {t("modelSources.empty")}
          </div>
        )}
      </div>

      {settings ? (
        <div className="rounded-lg border bg-muted/20 p-3 text-xs text-muted-foreground">
          {t("modelSources.routingSummary", {
            global: globalApiRoutingOverrideLabel(t, settings.globalApiRoutingOverride),
            provider: providerFailurePolicyLabel(t, settings.providerFailurePolicy),
            count: settings.providerMaxAttempts,
          })}
        </div>
      ) : null}

      <ModelSourceCreateDialog
        open={createDialog.open}
        busy={createMutation.isPending}
        onOpenChange={createDialog.onOpenChange}
        onSubmit={createSource}
      />

      <ModelSourceEditDialog
        open={editDialog.open}
        busy={updateMutation.isPending}
        source={editDialog.data}
        onOpenChange={editDialog.onOpenChange}
        onSubmit={updateSource}
      />

      <ConfirmDialog
        open={deleteDialog.open}
	        title={t("modelSources.deleteDialog.title")}
	        description={t("modelSources.deleteDialog.description")}
	        confirmLabel={t("common.actions.delete")}
        onOpenChange={deleteDialog.onOpenChange}
        onConfirm={() => {
          if (!deleteDialog.data) return;
          void deleteMutation.mutateAsync(deleteDialog.data.id).finally(() => deleteDialog.hide());
        }}
      />
    </section>
  );
}
