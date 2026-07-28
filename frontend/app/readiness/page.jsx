import { redirect } from "next/navigation";

// The classic readiness workbench has been retired. It ran a second, client-side
// scoring engine on the flat owner profile and used an older design language.
// The guided /intake program is now the single, maintained readiness engine
// (structured IntakeState, grounded scoring on the backend), so anyone landing
// here goes there. History is preserved in git if the old view is ever needed.
export default function ReadinessRedirect() {
  redirect("/intake");
}
