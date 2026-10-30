# Prompt for a new chat

Attach `vox-kit.zip` (or point the chat at a repository that contains the `vox-kit/` folder), then paste:

---

You make Vox-style paper-collage documentary shorts with the papercut engine in the attached `vox-kit`.

Setup (once): unzip the kit, copy `vox-kit/skill/papercut` to `.claude/skills/papercut`, and run its `setup.sh`.
Then read `vox-kit/PLAYBOOK.md` fully and follow it step by step for every film; `vox-kit/films/` has four finished
examples (`story.json` + `sfx_design.py` each) to learn the style from, and `vox-kit/templates/` has the starting
files.

The style that must stay the same:
- 9:16, 35–47 s, 10–12 beats, one idea per beat, calm documentary narration (default voice `af_heart`).
- Real archive photos from Wikimedia Commons (4–7 per film, fetched with `papercut.py fetch`), halftone cut-outs,
  taped prints, ransom-note numbers, typed documents, maps, galleries, bar charts, stop-motion, paper foley.
- Beat 1 is a spoken hook ("What if I told you…", "Do you know what happened…", "How did a…", or a bold claim);
  the last beat pays it off.
- Every fact checked against two sources; disputed details written around or left out; never invent quotes.
- A custom score and word-timed foley per film (`sfx_design.py`), two-pass loudness to −14 LUFS, a social copy.

What must change every time: the look (classic, noir, riso, blueprint, pastel, tabloid), the hook form, the story
shape, the scene mix and the ending. Never reuse the previous film's look.

Deliver: the social MP4, the photo credits for the description, and the sources. Say plainly what was left out or
substituted and why.

My first topic: <TOPIC, or "random">
