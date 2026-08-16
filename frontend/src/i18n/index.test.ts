import { describe, expect, it } from "vitest";

import i18n, { normalizeSupportedLanguage } from "@/i18n";

describe("normalizeSupportedLanguage", () => {
  it("keeps exact supported locales", () => {
    expect(normalizeSupportedLanguage("en")).toBe("en");
    expect(normalizeSupportedLanguage("vi")).toBe("vi");
  });

  it("normalizes detected regional locales to supported toggle values", () => {
    expect(normalizeSupportedLanguage("en-US")).toBe("en");
    expect(normalizeSupportedLanguage("vi-VN")).toBe("vi");
    expect(normalizeSupportedLanguage("zh-CN")).toBe("vi");
    expect(normalizeSupportedLanguage("ko-KR")).toBe("vi");
  });

  it("falls back to English for missing or unsupported locales", () => {
    expect(normalizeSupportedLanguage(undefined)).toBe("en");
    expect(normalizeSupportedLanguage("fr-FR")).toBe("en");
  });

  it("migrates removed Chinese detections to the Vietnamese resource", async () => {
    await i18n.changeLanguage(normalizeSupportedLanguage("zh"));

    expect(i18n.resolvedLanguage).toBe("vi");
  });
});
