import type { FeintEvent } from "../../lib/types";
import { EventCard } from "./EventCard";

interface Props {
  events: FeintEvent[];
  onSelect: (event: FeintEvent) => void;
}

export function EventFeed({ events, onSelect }: Props) {
  if (events.length === 0) {
    return <div className="muted">No events match the current filters.</div>;
  }
  return (
    <div>
      {events.map((e) => (
        <EventCard key={e.id} event={e} onClick={() => onSelect(e)} />
      ))}
    </div>
  );
}
