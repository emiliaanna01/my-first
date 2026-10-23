# Round House: how a project moves

A 75 s product-walkthrough film in the style of inflight's launch video (whatships.com/videos/inflight),
told with Round House's design and services: one client's lead flow, from an unanswered inquiry to v2.

| Time | Scene | Voiceover |
|---|---|---|
| 0–7 s | Night: an 11:48 PM inquiry rolls to 8:30 AM, still unread, more pile up | "A new inquiry lands just before midnight…" |
| 7–22 s | Wordmark, then the site's own journey card rises as *prototype · v1*; New inquiry → Qualified → Booked light up | "…starting from a real, working prototype." |
| 22–36 s | Review toolbar; Maya pins a comment, records a walkthrough; notes sync into the team thread | "Pin a comment to the exact step…" |
| 36–48 s | Agent terminal pulls 3 next steps, ticks them off, waits for a human approval, "v2 is ready for review" | "Human judgment stays in the loop…" |
| 48–61 s | v2: repeat customer flagged, text reply sent, booking; then 43.3 hours back / month | "Less repetition. More room for better work." |
| 61–75.5 s | Diagnose. Build. Run. → wordmark, "Good ideas. Made real.", Let's talk | "Round House. Good ideas, made real. Let's talk." |

The prototype, pipeline, calculator and copy are the site's own DOM and CSS. The reviewers (Maya, Sam), the inquiry text and
the three next steps are illustrative, as the site labels these cards ("ILLUSTRATIVE CONCEPT", kept on screen).
The review toolbar, thread and terminal are drawn in Round House's style to show the process; they are not a Round House product.

Rebuild: `python3 build/build.py`, then `npx --prefix ../../motion hyperframes check` and `... render -q looks`,
then normalise with `ffmpeg -af "loudnorm=I=-15:TP=-2:LRA=11"`.
Voice: Kokoro `af_heart` at 0.92× (`build/vo.txt`). Music: "Inspiration profonde" (Monplaisir, CC0) at 0.10.
Effects: Mixkit, via video-shotcraft.
