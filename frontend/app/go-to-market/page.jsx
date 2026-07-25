const scripts = [
  {
    title: "Ideal customer",
    body: "Founder-led businesses with 10 to 100 workers. The owner is 55 or older, cares about their people and their good name, has no clear next owner, and values privacy. They want to get ready before a buyer sets the terms."
  },
  {
    title: "Advisor outreach",
    body: "I built a private readiness program for owner clients who aren't ready for a broker yet. It walks them through what to protect and where the business leans too much on them, then hands you a ready-to-use summary. Could I show you a sample?"
  },
  {
    title: "Seller-facing email",
    body: "Decide what you protect before a buyer decides for you. StewardPath works through it with you in private: a guided check, a score you can read, a plan you return to. You walk in ready, while the terms are still yours to set. Private by default. Never used to train AI."
  },
  {
    title: "LinkedIn DM",
    body: "I'm testing a private readiness program for founder-led owners. It's built for people who care about their team, their customers, and their legacy, not just price. It listens, shows you what it heard, and keeps you in control of what anyone sees. Useful for you or a client?"
  },
  {
    title: "Local workshop title",
    body: "Before You Sell: What Every Owner Should Protect and Prepare Before They Talk to Buyers"
  },
  {
    title: "Flyer copy",
    body: "Thinking about stepping back one day? Don't let the first serious buyer decide your company's future. Prepare in private, at your own pace, with a program that stays with you and a real person when you want one."
  },
  {
    title: "Trust and privacy line",
    body: "Private by default. We share nothing with employees, family, or buyers unless you choose. We never use your answers to train AI. Export or delete everything anytime."
  },
  {
    title: "Pricing test",
    body: "Free sample. $249 Owner Readiness Program, a guided walk to a confident handoff. $1,500 concierge package with a guided intake and a private review. $199 a month for an advisor pilot of up to ten clients."
  }
];

export default function GoToMarketPage() {
  return (
    <main className="publicShell">
      <section className="publicHero">
        <div>
          <p className="publicEyebrow">Go-to-market support</p>
          <h1>Start where trust already lives. Let the program prepare the owner.</h1>
          <p>
            On a tight budget, start where trust already exists: CPAs, exit
            planners, estate lawyers, wealth advisors, and community banks. The
            pitch is not a report. It is a private program that listens, keeps
            the owner in control of what they share, and gets them ready for the
            advisor meeting. Use the public page as proof they can forward.
          </p>
          <div className="publicActions">
            <a href="/" className="primaryCta">View public page</a>
            <a href="/intake" className="primaryCta">Open the readiness program</a>
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
