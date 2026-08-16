import { CalendarClock } from "lucide-react";
import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils";
import {
  formatDateOnly,
  formatDateTimeInline,
  formatSingleUnitRemaining,
  isExpiredDateTime,
  parseDate,
} from "@/utils/formatters";

type SubscriptionRenewalProps = {
  activeUntil: string | null | undefined;
  className?: string;
  showIcon?: boolean;
  showLabel?: boolean;
  showDate?: boolean;
};

export function SubscriptionRenewal({
  activeUntil,
  className,
  showIcon = false,
  showLabel = true,
  showDate = true,
}: SubscriptionRenewalProps) {
  const { t } = useTranslation();
  const until = parseDate(activeUntil);

  if (!until) {
    return (
      <span className={cn("text-muted-foreground", className)}>
        {showLabel ? `${t("accounts.subscription.renewal")}: ` : ""}--
      </span>
    );
  }

  const expired = isExpiredDateTime(until.toISOString());
  const remaining = formatSingleUnitRemaining(until.toISOString());
  const date = formatDateOnly(until.toISOString());
  const text = expired
    ? t("accounts.subscription.expiredAt", { date })
    : showDate
      ? showLabel
        ? t("accounts.subscription.renewalAt", { date })
        : date
      : t("accounts.subscription.renewal");

  return (
    <span
      className={cn(
        "inline-flex min-w-0 items-center gap-1 tabular-nums",
        expired
          ? "text-destructive"
          : remaining.expiringSoon
            ? "text-amber-600 dark:text-amber-400"
            : "text-muted-foreground",
        className,
      )}
      title={t("accounts.subscription.activeUntilTitle", {
        dateTime: formatDateTimeInline(until.toISOString()),
      })}
    >
      {showIcon ? <CalendarClock className="h-3 w-3 shrink-0" aria-hidden="true" /> : null}
      <span className="truncate">
        {text}
        {!expired ? ` · ${remaining.label}` : ""}
      </span>
    </span>
  );
}
