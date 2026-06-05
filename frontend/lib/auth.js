import { apiFetch } from "./api";

// Passwordless email auth. The owner proves they control an email with a
// one-time code (primary) or the magic link in the same email (fallback).
export const authApi = {
  // Ask for a code + link at a gate ("save" to resume later, "report" to open the report).
  request: (email, projectId, gate) =>
    apiFetch("/auth/request", { method: "POST", body: JSON.stringify({ email, projectId, gate }) }),

  // Verify the typed code. On success the backend sets the session cookie.
  verify: (email, code) =>
    apiFetch("/auth/verify", { method: "POST", body: JSON.stringify({ email, code }) }),

  // Look at a magic-link token without consuming it (for the landing page).
  peekLink: (token) => apiFetch(`/auth/confirm?token=${encodeURIComponent(token)}`),

  // Explicit click that consumes the magic link and signs the owner in.
  confirmLink: (token) =>
    apiFetch("/auth/confirm", { method: "POST", body: JSON.stringify({ token }) }),

  // Who am I, if anyone. Safe to call when signed out (returns authenticated: false).
  me: () => apiFetch("/auth/me"),

  logout: () => apiFetch("/auth/logout", { method: "POST" })
};
