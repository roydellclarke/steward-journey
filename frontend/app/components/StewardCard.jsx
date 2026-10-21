import { STEWARD, STEWARD_READY } from "../../lib/steward";
import "./steward.css";

// Renders nothing until a real person is filled into lib/steward.js. An empty
// card is better than an invented one.
export default function StewardCard() {
  if (!STEWARD_READY) return null;

  const initials = STEWARD.name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("");

  return (
    <aside className="stewardCard">
      {STEWARD.photo ? (
        <img className="stewardPhoto" src={STEWARD.photo} alt={STEWARD.name} width="96" height="96" />
      ) : (
        <span className="stewardPhoto stewardInitials" aria-hidden="true">{initials}</span>
      )}
      <div className="stewardBody">
        <p className="stewardWords">{STEWARD.words}</p>
        <p className="stewardWho">
          <strong>{STEWARD.name}</strong>
          <span>{STEWARD.role}</span>
          {STEWARD.email ? <a href={`mailto:${STEWARD.email}`}>{STEWARD.email}</a> : null}
        </p>
      </div>
    </aside>
  );
}
