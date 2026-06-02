const scripts = [
  {
    title: "Ideal customer",
    body: "Founder-led businesses with 5-100 employees where the owner is 55+, cares about employees and reputation, has no clear successor, and wants to prepare before buyers define the terms."
  },
  {
    title: "Advisor outreach",
    body: "I built a private readiness report for business-owner clients who are not ready for a broker conversation yet. It helps them name what must be protected, where the business depends too much on them, and what to prepare before buyer conversations. Could I show you a sample report for one owner profile?"
  },
  {
    title: "Seller-facing email",
    body: "Before you sell, decide what must be protected. StewardPath helps you prepare a private readiness report around employees, customers, company name, financial clarity, and successor fit before a buyer controls the conversation."
  },
  {
    title: "LinkedIn DM",
    body: "I am testing a private transition-readiness report for founder-led business owners. It is built for owners who care about employees, customers, and legacy, not just price. Would a sample report be useful for you or one client?"
  },
  {
    title: "Local workshop title",
    body: "Before You Sell: What Every Business Owner Should Protect Before Talking To Buyers"
  },
  {
    title: "Flyer copy",
    body: "Thinking about stepping back someday? Do not let the first serious buyer define the future of your business. Prepare a private report on readiness, successor fit, and what must be protected."
  },
  {
    title: "Pricing test",
    body: "Free sample report, $249 owner readiness report, $1,500 concierge readiness package, and $199/month advisor pilot for up to 10 owner reports."
  }
];

export default function GoToMarketPage() {
  return (
    <main className="publicShell">
      <section className="publicHero">
        <div>
          <p className="publicEyebrow">Go-to-market support</p>
          <h1>Start with trusted advisors. Let the website support the seller.</h1>
          <p>
            With limited budget, begin where trust already exists: CPAs, exit
            planners, estate attorneys, wealth advisors, and community banks.
            Use the public page as the proof they can forward to owners.
          </p>
          <div className="publicActions">
            <a href="/" className="primaryCta">View public page</a>
            <a href="/mvp" className="primaryCta">Open readiness app</a>
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
