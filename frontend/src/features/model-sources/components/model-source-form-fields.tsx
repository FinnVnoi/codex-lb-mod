import { Plus, Trash2 } from "lucide-react";
import type { Control } from "react-hook-form";
import { useFieldArray } from "react-hook-form";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
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
  apiKeyLabel: string;
  apiKeyPlaceholder?: string;
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
  apiKeyLabel,
  apiKeyPlaceholder,
}: ModelSourceFormFieldsProps) {
  const { t } = useTranslation();
  const { fields, append, remove } = useFieldArray({ control, name: "models" });

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

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-medium">{t("modelSources.fields.models")}</div>
            <p className="text-xs text-muted-foreground">{t("modelSources.fields.modelsDescription")}</p>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => append({ ...emptyModelFormValue })}>
            <Plus className="mr-1.5 h-4 w-4" />
            {t("modelSources.actions.addModel")}
          </Button>
        </div>

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
