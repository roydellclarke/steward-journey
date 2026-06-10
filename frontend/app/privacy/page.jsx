// Privacy Policy. Plain language for owners, true to how the product behaves
// (default-private, never used to train AI, export or delete anytime). Bracketed
// values are placeholders for the business to fill, and a lawyer should review
// before launch.

export const metadata = {
  title: "Privacy",
  description: "How StewardPath handles your information: private by default, never used to train AI, yours to export or delete anytime.",
  alternates: { canonical: "/privacy" }
};

export default function PrivacyPolicy() {
  return (
    <main className="publicShell">
      <section className="publicBand legalDoc">
        <div>
          <p className="publicEyebrow">Privacy</p>
          <h1>Your privacy, in plain terms</h1>
          <p className="legalMeta">Last updated [DATE]. This policy covers StewardPath, operated by [COMPANY LEGAL NAME].</p>

          <p>
            StewardPath helps you prepare to hand off your business. The work is
            personal, so we treat it that way. Your answers stay private by
            default, and you decide what is ever shared.
          </p>

          <h2>What we collect</h2>
          <p>
            We collect what you give us: the answers in your readiness program,
            your email address for sign-in, and the records you create as you
            prepare. When you pay, our payment processor handles your card. We
            never see or store full card numbers.
          </p>

          <h2>How we use it</h2>
          <p>
            We use your information to build your readiness, save your progress,
            send your sign-in codes and receipts, and support you if you ask. We
            do not sell your information. We never use your information to train
            artificial intelligence.
          </p>

          <h2>Who can see it</h2>
          <p>
            You can. By default, no one else does. If you book a review with a
            person, they see only what you choose to share. You control sharing
            at the section and field level, and you can change your mind.
          </p>

          <h2>Your controls</h2>
          <p>
            You can export everything we hold for you at any time. You can delete
            your data at any time, and deletion is final. We keep a small record
            that an action happened, with no sensitive details in it.
          </p>

          <h2>The services we rely on</h2>
          <p>
            We use a payment processor (Stripe) to take payments and an email
            provider to send your sign-in codes and receipts. They handle only
            what they need to do their job, under their own terms.
          </p>

          <h2>Security</h2>
          <p>
            Sign-in uses a one-time email code, so there is no password to leak.
            Sessions are signed, and access to your records is checked on every
            request. No system is perfect, and we will tell you promptly if a
            breach ever affects your data.
          </p>

          <h2>Keeping and deleting data</h2>
          <p>
            We keep your information while your account is active or as the law
            requires. When you delete it, we remove it from our systems. Backups
            age out on a rolling basis.
          </p>

          <h2>Children</h2>
          <p>StewardPath is for business owners and is not directed to children.</p>

          <h2>Changes and contact</h2>
          <p>
            If this policy changes in a way that affects you, we will say so here
            and, where it matters, by email. Questions about your privacy go to
            [PRIVACY CONTACT EMAIL].
          </p>
        </div>
      </section>
    </main>
  );
}
