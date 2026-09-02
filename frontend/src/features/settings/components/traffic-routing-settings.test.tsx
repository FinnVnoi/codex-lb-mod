import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TrafficRoutingSettings } from "@/features/settings/components/traffic-routing-settings";
import { buildSettingsUpdateRequest } from "@/features/settings/payload";
import { createDashboardSettings } from "@/test/mocks/factories";

if (!HTMLElement.prototype.hasPointerCapture) {
  HTMLElement.prototype.hasPointerCapture = () => false;
}
if (!HTMLElement.prototype.setPointerCapture) {
  HTMLElement.prototype.setPointerCapture = () => undefined;
}
if (!HTMLElement.prototype.releasePointerCapture) {
  HTMLElement.prototype.releasePointerCapture = () => undefined;
}

const BASE_SETTINGS = createDashboardSettings({
  globalApiRoutingOverride: "normal",
  providerFailurePolicy: "account_after_first_failure",
  accountFailurePolicy: "accounts_before_providers",
  providerMaxAttempts: 3,
  accountMaxAttempts: 3,
});

const BASE_PAYLOAD = buildSettingsUpdateRequest(BASE_SETTINGS, {});

describe("TrafficRoutingSettings", () => {
  it("updates the global API routing override", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(<TrafficRoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />);

    await user.click(screen.getByRole("combobox", { name: "Global API routing override" }));
    await user.click(screen.getByRole("option", { name: "Provider first" }));

    expect(onSave).toHaveBeenCalledWith({
      ...BASE_PAYLOAD,
      globalApiRoutingOverride: "provider_first",
    });
  });

  it("clamps max attempts to the backend contract range", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(<TrafficRoutingSettings settings={BASE_SETTINGS} busy={false} onSave={onSave} />);

    await user.clear(screen.getByRole("spinbutton", { name: "Provider max attempts" }));
    await user.type(screen.getByRole("spinbutton", { name: "Provider max attempts" }), "11");

    expect(onSave).toHaveBeenLastCalledWith({
      ...BASE_PAYLOAD,
      providerMaxAttempts: 10,
    });
  });
});
