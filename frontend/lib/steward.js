// The person behind StewardPath.
//
// The public pages promise "a real person" more than once. An owner deciding
// whether to type their life's work into a website wants to see who that is.
// Nothing here is invented: fill these fields with the real person, or leave
// `name` empty and the card does not render at all. Never put a stock photo,
// a made-up advisor, or a borrowed credential in this file.
//
// To turn the card on:
//   1. Set name, role, and words below.
//   2. Drop a real photo at frontend/public/img/steward.jpg (square, 600px+),
//      or leave `photo` empty for initials in place of a picture.
//   3. Set `email` to an address a person actually reads.

export const STEWARD = {
  name: "",
  role: "",
  words: "",
  photo: "",
  email: ""
};

export const STEWARD_READY = Boolean(STEWARD.name && STEWARD.role && STEWARD.words);
