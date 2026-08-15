import { describe, expect, it } from "vitest";
import { riskStyle } from "./RiskScore";

describe("risk state presentation", () => {
  it.each([
    ["SAFE", "Safe"],
    ["LOW_RISK", "Low risk"],
    ["SUSPICIOUS", "Suspicious"],
    ["PHISHING", "Phishing"],
  ])("maps %s to a clear label", (classification, label) => {
    expect(riskStyle(classification).label).toBe(label);
  });

  it("uses a neutral state for unavailable classifications", () => {
    expect(riskStyle(undefined).label).toBe("Unknown");
    expect(riskStyle(undefined).tone).toBe("text-slate-300");
  });
});

