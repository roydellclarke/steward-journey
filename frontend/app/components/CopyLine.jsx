"use client";

import { useEffect, useState } from "react";
import "./copyline.css";

// A block of text an advisor can lift and paste into an email, with the link
// pointing wherever this page is actually served from. The server renders the
// configured site URL so the text is complete before JavaScript runs; after
// mount it switches to the real origin, which keeps the link right in every
// environment.
export default function CopyLine({ template, fallbackOrigin, label }) {
  const [origin, setOrigin] = useState(fallbackOrigin);
  const [state, setState] = useState("idle");

  useEffect(() => {
    if (typeof window !== "undefined") setOrigin(window.location.origin);
  }, []);

  const message = template.replace("{url}", origin);

  async function copy() {
    try {
      await navigator.clipboard.writeText(message);
      setState("copied");
    } catch {
      setState("blocked");
    }
  }

  return (
    <div className="copyLine">
      <p className="copyText">{message}</p>
      <div className="copyActions">
        <button type="button" onClick={copy}>{label}</button>
        {state === "copied" ? <span role="status">Copied. Paste it into an email.</span> : null}
        {state === "blocked" ? <span role="status">Copying is blocked here. Select the text and copy it by hand.</span> : null}
      </div>
    </div>
  );
}
