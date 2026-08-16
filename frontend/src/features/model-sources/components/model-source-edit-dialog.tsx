import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Form } from "@/components/ui/form";
import { ModelSourceFormFields } from "@/features/model-sources/components/model-source-form-fields";
import {
  createModelSourceFormSchema,
  formValuesFromSource,
  modelInputsFromForm,
  type ModelSourceFormValues,
} from "@/features/model-sources/components/model-source-form";
import type { ModelSource, ModelSourceUpdateRequest } from "@/features/model-sources/schemas";

export type ModelSourceEditDialogProps = {
  open: boolean;
  busy: boolean;
  source: ModelSource | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (sourceId: string, payload: ModelSourceUpdateRequest) => Promise<void>;
};

type ModelSourceEditFormProps = {
  source: ModelSource;
  busy: boolean;
  onSubmit: (sourceId: string, payload: ModelSourceUpdateRequest) => Promise<void>;
  onClose: () => void;
};

function ModelSourceEditForm({ source, busy, onSubmit, onClose }: ModelSourceEditFormProps) {
  const { t } = useTranslation();
  const form = useForm<ModelSourceFormValues>({
    resolver: zodResolver(createModelSourceFormSchema(t)),
    defaultValues: formValuesFromSource(source),
  });

  const handleSubmit = async (values: ModelSourceFormValues) => {
    const payload: ModelSourceUpdateRequest = {
      name: values.name,
      baseUrl: values.baseUrl,
      supportsChatCompletions: values.supportsChatCompletions,
      supportsResponses: values.supportsResponses,
      supportsAudioTranscriptions: values.supportsAudioTranscriptions,
      routingPolicy: values.routingPolicy,
      models: modelInputsFromForm(values, source.models),
    };
    const apiKey = values.apiKey.trim();
    if (apiKey) payload.apiKey = apiKey;
    try {
      await onSubmit(source.id, payload);
    } catch {
      return;
    }
    onClose();
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <ModelSourceFormFields
          control={form.control}
          apiKeyLabel={t("modelSources.fields.upstreamApiKey")}
          apiKeyPlaceholder={t("modelSources.editDialog.keepCurrentKey")}
        />
        <DialogFooter>
          <Button type="submit" disabled={busy || form.formState.isSubmitting}>
            {t("common.actions.save")}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
}

export function ModelSourceEditDialog({ open, busy, source, onOpenChange, onSubmit }: ModelSourceEditDialogProps) {
  const { t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>{t("modelSources.editDialog.title")}</DialogTitle>
          <DialogDescription>{t("modelSources.editDialog.description")}</DialogDescription>
        </DialogHeader>
        {source ? (
          <ModelSourceEditForm
            key={`${source.id}:${open ? "open" : "closed"}`}
            source={source}
            busy={busy}
            onSubmit={onSubmit}
            onClose={() => onOpenChange(false)}
          />
        ) : (
          <p className="text-sm text-muted-foreground">{t("modelSources.editDialog.selectSource")}</p>
        )}
      </DialogContent>
    </Dialog>
  );
}
