"use client";

import { useEffect, useRef } from "react";

// Accessibility for modal dialogs: focus trap, Escape to close, and focus
// restore to whatever opened the modal. Without this, keyboard and screen
// reader users can Tab out to the page behind an open dialog and lose their
// place. Pass a ref on the dialog container and the close handler.
export function useModalA11y(containerRef, onClose) {
  // Keep the latest onClose without re-running the setup effect (which would
  // re-steal focus on every parent render).
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const restoreRef = useRef(null);

  useEffect(() => {
    restoreRef.current = document.activeElement;
    const container = containerRef.current;
    if (!container) return undefined;

    const selector =
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const focusables = () =>
      Array.from(container.querySelectorAll(selector)).filter((el) => el.offsetParent !== null);

    // Move focus into the dialog when it opens. Prefer the first form field
    // (the thing the owner is meant to fill) over a leading close button.
    const items = focusables();
    const preferred = items.find((el) => /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) || items[0];
    if (preferred) preferred.focus();

    function onKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current?.();
        return;
      }
      if (event.key !== "Tab") return;
      const items = focusables();
      if (!items.length) return;
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      if (event.shiftKey && document.activeElement === firstEl) {
        event.preventDefault();
        lastEl.focus();
      } else if (!event.shiftKey && document.activeElement === lastEl) {
        event.preventDefault();
        firstEl.focus();
      }
    }

    container.addEventListener("keydown", onKeyDown);
    return () => {
      container.removeEventListener("keydown", onKeyDown);
      const toRestore = restoreRef.current;
      if (toRestore && typeof toRestore.focus === "function") toRestore.focus();
    };
    // containerRef is a stable ref object, so this runs once per open/close.
  }, [containerRef]);
}
