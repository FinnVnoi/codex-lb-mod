import { CheckCircle2, Copy, Download, LoaderCircle, Plus, Trash2, Upload, XCircle } from "lucide-react";
import { useState } from "react";
import type { Control, UseFormSetValue } from "react-hook-form";
import { useFieldArray, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { probeModelSource } from "@/features/model-sources/api";
import { Checkbox } from "@/components/ui/checkbox";
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  emptyModelFormValue,
  type ModelSourceFormValues,
} from "@/features/model-sources/components/model-source-form";

type ModelSourceFormFieldsProps = {
  control: Control<ModelSourceFormValues>;
  setValue: UseFormSetValue<ModelSourceFormValues>;
  apiKeyLabel: string;
  apiKeyPlaceholder?: string;
  sourceId?: string;
};

const PROVIDER_CAPABILITIES = [
  ["supportsChatCompletions", "modelSources.capabilities.chatCompletions"] as const,
  ["supportsResponses", "modelSources.capabilities.responses"] as const,
  ["supportsAudioTranscriptions", "modelSources.capabilities.audioTranscriptions"] as const,
];

const MODEL_CAPABILITIES = [
  ["supportsStreaming", "modelSources.capabilities.streaming"] as const,
  ["supportsTools", "modelSources.capabilities.tools"] as const,
  ["supportsVision", "modelSources.capabilities.vision"] as const,
  ["supportsReasoning", "modelSources.capabilities.reasoning"] as const,
  ["isEnabled", "modelSources.fields.modelEnabled"] as const,
];

export function ModelSourceFormFields({
  control,
  setValue,
  apiKeyLabel,
  apiKeyPlaceholder,
  sourceId,
}: ModelSourceFormFieldsProps) {
  const { t } = useTranslation();
  const { fields, append, remove } = useFieldArray({ control, name: "models" });
  const models = useWatch({ control, name: "models" }) ?? [];
  const baseUrl = useWatch({ control, name: "baseUrl" }) ?? "";
  const apiKey = useWatch({ control, name: "apiKey" }) ?? "";
  const supportsResponses = useWatch({ control, name: "supportsResponses" }) ?? false;
  const [probePending, setProbePending] = useState(false);
  const [probeResult, setProbeResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [jsonText, setJsonText] = useState("");
  const [jsonError, setJsonError] = useState<string | null>(null);
  const exportModels = () => setJsonText(JSON.stringify(models, null, 2));
  const importModels = () => {
    try {
      const parsed: unknown = JSON.parse(jsonText);
      if (!Array.isArray(parsed) || parsed.length === 0) throw new Error("invalid");
      const imported = parsed.map((raw) => {
        if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("invalid");
        const model = raw as Record<string, unknown>;
        if (typeof model.model !== "string" || !model.model.trim()) throw new Error("invalid");
        const text = (key: string) => model[key] == null ? "" : String(model[key]);
        const flag = (key: string, fallback: boolean) => typeof model[key] === "boolean" ? model[key] : fallback;
        return {
          model: model.model,
          upstreamModel: text("upstreamModel"),
          contextWindow: text("contextWindow"),
          maxOutputTokens: text("maxOutputTokens"),
          inputPer1M: text("inputPer1M"),
          cachedInputPer1M: text("cachedInputPer1M"),
          outputPer1M: text("outputPer1M"),
          audioPerMinute: text("audioPerMinute"),
          supportsStreaming: flag("supportsStreaming", true),
          supportsTools: flag("supportsTools", false),
          supportsVision: flag("supportsVision", false),
          supportsReasoning: flag("supportsReasoning", false),
          isEnabled: flag("isEnabled", true),
        };
      });
      setValue("models", imported, { shouldDirty: true, shouldValidate: true });
      setJsonError(null);
    } catch {
      setJsonError(t("modelSources.modelsJson.invalid"));
    }
  };
  const probeProvider = async () => {
    const firstModel = models.find((model) => model.isEnabled && model.model.trim());
    if (!baseUrl.trim() || !firstModel) return;
    setProbePending(true);
    setProbeResult(null);
    try {
      const result = await probeModelSource({
        sourceId,
        baseUrl: baseUrl.trim(),
        apiKey: apiKey.trim() || undefined,
        model: firstModel.model.trim(),
        upstreamModel: firstModel.upstreamModel.trim() || undefined,
        useResponses: supportsResponses,
      });
      setProbeResult({ ok: result.ok, message: result.message });
    } catch (error) {
      setProbeResult({ ok: false, message: error instanceof Error ? error.message : String(error) });
    } finally {
      setProbePending(false);
    }
  };

  const copyModels = async () => {
    const text = jsonText || JSON.stringify(models, null, 2);
    setJsonText(text);
    await navigator.clipboard?.writeText(text);
  };

  return (
    <>
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField
          control={control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t("apiKeys.table.name")}</FormLabel>
              <FormControl><Input {...field} autoComplete="off" /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="baseUrl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t("modelSources.fields.baseUrl")}</FormLabel>
              <FormControl>
                <Input {...field} placeholder="https://api.example.com/v1" autoComplete="off" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={control}
        name="apiKey"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{apiKeyLabel}</FormLabel>
            <FormControl>
              <Input {...field} type="password" autoComplete="new-password" placeholder={apiKeyPlaceholder} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="flex flex-wrap items-center gap-3 rounded-lg border p-3">
        <Button
          type="button"
          variant="outline"
          disabled={probePending || !baseUrl.trim() || !models.some((model) => model.isEnabled && model.model.trim())}
          onClick={() => void probeProvider()}
        >
          {probePending ? <LoaderCircle className="mr-1.5 h-4 w-4 animate-spin" /> : null}
          {t("modelSources.actions.checkProvider")}
        </Button>
        {probeResult ? (
          <p className={`flex items-center gap-1.5 text-xs ${probeResult.ok ? "text-emerald-600" : "text-destructive"}`}>
            {probeResult.ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {probeResult.message}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">{t("modelSources.probe.description")}</p>
        )}
      </div>

      <FormField
        control={control}
        name="routingPolicy"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{t("modelSources.fields.routingPolicy")}</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="burn_first">{t("common.routingPolicies.burnFirst")}</SelectItem>
                <SelectItem value="normal">{t("common.routingPolicies.normal")}</SelectItem>
                <SelectItem value="preserve">{t("common.routingPolicies.preserve")}</SelectItem>
                <SelectItem value="fallback_only">{t("common.routingPolicies.fallbackOnly")}</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {t("modelSources.fields.routingPolicyDescription")}
            </p>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid gap-2 sm:grid-cols-3">
        {PROVIDER_CAPABILITIES.map(([key, labelKey]) => (
          <FormField
            key={key}
            control={control}
            name={key}
            render={({ field }) => (
              <FormItem>
                <label className="flex items-center gap-2 rounded-md border p-2 text-sm">
                  <FormControl>
                    <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(checked === true)} />
                  </FormControl>
                  {t(labelKey)}
                </label>
              </FormItem>
            )}
          />
        ))}
      </div>

      <FormField
        control={control}
        name="estimateMissingStreamUsage"
        render={({ field }) => (
          <FormItem>
            <label className="flex items-start gap-2 rounded-md border p-3 text-sm">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={(checked) => field.onChange(checked === true)}
                />
              </FormControl>
              <span>
                <span className="block font-medium">{t("modelSources.fields.estimateMissingStreamUsage")}</span>
                <span className="block text-xs text-muted-foreground">
                  {t("modelSources.fields.estimateMissingStreamUsageDescription")}
                </span>
              </span>
            </label>
          </FormItem>
        )}
      />

      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-medium">{t("modelSources.fields.models")}</div>
            <p className="text-xs text-muted-foreground">{t("modelSources.fields.modelsDescription")}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" size="sm" onClick={exportModels}>
              <Download className="mr-1.5 h-4 w-4" />{t("modelSources.modelsJson.export")}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => void copyModels()}>
              <Copy className="mr-1.5 h-4 w-4" />{t("modelSources.modelsJson.copy")}
            </Button>
            <Button type="button" variant="outline" size="sm" disabled={!jsonText.trim()} onClick={importModels}>
              <Upload className="mr-1.5 h-4 w-4" />{t("modelSources.modelsJson.import")}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => append({ ...emptyModelFormValue })}>
              <Plus className="mr-1.5 h-4 w-4" />{t("modelSources.actions.addModel")}
            </Button>
          </div>
        </div>
        <textarea
          value={jsonText}
          onChange={(event) => { setJsonText(event.target.value); setJsonError(null); }}
          placeholder={t("modelSources.modelsJson.placeholder")}
          className="min-h-28 w-full rounded-md border bg-background px-3 py-2 font-mono text-xs"
          aria-label={t("modelSources.modelsJson.aria")}
        />
        <p className="text-xs text-muted-foreground">{t("modelSources.modelsJson.description")}</p>
        {jsonError ? <p className="text-xs text-destructive">{jsonError}</p> : null}

        {fields.map((fieldItem, index) => (
          <div key={fieldItem.id} className="space-y-4 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium">{t("modelSources.fields.modelNumber", { number: index + 1 })}</div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                disabled={fields.length === 1}
                onClick={() => remove(index)}
                aria-label={t("modelSources.actions.removeModel")}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                control={control}
                name={`models.${index}.model`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("modelSources.fields.publicModel")}</FormLabel>
                    <FormControl><Input {...field} placeholder="gpt-5.5-cpa" autoComplete="off" /></FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={control}
                name={`models.${index}.upstreamModel`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("modelSources.fields.upstreamModel")}</FormLabel>
                    <FormControl><Input {...field} placeholder="vendor/real-model" autoComplete="off" /></FormControl>
                    <p className="text-xs text-muted-foreground">{t("modelSources.fields.singleModelAliasDescription")}</p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                control={control}
                name={`models.${index}.contextWindow`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("modelSources.fields.contextWindow")}</FormLabel>
                    <FormControl><Input {...field} placeholder="128000" inputMode="numeric" /></FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={control}
                name={`models.${index}.maxOutputTokens`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("modelSources.fields.maxOutputTokens")}</FormLabel>
                    <FormControl><Input {...field} placeholder="32768" inputMode="numeric" /></FormControl>
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">{t("modelSources.fields.pricing")}</div>
              <p className="text-xs text-muted-foreground">{t("modelSources.fields.perModelPricingDescription")}</p>
              <div className="grid gap-3 sm:grid-cols-3">
                {([
                  ["inputPer1M", "common.units.input"],
                  ["cachedInputPer1M", "common.units.cached"],
                  ["outputPer1M", "common.units.output"],
                ] as const).map(([key, labelKey]) => (
                  <FormField
                    key={key}
                    control={control}
                    name={`models.${index}.${key}`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs text-muted-foreground">{t(labelKey)}</FormLabel>
                        <FormControl><Input {...field} placeholder="0.00" inputMode="decimal" /></FormControl>
                      </FormItem>
                    )}
                  />
                ))}
              </div>
            </div>

            <FormField
              control={control}
              name={`models.${index}.audioPerMinute`}
              render={({ field }) => (
                <FormItem className="max-w-xs">
                  <FormLabel>{t("modelSources.fields.audioPricing")}</FormLabel>
                  <FormControl><Input {...field} placeholder="0.00" inputMode="decimal" /></FormControl>
                </FormItem>
              )}
            />

            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {MODEL_CAPABILITIES.map(([key, labelKey]) => (
                <FormField
                  key={key}
                  control={control}
                  name={`models.${index}.${key}`}
                  render={({ field }) => (
                    <FormItem>
                      <label className="flex items-center gap-2 rounded-md border bg-background p-2 text-sm">
                        <FormControl>
                          <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(checked === true)} />
                        </FormControl>
                        {t(labelKey)}
                      </label>
                    </FormItem>
                  )}
                />
              ))}
            </div>
          </div>
        ))}
        <FormField control={control} name="models" render={() => <FormItem><FormMessage /></FormItem>} />
      </div>
    </>
  );
}
