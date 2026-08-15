import { describe, expect, it } from "vitest";
import { summarizeAnalyses } from "./analysis-utils";

describe("analysis summaries", () => {
  it("counts classifications and calculates risk statistics", () => {
    const summary = summarizeAnalyses([
      { classification: "SAFE", risk_score: 10, confidence: 0.8 },
      { classification: "LOW_RISK", risk_score: 40, confidence: 0.6 },
      { classification: "SUSPICIOUS", risk_score: 70, confidence: 0.9 },
      { classification: "PHISHING", risk_score: 95, confidence: 1 },
    ]);

    expect(summary.total).toBe(4);
    expect(summary.safe).toBe(1);
    expect(summary.spam).toBe(1);
    expect(summary.flagged).toBe(2);
    expect(summary.averageRisk).toBe(53.75);
    expect(summary.highestRisk).toBe(95);
  });

  it("handles empty history without producing invalid values", () => {
    const summary = summarizeAnalyses();
    expect(summary.total).toBe(0);
    expect(summary.averageRisk).toBe(0);
    expect(summary.averageConfidence).toBe(0);
    expect(summary.distribution.PHISHING).toBe(0);
  });
});
