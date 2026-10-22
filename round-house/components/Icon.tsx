import type { IconName } from "@/lib/content";

const PATHS: Record<IconName, string> = {
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  doc: '<path d="M7 3.5h7l4 4V20a.5.5 0 0 1-.5.5h-10A.5.5 0 0 1 7 20z"/><path d="M14 3.5V8h4M9.5 12.5h5M9.5 16h5"/>',
  tag: '<path d="M3.5 12.2V4a.5.5 0 0 1 .5-.5h8.2l8.3 8.3-8.7 8.7z"/><circle cx="8" cy="8" r="1.4"/>',
  shield: '<path d="M12 3.2l7 2.8v5.5c0 4.3-3 7.6-7 9.3-4-1.7-7-5-7-9.3V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="M11 12.2l8.5-8.5M16.5 6.7l2.3 2.3M14.4 8.8l1.8 1.8"/>',
  gauge: '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/><circle cx="12" cy="17" r="1.2"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.6v.1"/>',
  arrowL: '<path d="M15 5l-7 7 7 7"/>',
  arrowR: '<path d="M9 5l7 7-7 7"/>',
  out: '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  map: '<path d="M4 6.5l5-2 6 2 5-2v13l-5 2-6-2-5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
  wrench: '<path d="M14.5 4.2a4.5 4.5 0 0 0-5.7 5.7L3.6 15.1a1.6 1.6 0 0 0 0 2.3l3 3a1.6 1.6 0 0 0 2.3 0l5.2-5.2a4.5 4.5 0 0 0 5.7-5.7l-3 3-3-.6-.6-3z"/>',
  pen: '<path d="M4 20l1-4.5L15.5 5a2.1 2.1 0 0 1 3 3L8 18.5z"/><path d="M13.5 7l3 3"/>',
};

export function Icon({ name, size }: { name: IconName; size?: number }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: PATHS[name] }}
    />
  );
}
