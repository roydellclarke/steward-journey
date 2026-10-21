// The three-question read: the smallest honest thing StewardPath can tell a
// stranger about their own business, with no account, no payment, and no email.
//
// Two rules govern this file.
//  1. Deterministic. Every word an owner reads is chosen here, by the options
//     they picked. Nothing is generated and nothing is inferred.
//  2. Honest about its own limits. Three answers cannot produce a readiness
//     score, so this never shows one. It names the heaviest pressure point and
//     then says plainly what it cannot see. The full program asks 38 questions.

export const QUICK_QUESTIONS = [
  {
    id: "dependency",
    area: "How much runs through you",
    prompt: "You are out for a month starting tomorrow, with no warning. What happens?",
    why: "A buyer prices this first, and your family feels it every day.",
    options: [
      { value: "stops", label: "Most of it stops until I get back", weight: 1 },
      { value: "limps", label: "It limps along, and I come home to a mess", weight: 2 },
      { value: "holds", label: "My people hold it together for a month", weight: 4 },
      { value: "runs", label: "It runs fine. Nobody panics", weight: 5 }
    ]
  },
  {
    id: "books",
    area: "Financial clarity",
    prompt: "Could you hand a careful buyer three clean years of books next week?",
    why: "This is the first thing anyone serious asks to see.",
    options: [
      { value: "head", label: "No. A lot of it lives in my head", weight: 1 },
      { value: "months", label: "Not next week. Give me a few months and my accountant", weight: 2 },
      { value: "mostly", label: "Mostly. A few things would need explaining", weight: 4 },
      { value: "ready", label: "Yes. They are clean and they are ready", weight: 5 }
    ]
  },
  {
    id: "successor",
    area: "Who comes next",
    prompt: "If you stepped back next year, does anyone know who would take over?",
    why: "Naming a possibility is not a promise to anyone.",
    options: [
      { value: "nobody", label: "No one. That is the part I avoid", weight: 1 },
      { value: "unsaid", label: "I have a name in mind. I have not said it out loud", weight: 2 },
      { value: "few", label: "A few people could. I have not chosen", weight: 3 },
      { value: "known", label: "Yes, and they know it", weight: 5 }
    ]
  }
];

// What the owner sees, keyed to the area and how heavy the answer is. Written
// to be true at every level: a strong answer still gets a next step, because
// nobody finishes this page believing they are done.
const READOUTS = {
  dependency: {
    low: {
      headline: "Most of this business is still you.",
      body: "A buyer reads that as risk and pays for it in the price. It is also the one thing that moves the most when you work on it, and you can start this month by writing down what only you know."
    },
    mid: {
      headline: "Your people can carry it for a while.",
      body: "That is further along than most owners get. The question a careful buyer asks next is what happens in month three, not month one."
    },
    high: {
      headline: "It runs without you.",
      body: "That is the rarest answer on this page. Your work now is proving it to someone else on paper, because a buyer believes records, not reassurance."
    }
  },
  books: {
    low: {
      headline: "Your books are not ready for a stranger to read.",
      body: "Every week of cleanup now is a week a buyer does not spend doubting you. Of the five areas, this one usually costs the least to fix and the most to leave alone."
    },
    mid: {
      headline: "Your books would hold up, with some explaining.",
      body: "Explaining is the part that costs you. Write down the handful of things you would have to say out loud, and the conversation stops being a negotiation about trust."
    },
    high: {
      headline: "Your books are ready.",
      body: "That clears the question most owners stall on. It also means the harder questions, the ones about people and timing, are the ones standing between you and a clean handoff."
    }
  },
  successor: {
    low: {
      headline: "Nobody knows who comes next, including you.",
      body: "That is the most common answer owners give, and the heaviest one to carry by yourself. Listing who could do it is not a promise to anyone, and it is the first step out of the fog."
    },
    mid: {
      headline: "You have someone in mind and you have not said it.",
      body: "The silence has a cost. Until you weigh that person against what you refuse to lose, you are protecting a hope rather than making a choice."
    },
    high: {
      headline: "Someone knows they are next.",
      body: "You are past the question that stops most owners. What remains is the handover itself: what they need to learn, in what order, and by when."
    }
  }
};

// The areas three questions never touch. Named plainly, because the honest
// pitch for the full program is the size of this list.
export const UNSEEN = [
  "What is written down, and what still lives only in your head",
  "Whether your family agrees on any of this",
  "How ready you feel, honestly, to let go",
  "What you refuse to lose, in your own words"
];

function band(weight) {
  if (weight <= 2) return "low";
  if (weight <= 4) return "mid";
  return "high";
}

// Lowest answer wins. A tie goes to the earlier question, which orders the
// areas by how much they move a handoff: dependency, then books, then
// succession.
export function readFrom(answers) {
  const scored = QUICK_QUESTIONS.map((question) => {
    const chosen = question.options.find((option) => option.value === answers[question.id]);
    return { question, option: chosen, weight: chosen ? chosen.weight : null };
  });
  if (scored.some((entry) => entry.weight === null)) return null;

  const pressure = scored.reduce((worst, entry) => (entry.weight < worst.weight ? entry : worst));
  const readout = READOUTS[pressure.question.id][band(pressure.weight)];

  return {
    pressureArea: pressure.question.area,
    headline: readout.headline,
    body: readout.body,
    // Every area touched, so the owner sees the whole of what they just told
    // us, not only the worst part.
    areas: scored.map((entry) => ({
      area: entry.question.area,
      answer: entry.option.label,
      weight: entry.weight,
      isPressure: entry.question.id === pressure.question.id
    })),
    unseen: UNSEEN
  };
}
