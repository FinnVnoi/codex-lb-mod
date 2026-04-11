import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountListItem } from "@/features/accounts/components/account-list-item";
import { createAccountSummary } from "@/test/mocks/factories";

describe("AccountListItem", () => {
  it("renders neutral quota track when secondary remaining percent is unknown", () => {
    const account = createAccountSummary({
      usage: {
        primaryRemainingPercent: 82,
        secondaryRemainingPercent: null,
      },
    });

    render(<AccountListItem account={account} selected={false} onSelect={vi.fn()} />);

    expect(screen.getByTestId("mini-quota-track")).toHaveClass("bg-muted");
    expect(screen.queryByTestId("mini-quota-fill")).not.toBeInTheDocument();
  });

  it("renders quota fill when secondary remaining percent is available", () => {
    const account = createAccountSummary({
      usage: {
        primaryRemainingPercent: 82,
        secondaryRemainingPercent: 73,
      },
    });

    render(<AccountListItem account={account} selected={false} onSelect={vi.fn()} />);

    expect(screen.getByTestId("mini-quota-fill")).toHaveStyle({ width: "73%" });
  });

  it("renders upstream and internal identifiers separately when requested", () => {
    const account = createAccountSummary({
      accountId: "4a00521f-1111_b5dfc0ba__copy2",
      upstreamAccountId: "4a00521f-1111-2222-3333-444455556666",
      email: "same@example.com",
      displayName: "same@example.com",
    });

    render(<AccountListItem account={account} selected={false} showAccountId onSelect={vi.fn()} />);

    expect(screen.getByText(/Upstream/)).toBeInTheDocument();
    expect(screen.getByText(/Internal/)).toBeInTheDocument();
  });
});
