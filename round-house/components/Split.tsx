import { Fragment, createElement, type ReactNode } from "react";

/** Renders a heading as masked words so the motion layer can raise them into place.
    The heading keeps its full text as its accessible name. */
export function SplitHeading({ as = "h2", text, className, id, children }: { as?: "h1" | "h2" | "h3"; text: string; className?: string; id?: string; children?: ReactNode }) {
  const words = text.split(" ");
  return createElement(
    as,
    { className, id, "aria-label": text, "data-split": "" },
    words.map((w, i) => (
      <Fragment key={i}>
        <span className="wm" aria-hidden="true"><span className="w">{w}</span></span>
        {i < words.length - 1 ? " " : null}
      </Fragment>
    )),
    children,
  );
}
