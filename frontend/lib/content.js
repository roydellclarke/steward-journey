// Single source of truth for the answer/guide pages. Each guide is authored
// once as structured content here, then rendered two ways with no drift:
//  - human HTML at /content/<slug>            (app/content/[slug]/page.jsx)
//  - raw Markdown at /content/<slug>.md        (served for LLMs and agents)
// Writing follows the StewardPath laws: plain, warm, no em-dashes.

export const CONTENT = {
  "trades-readiness": {
    slug: "trades-readiness",
    title: "Selling or handing off a trades business, on your terms",
    description:
      "A plain guide for owners of HVAC, plumbing, electrical, and contracting businesses getting ready to sell, pass on, or step back. What buyers ask, how to reduce how much rides on you, and how to protect your crew and customers.",
    intro:
      "You built a trades business that runs on your name, your crew, and your word. When the calls come in from buyers, brokers, or a roll-up, the smart move is to get ready before they set the terms. This guide is for HVAC, plumbing, electrical, roofing, and general contracting owners. It is preparation, not advice, and it points you to a real person for the legal, tax, and valuation work.",
    sections: [
      {
        heading: "I got an offer for my contracting business. What do I do first?",
        body: [
          "Slow down before you answer. An unsolicited offer is a starting point, not a price. Owners who prepare first almost always do better than owners who react to the first number.",
          "Get clear on three things before you talk terms: how much the business depends on you, what your books really show, and what you refuse to give up in a sale. StewardPath walks you through all three in private, so you walk into the call ready instead of guessing."
        ]
      },
      {
        heading: "How much is my HVAC or trades business worth to a buyer?",
        body: [
          "Buyers in the trades look at recurring revenue, the size and loyalty of your crew, your service agreements, and how much the work depends on the owner. A book of maintenance contracts is worth more than one-off jobs.",
          "You do not need an exact number to get ready. You need to know where you stand and what a careful buyer will question. StewardPath gives you a readiness score across five areas, each with the reason behind it, so you see the gaps a buyer will see."
        ]
      },
      {
        heading: "The business depends on me. How do I fix that before I sell?",
        body: [
          "If you hold the key customer relationships, quote every big job, and keep the schedule in your head, a buyer sees risk and pays less. Reducing how much rides on you is the single biggest lever on your price.",
          "Start by writing down what only you know, training a lead tech or office manager to run the day to day, and moving customer relationships onto the company name instead of yours. StewardPath turns this into a short, prioritized plan, and your score climbs as you finish each step."
        ]
      },
      {
        heading: "How do I sell without hurting my crew and my customers?",
        body: [
          "For most trades owners this is the real worry, not the price. You want your techs to keep their jobs and your customers to keep getting good service.",
          "You can name what must be protected and weigh buyers by fit, not just by the size of the check. StewardPath has you list your non-negotiables, then ranks family, a key employee, a competitor, and an outside buyer by how well each fits what you value."
        ]
      },
      {
        heading: "Who should take over: a key tech, a competitor, or an outside buyer?",
        body: [
          "Each path trades off differently. A key employee keeps the culture but may not have the cash. A competitor pays for your customers but may cut your crew. An outside buyer or roll-up brings money and systems but may change the name and the way you work.",
          "There is no single right answer. The right answer is the one that fits what you refuse to lose. StewardPath scores each candidate against your values so you choose with clear eyes."
        ]
      },
      {
        heading: "What should I prepare before I call a CPA, attorney, or broker?",
        body: [
          "Arriving organized saves you money. When your books, your risks, and your goals are written down, the legal and accounting work runs faster, which can mean fewer billable hours.",
          "StewardPath produces briefs you can hand over: an advisor summary, a family guide, and a note on your preferred successor, built only from what you shared. You decide what to share and when."
        ]
      }
    ],
    cta: {
      text: "Start your private readiness check. It is free to see your score and your plan.",
      href: "/intake"
    }
  }
};

export const CONTENT_SLUGS = Object.keys(CONTENT);

export function getContent(slug) {
  return CONTENT[slug] || null;
}

// Render the same structured content to clean Markdown for the .md mirror.
export function toMarkdown(slug) {
  const c = getContent(slug);
  if (!c) return "";
  const lines = [`# ${c.title}`, "", `> ${c.description}`, "", c.intro, ""];
  for (const section of c.sections) {
    lines.push(`## ${section.heading}`, "");
    for (const para of section.body || []) lines.push(para, "");
    for (const bullet of section.bullets || []) lines.push(`- ${bullet}`);
    if (section.bullets?.length) lines.push("");
  }
  if (c.cta) lines.push(`---`, "", `${c.cta.text}`, "");
  return lines.join("\n");
}
