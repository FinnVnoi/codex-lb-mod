import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SubscriptionRenewal } from "@/features/accounts/components/subscription-renewal";

describe("SubscriptionRenewal", () => {
  afterEach(() => vi.useRealTimers());

  it("renders a translated renewal label with a non-negative countdown", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T12:00:00.000Z"));
    render(<SubscriptionRenewal activeUntil="2026-01-11T12:00:00.000Z" showIcon />);
    expect(screen.getByText("Renewal 01/11/2026 · 10d")).toBeInTheDocument();
    expect(screen.queryByText(/accounts\.subscription/)).not.toBeInTheDocument();
  });

  it("renders an expired date without a negative countdown", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-07T12:00:00.000Z"));
    render(<SubscriptionRenewal activeUntil="2026-01-11T12:00:00.000Z" showIcon />);
    expect(screen.getByText("Expired 01/11/2026")).toBeInTheDocument();
    expect(screen.queryByText(/-\d+d/)).not.toBeInTheDocument();
  });
});
