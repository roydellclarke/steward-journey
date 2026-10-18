// Single source of truth for the answer/guide pages. Each guide is authored
// once as structured content here, then rendered two ways with no drift:
//  - human HTML at /content/<slug>            (app/content/[slug]/page.jsx)
//  - raw Markdown at /content/<slug>.md        (served for LLMs and agents)
// Writing follows the StewardPath laws: plain, warm, no em-dashes.

export const CONTENT = {
  "trades-readiness": {
    slug: "trades-readiness",
    eyebrow: "Guide for trades owners",
    // ISO dates feed Article datePublished/dateModified. Bump dateModified
    // when you revise the guide so search and AI engines see it as current.
    datePublished: "2026-06-24",
    dateModified: "2026-06-24",
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
  },

  // The moment pages. Each one is titled with the sentence an owner says to
  // themself, because that is what they type into a search box and what an
  // advisor repeats when they send the link. quickRead puts the three-question
  // card on the page, so a reader who recognizes themself gets something true
  // before anyone asks who they are.
  "offer-on-the-table": {
    slug: "offer-on-the-table",
    eyebrow: "When an offer arrives",
    datePublished: "2026-10-18",
    dateModified: "2026-10-18",
    quickRead: true,
    door: "Someone offered to buy my business.",
    title: "Someone offered to buy my business. What should I do first?",
    description:
      "An unsolicited offer is a starting point, not a price. What to check, what to get ready, and who to call, in the week after the call.",
    intro:
      "The call comes out of nowhere. A competitor, a broker, or a buyer you have never heard of wants to talk about your company. Your first instinct is to feel flattered, or to say no and hang up. Both are reactions. This guide is for the week after that call. It is preparation, not advice, and it tells you when to bring in the people who do the legal, tax, and valuation work.",
    sections: [
      {
        heading: "Should I answer an unsolicited offer right away?",
        body: [
          "No. Thank them, tell them you are not running a process, and ask them to put in writing what they have in mind. That one sentence costs you nothing and buys you weeks.",
          "The person calling you has done this many times. You have likely done it never. Owners who prepare first do better than owners who answer fast, and the gap is not small."
        ]
      },
      {
        heading: "Is the number they mentioned a real price?",
        body: [
          "Usually it is a range built on assumptions nobody has tested. It moves once they see your books, your customer list, and how much of the daily work runs through you.",
          "You do not need a valuation to get ready. You need to know what they will find when they look. A careful buyer checks the same handful of things every time, and you can check them yourself first."
        ]
      },
      {
        heading: "What should I have ready before I talk terms?",
        body: [
          "Three things, in this order. How much of the business depends on you personally. What your books show without you there to explain them. What you refuse to give up, written in your own words.",
          "The third one surprises owners. It is also the one that protects you later, when the offer looks good and the terms turn complicated."
        ]
      },
      {
        heading: "How do I keep my employees from hearing about this too early?",
        body: [
          "Say nothing you are not ready to repeat. Early talks fall apart often, and a crew that heard a rumor does not unhear it. Keep the circle to people who have a reason to be in it.",
          "Your answers here stay private by default. Nothing reaches your family, your employees, or a buyer unless you choose to share it."
        ]
      },
      {
        heading: "Who should I call first: my CPA, a lawyer, or a broker?",
        body: [
          "Your CPA, and walk in with something written. An advisor handed a partial picture late spends billable hours assembling what you already knew.",
          "A broker works for the transaction. Call one when you have decided you want a process, not before. StewardPath builds the summary you hand your advisor, from what you told us and nothing else."
        ]
      }
    ],
    cta: {
      text: "See where you stand before you call them back. Free to start, private by default.",
      href: "/intake"
    }
  },

  "no-one-to-hand-it-to": {
    slug: "no-one-to-hand-it-to",
    eyebrow: "When the family says no",
    datePublished: "2026-10-18",
    dateModified: "2026-10-18",
    quickRead: true,
    door: "My children do not want it.",
    title: "My children do not want the business. What happens now?",
    description:
      "What it means when the next generation says no, how to be sure they mean it, and who else could carry the work forward.",
    intro:
      "You may have built it partly for them. Now they have said no, or they have said nothing for years, which is its own answer. This is the quietest grief in business and almost nobody says it out loud. Here is what owners in your spot do next.",
    sections: [
      {
        heading: "Is it a failure if my kids do not want it?",
        body: [
          "No. A business that needed one particular child to survive was always fragile. The work you did is still the work you did, and it can carry on in hands that are not theirs.",
          "Most owners feel the sting anyway. Name it, then keep moving. The decision in front of you does not ask you to feel fine about it first."
        ]
      },
      {
        heading: "How do I know whether they really mean it?",
        body: [
          "Ask once, plainly, and ask about the work rather than the title. Not whether they want the company, but whether they want to run the crew, do the quoting, and answer the phone at six in the morning.",
          "A soft no usually means they do not want your job. A hard no means they do not want your life. You can plan around either one."
        ]
      },
      {
        heading: "Who else could take it on?",
        body: [
          "Four kinds of people, in most cases. A key employee who already knows the work. A manager who could run it with support. An outside operator looking for a business like yours. A competitor who wants your customers.",
          "Each one protects something different and costs you something different. The right answer fits what you refuse to lose. It is not automatically the one with the biggest number attached."
        ]
      },
      {
        heading: "How do I bring this up at the family table?",
        body: [
          "Separate the money talk from the work talk. Children who do not want to run it often still care what happens to the people in it, and they usually have a view about the name.",
          "Go in with something written. A short page about what matters to you turns a loaded conversation into something everyone can read and react to."
        ]
      },
      {
        heading: "What if I wait and hope they change their mind?",
        body: [
          "Waiting is a choice and it has a price. Every year you carry the business alone is a year the people who could carry it look somewhere else.",
          "You can prepare a handoff and still leave the door open. Those two do not fight each other."
        ]
      }
    ],
    cta: {
      text: "See who could carry it forward, weighed against what you refuse to lose.",
      href: "/intake"
    }
  },

  "cannot-step-away": {
    slug: "cannot-step-away",
    eyebrow: "When it all runs through you",
    datePublished: "2026-10-18",
    dateModified: "2026-10-18",
    quickRead: true,
    door: "I cannot take two weeks off.",
    title: "I cannot take two weeks off. How do I fix that before I sell?",
    description:
      "Why how much runs through you sets your price, what to write down first, how to move customers off your name, and how long the work takes.",
    intro:
      "You have not taken a real vacation in years. If you leave, calls go unanswered, quotes sit, and something breaks. Owners mention this with a shrug, as though it were a personality trait. A buyer reads it as the largest risk in the company and prices it that way. Here is the better news: this is the gap that moves the most when you work on it.",
    sections: [
      {
        heading: "Why does a buyer care whether I can take a vacation?",
        body: [
          "Because they are buying what happens after you leave. If the business needs you on the phone, they are buying a job, and they pay what a job is worth.",
          "Of the five areas we score, this is the one where a few months of work changes what someone will pay. It moves further than any of the others."
        ]
      },
      {
        heading: "What should I write down first?",
        body: [
          "Start with what only you know. How you price a job. Which customers call you directly. What you do when a big one goes wrong. Who you call when a machine dies on a Friday afternoon.",
          "An hour a week for a season covers more than owners expect. You are not writing a manual. You are emptying your head onto paper where someone else can reach it."
        ]
      },
      {
        heading: "How do I move customer relationships off my name?",
        body: [
          "Bring someone with you, then let them take the next call. The first few feel like a downgrade to the customer, so say out loud who is looking after them now and why you trust that person.",
          "Buyers test this directly. They ask which customers buy because of the company and which buy because of you."
        ]
      },
      {
        heading: "How long does this take?",
        body: [
          "Most owners see real movement in six to twelve months, and the first signs show up sooner. You are not rebuilding the company. You are making it readable to someone who is not you.",
          "A score that climbs as you finish steps keeps the work visible, which matters when the work is slow and nobody is clapping."
        ]
      },
      {
        heading: "What if nobody on my team is ready?",
        body: [
          "That is information, not a dead end. A thin bench is a hiring and training plan, and a buyer will ask about it either way, so you are better off finding it first.",
          "Some owners pick a path that does not need a deep bench at all. Knowing which owner you are is the point of getting ready."
        ]
      }
    ],
    cta: {
      text: "See how much still runs through you, and what to fix first.",
      href: "/intake"
    }
  },

  "three-years-out": {
    slug: "three-years-out",
    eyebrow: "When the date is set",
    datePublished: "2026-10-18",
    dateModified: "2026-10-18",
    quickRead: true,
    door: "I want out in about three years.",
    title: "I want to retire in about three years. Where do I start?",
    description:
      "A plain order of operations for an owner with a three-year horizon: the first ninety days, the second year, when to bring in a professional, and what to do if the date moves.",
    intro:
      "Three years sounds like plenty until you count backwards. The work that raises what a business is worth takes twelve to eighteen months to show, and the work on the deal itself takes most of a year after that. Here is the order most owners wish they had used.",
    sections: [
      {
        heading: "Is three years enough time?",
        body: [
          "Yes, and it is close to the minimum for doing this on your terms instead of someone else's. Owners who start a year out tend to take the first reasonable offer, because they have run out of room to say no.",
          "Room to say no is the whole asset. Everything below protects it."
        ]
      },
      {
        heading: "What should I do in the first ninety days?",
        body: [
          "Three things, none of which involve a buyer. See where you stand across the five areas. Write down what you refuse to lose. Start emptying your head onto paper.",
          "None of this commits you to selling. Owners who decide to stay end up with a business that runs better and a plan their family can read."
        ]
      },
      {
        heading: "What should I do in the second year?",
        body: [
          "Close the gaps you found, starting with what a buyer looks at first. Clean the books. Reduce how much runs through you. Build the bench, or decide to sell to someone who brings their own.",
          "This is also the year to weigh the paths honestly: family, a key employee, an outside operator, a competitor. Rule out the ones you would never accept, and stop spending thought on them."
        ]
      },
      {
        heading: "When do I bring in a CPA or an attorney?",
        body: [
          "Bring your CPA in early, in the first year, with something written in your hand. Bring an attorney in when you are getting ready to talk to a particular buyer.",
          "StewardPath does not do the legal, tax, or valuation work and will not pretend to. It prepares the summary you hand to the people who do."
        ]
      },
      {
        heading: "What if my timeline changes?",
        body: [
          "It often does. Health, a good offer, or one tired year can move the date. A plan you keep beats a date you set.",
          "The work does not expire either. An owner who got ready and then stayed another five years still owns a business that runs without them."
        ]
      }
    ],
    cta: {
      text: "Start the ninety-day work. The check is free, and it saves where you left off.",
      href: "/intake"
    }
  }
};

export const CONTENT_SLUGS = Object.keys(CONTENT);

// The moment pages, in the order an owner is most likely to be living one.
// `door` is the sentence an owner says to themself, which is what gets typed
// into a search box and what an advisor repeats when they send the link.
export const MOMENTS = Object.values(CONTENT)
  .filter((entry) => entry.door)
  .map((entry) => ({ slug: entry.slug, door: entry.door, title: entry.title }));

export function getContent(slug) {
  return CONTENT[slug] || null;
}

// FAQ entities for a schema.org FAQPage, built from the question-shaped
// section headings. The guides are authored as the questions owners ask, so
// every section maps cleanly to a Question/Answer pair for AI extraction.
export function faqEntities(slug) {
  const c = getContent(slug);
  if (!c) return [];
  return c.sections
    .filter((s) => (s.body || []).length)
    .map((s) => ({
      "@type": "Question",
      name: s.heading,
      acceptedAnswer: { "@type": "Answer", text: (s.body || []).join(" ") }
    }));
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
