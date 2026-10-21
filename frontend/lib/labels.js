// Plain-English labels for every scored field the backend returns. Owner-facing
// copy never shows a raw field name or an internal framework label, so each map
// here is the single place a score name becomes words an owner would use.

// The five readiness areas. These match the wording already used in the
// program (app/intake/page.jsx) so a sample report and a real one read alike.
export const AREA_LABELS = {
  financial_clarity: "Financial clarity",
  operational_transferability: "How well it runs without you",
  process_documentation: "What's written down",
  family_alignment: "Family on the same page",
  owner_emotional_readiness: "Your readiness to step back"
};

// What a careful buyer studies. The backend groups these under an internal
// research label; owners see the plain question each one asks.
export const BUYER_VIEW_LABELS = {
  understandable_business: "Easy for an outsider to understand",
  founder_independence: "Runs without you",
  management_depth: "Strength of your bench",
  durable_customer_value: "Customers who stay",
  stewardship_fit: "Fit for a careful next owner"
};

// A 1 to 5 score, said out loud. Used for screen readers and for the small
// label beside each bar, so the number is never the only signal.
export const BAND_WORDS = ["", "thin", "early", "mixed", "solid", "strong"];

export function bandWord(score) {
  return BAND_WORDS[Math.max(1, Math.min(5, Math.round(score)))] || "mixed";
}
