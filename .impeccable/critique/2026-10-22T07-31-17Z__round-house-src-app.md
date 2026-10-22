---
target: round-house site
total_score: 23
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 2
target_identity: "file:/home/user/my-first/round-house/src/app"
timestamp: 2026-10-22T07-31-17Z
slug: round-house-src-app
---
Method: dual-agent (A: design review · B: detector + browser overlay)

## Design Health Score
| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Services track line rests half-drawn; hours line says "Back at 9am" on weekends |
| 2 | Match System / Real World | 3 | Jargon leaks: speed-to-lead, zero data retention, "Rev. C" |
| 3 | User Control and Freedom | 3 | Hovering the schematic rewrites the caption being read |
| 4 | Consistency and Standards | 2 | "Book a call" goes to a form; signal yellow used decoratively in 3 places |
| 5 | Error Prevention | 3 | Budget select mixes bands with "Monthly retainer" |
| 6 | Recognition Rather Than Recall | 3 | 13-row flat Build list; mobile retainer table clips plans |
| 7 | Flexibility and Efficiency | n/a | Marketing surface |
| 8 | Aesthetic and Minimalist Design | 3 | Same figures twice on Home; "Sample engagement" x7 |
| 9 | Error Recovery | 3 | mailto fallback until a form endpoint is set |
| 10 | Help and Documentation | n/a | Marketing surface (FAQ covers procurement) |
| **Total** | | **23/32** | **Good (72%)** |

## Design Specificity Verdict
LLM: hero turntable, title-block footer and spec-sheet pricing are ownable; below the hero the roundhouse grammar disappears and sections read as a tidy editorial template.
Detector: source scan 0 (regex-only, undercount); URL scan 2 warnings (oversized-h1 on /, skipped-heading on /services) + advisories (repeating-stripes-gradient = intentional drafting grid, false positive; 6 stragglers in dd/li, real). No console errors or failed requests.

## Priority Issues
- [P1] "Book a 30-minute call" links to a form; booking button buried below the form on phone. /impeccable clarify, adapt
- [P1] Case studies show return but not investment or payback. /impeccable clarify
- [P2] Track line resting states broken (half-drawn on Services load; rail overruns station 3). /impeccable animate
- [P2] Signal yellow used where nothing is clickable (Services outcome callouts, first station, About logo hub). /impeccable colorize
- [P2] Services Build is a 13-row flat wall; mobile retainer table clips; Run column uninformative. /impeccable distill, adapt

## Persona Red Flags
Jordan: no faces/names on About; jargon; Book lands on a form. Riley: weekend hours copy; hover hijacks caption; focus does not rotate bridge. Casey: booking below form; retainer table clipped; Send message vs full-width Book hierarchy flip.

## Minor Observations
Leads/CRM labels crowd; FAQ ink bleeds past the column; About hero empty right half; grid fragments under contact form; bay links all go to /services#build; Selected-work figures styled differently from results figures; "Next case study" link has no underline.

## Questions to Consider
Should the schematic recur (case studies lit at their bay, Build grouped by bay)? Is transparency real if proof omits cost? Should yellow mean exactly one thing?
