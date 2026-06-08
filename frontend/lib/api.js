export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiFetch(path, options = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    // Send the HttpOnly session cookie so authenticated owners stay signed in.
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

// Start a Stripe Checkout for one of the three paid products ("report",
// "concierge", "advisor") and send the browser to Stripe's hosted page.
export async function startCheckout(product, projectId = null) {
  const { url } = await apiFetch("/checkout", {
    method: "POST",
    body: JSON.stringify({ product, projectId })
  });
  if (!url) throw new Error("Checkout could not start. Please try again.");
  window.location.href = url;
}

export function toSnakeProfile(profile) {
  return {
    business_name: profile.businessName || "",
    industry: profile.industry || "",
    years_operating: Number(profile.yearsOperating || 0),
    employees: Number(profile.employees || 0),
    revenue_range: profile.revenueRange || "",
    profit_margin: profile.profitMargin || "",
    owner_dependency: profile.ownerDependency || "",
    timeline: profile.timeline || "",
    owner_goal: profile.ownerGoal || "",
    fears: profile.fears || "",
    non_negotiables: profile.nonNegotiables || "",
    family_context: profile.familyContext || "",
    next_owner_traits: profile.nextOwnerTraits || ""
  };
}
