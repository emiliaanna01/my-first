import Link from "next/link";

export default function NotFound() {
  return (
    <main id="main" className="site-main not-found">
      <div className="wrap">
        <p className="kicker">404, off the map</p>
        <h1 className="h1">This track does not go anywhere.</h1>
        <p className="lede">The page may have moved when we rebuilt the site. Try one of these.</p>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
          <Link className="btn" href="/">Back to the home page</Link>
          <Link className="ulink" href="/work">Case studies</Link>
          <Link className="ulink" href="/contact">Contact</Link>
        </div>
      </div>
    </main>
  );
}
