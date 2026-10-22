# Round House: launch + how-it-works film

GOAL:    A founder drowning in tools and admin understands in one minute what Round House does
         (connect thinking, systems and design) and wants to click "Let's talk".
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    58.8 s x 30 = 1764 frames. Music: Mixkit "House Vibez" (Lily J), 122.4 BPM, beat 0.49 s = 14.7 f,
         bar 1.96 s. Track enters at media 9.915 s so its first drop (track 15.795 s) hits film 5.88 s.
         Section C (track 46.775) = film 36.86, section E (track 63.005) = film 53.09.
REFS:    Burnwe 10Web + Opti, Innovid NIVO, Addx Texto, Zelios Supahub (the person's links):
         light warm grounds with one dark contrast world, real UI at 1.4-2x, a bold cursor whose click causes
         the next thing, state-morphing badges, 2-4 word kinetic lines, ~2 s per beat, tech-house bed.

LOOK:    Ground paper #f7f7f2 (hero), workflow #eef1e6, CTA lime #e5edcc, dark world #20271f.
         Ink #1d221e. Second-line sage #7d8c6a. Accent lime #e0ed9b, rationed: the active node, the recovered
         bars and $ value, the highlight under "real", the full stop of the wordmark.
         Display: Inter Tight Variable 550, tracking -0.055em, titles 96-150 px; hero words up to 210 px.
         Body/UI: DM Sans 400/500. All UI is the site's own DOM and CSS (site.css), never redrawn.
         Medium: the site itself, printed on paper: flat colour, no gradients, no glass, no glow.
         Shadows only the site's own. 3D: the hero spheres, captured from the live WebGL canvas (alpha WebM).
OBJECTS: the spheres (the brand's carrier: they absorb the clutter, they become the full stop);
         the cursor: macOS arrow, 60 px tall (5.6% of frame), white body, ink 2 px stroke, soft shadow;
         a click = cursor scales 0.82 for 3 f, the target presses (scale 0.96) and changes state that frame.
MOTION:  enter expo.out 0.6 s; camera power2.inOut 0.7 s; exits power3.in, 40% shorter than entrances;
         word stagger 0.07 s; cursor travel power3.inOut 0.55-0.8 s with a 1.5-2.5 px blur at peak;
         springs only on badges/icons (back.out(1.6)); titles land and hold dead still.
SHOTS:
 1  0.00-5.88   Dark world. "More software." on frame 0 with tool pills popping on every beat around it
                (pop x8, rotated takes); bar 2 "More back-and-forth."; bar 3 the pills are sucked into one
                lime sphere (whoosh), line becomes "Not another tool." + sage "A better way to work.";
                the sphere grows past the frame = colour flood to paper (object becomes the world).
 2  5.88-11.76  Drop. Paper. Hero: "Good ideas." / "Made real." per word blur-in, lime highlight wipes under
                "real", spheres (alpha video) rise in at right. Camera starts 1.35x on the title, pulls back to
                the full hero with header (wordmark seen inside the product). Cursor enters bottom-right,
                clicks "See what's possible" at 10.85 (click): the dark button zooms through to fill the frame.
 3  11.76-23.52 Dark ground from the button: "From first hello." / "To what's next." (ink-from-grey per word).
                Colour flood to #eef1e6 as the real workflow playground lands at 1.45x on its panel.
                Cursor clicks "Replay flow" (click): New inquiry -> Qualify & route -> Book a conversation light
                up in order, connectors draw, CONNECTED status (pop, sparkle, pop). Camera pulls back to the
                whole playground; cursor clicks tab "02 Internal AI assistants" (click): panel blur-swaps to
                that flow and it runs. Whip right into 4.
 4  23.52-31.36 Paper. "Find the right thing." / "Then make it work." Accordion Diagnose open; cursor clicks
                "Build" (click): Diagnose folds, Build unfolds, its three lines tick in; then "Run" (click).
                Camera push 1.0 -> 1.18 toward the rows. Hard cut on the last fold.
 5  31.36-43.12 Payoff. The calculator card (dark) at 1.1x: starts at 20 hrs / 10% (8.7 hrs back, 3 bars).
                Cursor grabs "Potential time reduction" and drags 10% -> 50%: bars fill lime one by one (soft
                ticks), 8.7 -> 43.3 hours, 1.1 -> 5.4 days, $346 -> $1,732 (all from the site's formula
                hours x pct x 4.33, x $40). Section C of the music at 36.86. Riser -> hit as 43.3 lands, camera
                punches in 1.1 -> 1.7 on "43.3 hours back / month" and holds.
 6  43.12-49.00 Claim on paper: "A clearer business." / "A more useful system." / "A brand with feeling."
                (the site's statement) one line per 1.4 s, ink-from-grey, sage second weight like the site.
 7  49.00-58.80 CTA lime ground: the site's "Let's talk." section; letters land one per 0.06 s, the arrow draws.
                Cursor clicks "Start a conversation" (click). At 53.09 (section E) a lime sphere drops into the
                full stop of "roundhouse." as the wordmark wipes in centred (riser -> impact), tagline
                "Good ideas. Made real." Hold 2.6 s, music fades 1.5 s.
BANNED:  dark void with small floating things (the dark world always holds full-size type or the card);
         glow, particles, gradients, glass; everything centred (titles sit left, like the site);
         fade-and-slide-up on every element; titles that drift after landing; three cards in a row;
         logo docked in a corner; invented dashboards (every UI is the site's); click rings.
QA:      0.0 (thumbnail: type + pills), 4.6 (sphere absorbs), 8.0 (hero), 10.9 (button click), 16.3 (nodes lit),
         19.6 (tab 2), 27.0 (Build open), 38.5 (bars filling), 40.5 (43.3 punch-in), 46.0 (claim), 54.5 (mark).
