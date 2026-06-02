const scripts = [
  {
    title: "Ideal customer",
    body: "Founder-led businesses with 10-100 employees where the owner is 55+, cares about employees and reputation, has no clear successor, is privacy-sensitive, and wants to prepare before buyers define the terms."
  },
  {
    title: "Advisor outreach",
    body: "I built a private, guided readiness program for owner clients who aren't ready for a broker conversation yet. It accompanies them through naming what must be protected, where the business depends too much on them, and what to prepare — then hands you an advisor-ready brief. Could I show you a sample for one owner profile?"
  },
  {
    title: "Seller-facing email",
    body: "Before you sell, decide what must be protected. StewardPath walks privately with you — a guided readiness check, a score you actually understand, and a plan you can return to — before a buyer controls the conversation. Private by default, and never used to train AI."
  },
  {
    title: "LinkedIn DM",
    body: "I'm testing a private readiness program for founder-led owners — built for people who care about employees, customers, and legacy, not just price. It listens and reflects back what you share, and you control what's ever revealed. Would a sample be useful for you or one client?"
  },
  {
    title: "Local workshop title",
    body: "Before You Sell: What Every Business Owner Should Protect — and Prepare — Before Talking To Buyers"
  },
  {
    title: "Flyer copy",
    body: "Thinking about stepping back someday? Don't let the first serious buyer define the future of your business. Prepare privately, at your pace, with a readiness program that accompanies you — and a person when you want one."
  },
  {
    title: "Trust & privacy line",
    body: "Private by default. Nothing is shared with employees, family, or buyers unless you choose to. Your answers are never used to train AI, and you can export or delete everything anytime."
  },
  {
    title: "Pricing test",
    body: "Free sample report, $249 owner readiness report, $1,500 concierge readiness package (guided intake + a private review with a person), and $199/month advisor pilot for up to 10 owner clients."
  }
];

export default function GoToMarketPage() {
  return (
    <main className="publicShell">
      <section className="publicHero">
        <div>
          <p className="publicEyebrow">Go-to-market support</p>
          <h1>Start with trusted advisors. Let the program accompany the owner.</h1>
          <p>
            With limited budget, begin where trust already exists: CPAs, exit
            planners, estate attorneys, wealth advisors, and community banks.
            The pitch isn't a report — it's a private program that listens,
            keeps the owner in control of what's shared, and prepares them for
            the advisor conversation. Use the public page as the proof they can
            forward to owners.
          </p>
          <div className="publicActions">
            <a href="/" className="primaryCta">View public page</a>
            <a href="/intake" className="primaryCta">Open the readiness program</a>
            <a href="/readiness">Classic workbench</a>
          </div>
        </div>
      </section>
      <section className="publicBand">
        <div className="publicGrid">
          {scripts.map((script) => (
            <article key={script.title}>
              <strong>{script.title}</strong>
              <p>{script.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
