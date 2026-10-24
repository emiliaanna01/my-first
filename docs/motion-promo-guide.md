# Motion Promo — User Guide

> Source: Google Doc "Motion prompt skill"
> https://docs.google.com/document/d/13HUxIbnPr_gBO6rKI0Cbx2Zbka6-JP2B7etBri8ELdg

Turn your written script or a website into a finished promo film.

You describe your product in plain words. It comes back as a dark, neon, glass-and-light motion film, the register of an Apple product reveal crossed with synthwave. No timeline editor, no keyframes, no After Effects.

**You get two files every time:**
- **.mp4** — the finished film, ready to post.
- **.html** — an interactive player you can scrub frame by frame, and edit later.

*Works anywhere you use Claude — web, mobile, desktop or terminal. Use Opus 5.*

## Contents

- **Where it works** — Every Claude surface, why the model matters, and using it elsewhere
- **Install** — Two clicks, once
- **Make your first film** — What to say, which ratio, how long
- **What happens next** — The four stages, and how long they take
- **Writing a script that animates well** — The part that decides whether the film is good
- **Refining it** — Plain-language notes and what each one changes
- **What the films look like** — The visual language, and how your brand colour fits
- **Troubleshooting** — The eight things that actually go wrong
- **Questions** — Licensing, logos, music, length

## Where it works

| Where | How |
| --- | --- |
| claude.ai (web) | Install the skill, then just ask |
| Claude mobile app | Same |
| Claude Desktop → Cowork | Same |
| Claude Code (terminal) | Same |

### The model matters more than the platform

This is the one thing that genuinely changes your results. The skill describes a look in detail, but something still has to design, choose the beats, cut your script to five-word lines, judge the timing. Stronger models do that noticeably better.

> **Use the best model available to you.** On Claude that means Opus 5. Weaker models produce a recognisably similar film with clumsier pacing and flatter composition.

### What you get back

Both files, normally. If an environment can only produce one, it will be the **.html** — that file contains the entire animation as code and plays in any browser, so it is a finished deliverable on its own, not a preview. If you want the MP4 and did not get one, just ask for it.

## Install

1. Click the **motion-promo.skill** file you were sent.
2. Press **Save skill**.

That is it. The skill stays in your account across every session — you never install it again, and you never paste anything.

## Make your first film

Just talk. Do not mention the skill by name — it recognises what you are asking for.

### From a script

*(example missing in the source document)*

### From a website

*Turn meridian.app into a 30 second launch film, 16:9.*

> That is the whole brief. **Say the duration and the aspect ratio** — those are the only two things it cannot decide for you.

### Which ratio?

| Ratio | Size | For |
| --- | --- | --- |
| 9:16 | 1080 × 1920 | TikTok, Reels, Shorts, Stories |
| 1:1 | 1080 × 1080 | Feed posts, LinkedIn |
| 16:9 | 1920 × 1080 | Website hero, YouTube, decks |

### Which duration?

**15–20 seconds** is the sweet spot for social. **30 seconds** for a launch or a site hero. Under 12 seconds feels rushed; over 45 seconds needs a real narrative to justify itself.

## What happens next

1. **It writes a beat sheet.** The film broken into 4–7 timed beats, each with a shot type and the words on screen. This appears in the reply. Read it — if the story is wrong, say so now, before it builds.
2. **It builds and previews stills.** Checking composition before committing.
3. **It renders every frame and encodes.** This is the slow part.
4. **It hands you the MP4 and the HTML.**

> **How long:** a 20-second film is roughly 600 individually painted frames. Expect **five to fifteen minutes** end to end. It will be working the whole time — that is normal, not stuck.

## Writing a script that animates well

This matters more than anything else you do. The same tool produces a great film or a mediocre one depending on what you feed it.

- **Write for the ear, not the page.** Say what your product does the way you would say it to a friend. It cuts your words down to five-word lines — give it good raw material to cut from.
- **Four to six ideas, maximum.** A 20-second film holds about five beats. If your script has twelve points, it picks five and drops the rest. Better that you choose which five.
- **Lead with the sharpest line.** The first beat is the one people actually watch.
- **Kill the adjectives.** "Powerful, intuitive, best-in-class platform" gives it nothing to animate. "Deploy in nine seconds" does.
- **Numbers are gold.** Concrete figures get their own shot type — a big number slamming in with a bloom. "40% fewer meetings" will look better than any adjective you can write.

### Weak vs strong

**Weak**

*Meridian is a comprehensive, enterprise-grade scheduling solution that leverages intelligent algorithms to optimise calendar management across your organisation.*

**Strong**

*Meridian finds meeting times nobody hates. It reads every calendar in your team and picks the slot that costs the least. Cut 40% of your meetings. Free under ten people.*

The second has four clean beats in it. The first has none.

## Refining it

After the first cut, say what is wrong in plain language. It re-renders only the part you changed, so a single note takes about a minute rather than a full rebuild.

| You say | What changes |
| --- | --- |
| "Beat three is too fast" | That beat stretches, the rest holds |
| "Make it pop more" | Stronger glow swell, more colour movement |
| "Too busy" | Fewer objects per beat, longer holds |
| "Colder" / "warmer" | The palette's hue arc shifts |
| "It looks laggy" | An easing curve gets fixed |
| "Use our brand purple #6633EE" | Palette remaps around your colour |
| "Drop the search bar scene" | That beat is cut, timing redistributed |
| "Different opening" | It swaps the first shot type |

You can keep going as long as you like. Nothing is baked until you are happy.

## What the films look like

Every film is composed from the same visual language, so they stay consistent as a set:

- **Pure black backgrounds.** Never grey, never a dark wash.
- **Light is the subject.** Objects are dark matte glass; what you see is the light coming off and behind them.
- **A neon spectrum that travels** — cool cyan and blue at the open, violet through the middle, warm or magenta at the close.
- **One idea per beat,** big and centred. Never a busy composite.
- **Typing that flashes** — the last character typed lights up in an accent colour and cools to white.
- **Hard cuts,** camera push-ins, expanding rings, glass icon tiles, shockwaves.

Your brand colour is woven in rather than pasted on — it takes the hero slot in the palette, and the cool-to-warm progression is built around it.

## Troubleshooting

**"Nothing happened when I asked."**
Check the skill is installed — ask "what skills do I have?" If it is there, say what you want more explicitly: "use the motion promo skill to make a 20 second film from this."

**"I only got the HTML, no MP4."**
The HTML is a complete, finished animation — open it in any browser. If you want the video file too, just ask: "now render that to MP4."

**"The result looks flat compared to the examples."**
Almost always the model. Switch to the strongest one available and ask again. After that, tighten the script — see *Writing a script that animates well*.

**"It's been going for ten minutes."**
Normal. Rendering is hundreds of individual frames. It will say when it is done.

**"The MP4 won't play."**
It is H.264 in an MP4 — plays everywhere. If your player refuses, try VLC, or open the .html file in a browser instead.

**"It picked the wrong parts of my script."**
Tell it which beats you wanted. Or rewrite the script tighter and ask again — it can only choose from what you gave it.

**"The colours are wrong for my brand."**
Give it the hex codes: "use #6633EE and #00D4A0". It will remap the palette and keep the structure.

**"Can I edit it myself afterwards?"**
Yes. The .html file contains the entire animation as readable code. Open it in a text editor — the timeline and brand settings are at the top, in plain English.
