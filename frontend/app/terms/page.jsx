// Terms of Service, including payment, refunds, and cancellation. Plain
// language. Bracketed values are placeholders for the business to fill, and a
// lawyer should review before launch.

export const metadata = {
  title: "Terms",
  description: "The terms for using StewardPath, including payment, refunds, cancellation, and the limits of what StewardPath is.",
  alternates: { canonical: "/terms" }
};

export default function TermsOfService() {
  return (
    <main className="publicShell">
      <section className="publicBand legalDoc">
        <div>
          <p className="publicEyebrow">Terms</p>
          <h1>Terms of service</h1>
          <p className="legalMeta">Last updated [DATE]. These terms govern your use of StewardPath, operated by [COMPANY LEGAL NAME].</p>

          <p>
            By using StewardPath, you agree to these terms. Please read them. They
            explain what StewardPath is, what you pay, and how cancellations and
            refunds work.
          </p>

          <h2>What StewardPath is, and is not</h2>
          <p>
            StewardPath is educational preparation support for owners getting
            ready to sell, pass on, or step away from a business. It is not legal,
            tax, investment, valuation, or brokerage advice. It does not replace a
            professional. For decisions with legal or financial weight, work with
            a qualified advisor. We route regulated work to humans on purpose.
          </p>

          <h2>Your account</h2>
          <p>
            You sign in with a one-time code sent to your email. You are
            responsible for the email account you use. Tell us if you suspect
            someone else has access.
          </p>

          <h2>What you pay</h2>
          <p>The current options are:</p>
          <ul>
            <li>Sample: free.</li>
            <li>Owner Readiness Program: $249, a one-time payment.</li>
            <li>Concierge package: $1,500, a one-time payment that includes a private review with a person.</li>
            <li>Advisor pilot: $199 per month, billed monthly until you cancel.</li>
          </ul>
          <p>
            Prices are in US dollars and may change, though a change never affects
            a payment you have already made. Payments are processed securely by
            Stripe.
          </p>

          <h2>Cancellation and refunds</h2>
          <p>
            You can cancel the monthly advisor pilot at any time. Your access
            continues through the period you already paid for, and you are not
            charged again after you cancel.
          </p>
          <p>
            For one-time purchases, if StewardPath has not delivered what you paid
            for, or something went wrong on our side, contact us within [REFUND
            WINDOW, e.g. 14 days] and we will make it right, including a refund
            where fair. Because the program gives you access to prepared guidance
            right away, refunds are considered case by case once you have used it.
          </p>

          <h2>Acceptable use</h2>
          <p>
            Use StewardPath for your own preparation. Do not misuse it, try to
            break it, or use it to harm others.
          </p>

          <h2>Your data</h2>
          <p>
            Your privacy is covered by our <a href="/privacy">Privacy Policy</a>.
            In short: private by default, never used to train AI, and yours to
            export or delete anytime.
          </p>

          <h2>Disclaimers and liability</h2>
          <p>
            StewardPath is provided as is, without warranties. We are not liable
            for decisions you make from your preparation, and our liability is
            limited to the amount you paid us in the prior twelve months, to the
            extent the law allows.
          </p>

          <h2>Changes and contact</h2>
          <p>
            We may update these terms. If a change matters, we will say so here
            and, where it affects you, by email. Questions go to [CONTACT EMAIL].
            These terms are governed by the laws of [JURISDICTION].
          </p>
        </div>
      </section>
    </main>
  );
}
