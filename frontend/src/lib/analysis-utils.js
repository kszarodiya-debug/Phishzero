export const CLASSIFICATIONS = ["SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"];

export function summarizeAnalyses(analyses = []) {
  const distribution = CLASSIFICATIONS.reduce((counts, classification) => {
    counts[classification] = 0;
    return counts;
  }, {});
  let riskTotal = 0;
  let confidenceTotal = 0;
  let scored = 0;
  let confident = 0;

  analyses.forEach((analysis) => {
    const classification = CLASSIFICATIONS.includes(analysis?.classification) ? analysis.classification : null;
    if (classification) distribution[classification] += 1;
    const risk = Number(analysis?.risk_score);
    if (Number.isFinite(risk)) {
      riskTotal += Math.max(0, Math.min(100, risk));
      scored += 1;
    }
    const confidence = Number(analysis?.confidence);
    if (Number.isFinite(confidence)) {
      confidenceTotal += Math.max(0, Math.min(1, confidence));
      confident += 1;
    }
  });

  const total = analyses.length;
  const flagged = distribution.SUSPICIOUS + distribution.PHISHING;
  return {
    total,
    safe: distribution.SAFE,
    spam: distribution.LOW_RISK,
    suspicious: distribution.SUSPICIOUS,
    phishing: distribution.PHISHING,
    flagged,
    distribution,
    averageRisk: scored ? riskTotal / scored : 0,
    averageConfidence: confident ? confidenceTotal / confident : 0,
    highestRisk: analyses.reduce((highest, analysis) => Math.max(highest, Number(analysis?.risk_score) || 0), 0),
  };
}

export function formatAnalysisDate(value, options = { dateStyle: "medium", timeStyle: "short" }) {
  if (!value) return "Unknown date";
  try {
    return new Intl.DateTimeFormat(undefined, options).format(new Date(value));
  } catch {
    return "Unknown date";
  }
}

export function formatClassification(classification) {
  return classification === "LOW_RISK" ? "LOW RISK" : String(classification || "UNKNOWN").replaceAll("_", " ");
}
