"""Looks: whole-film art direction, so two films never share one palette.

A look remaps the ten card names story.json uses for "bg" (mustard, red, teal, navy, newsprint, kraft, ink, cream, pink,
olive) to its own stock, and sets the accent ink (stamps, marker circles, map highlights), the caption highlight, the
label and caption fonts, the ransom-note tiles and the transition rhythm. story.json picks one with "look"; without it,
the film's slug picks one, so consecutive films differ unless a look is chosen on purpose.
"""
import hashlib

LOOKS = {
    # the original papercut stock: warm mid-century card
    "classic": {
        "cards": {"red": (196, 48, 38), "mustard": (214, 165, 52), "teal": (38, 104, 104), "navy": (30, 42, 66),
                  "newsprint": (226, 216, 194), "kraft": (176, 136, 92), "ink": (28, 26, 24), "cream": (238, 230, 212),
                  "pink": (222, 150, 140), "olive": (120, 120, 72)},
        "accent": "red", "highlight": "mustard", "label": "Anton", "caption": "Archivo",
        "tiles": ["cream", "ink", "red", "mustard"], "trans": ["right", "up", "left", "down", "cut", "right", "drop"],
    },
    # crime-file black and white with one red: for scandals, heists, disasters
    "noir": {
        "cards": {"red": (178, 30, 34), "mustard": (196, 190, 176), "teal": (58, 60, 62), "navy": (24, 24, 26),
                  "newsprint": (214, 210, 200), "kraft": (150, 142, 128), "ink": (16, 16, 17), "cream": (236, 233, 224),
                  "pink": (120, 116, 110), "olive": (84, 84, 80)},
        "accent": "red", "highlight": (255, 98, 88), "label": "Anton", "caption": "Archivo",
        "tiles": ["cream", "ink", "red", "ink"], "trans": ["cut", "left", "cut", "down", "cut", "right"],
    },
    # risograph print: fluoro pink, blue and yellow on off-white; for culture, music, youth, sport
    "riso": {
        "cards": {"red": (255, 72, 140), "mustard": (255, 214, 0), "teal": (0, 120, 191), "navy": (35, 40, 105),
                  "newsprint": (244, 239, 228), "kraft": (255, 168, 120), "ink": (30, 32, 70), "cream": (248, 244, 234),
                  "pink": (255, 150, 200), "olive": (0, 169, 92)},
        "accent": "red", "highlight": "mustard", "label": "Archivo", "caption": "Archivo",
        "tiles": ["cream", "red", "teal", "mustard"], "trans": ["up", "up", "cut", "left", "up", "drop"],
    },
    # engineering blueprint: blues and white with a safety-orange accent; for science, tech, space, building
    "blueprint": {
        "cards": {"red": (235, 110, 35), "mustard": (226, 232, 238), "teal": (40, 92, 168), "navy": (18, 44, 92),
                  "newsprint": (210, 222, 236), "kraft": (64, 110, 180), "ink": (12, 30, 64), "cream": (240, 244, 248),
                  "pink": (150, 186, 226), "olive": (90, 130, 160)},
        "accent": "red", "highlight": (255, 150, 80), "label": "Anton", "caption": "Archivo",
        "tiles": ["cream", "navy", "red", "teal"], "trans": ["right", "right", "cut", "right", "up"],
    },
    # soft pastels with a terracotta accent; for food, places, nature, gentle human stories
    "pastel": {
        "cards": {"red": (214, 104, 72), "mustard": (245, 222, 150), "teal": (150, 190, 170), "navy": (90, 96, 130),
                  "newsprint": (240, 232, 218), "kraft": (222, 190, 160), "ink": (52, 48, 46), "cream": (250, 244, 232),
                  "pink": (236, 196, 188), "olive": (178, 196, 150)},
        "accent": "red", "highlight": "mustard", "label": "Serif", "caption": "Archivo",
        "tiles": ["cream", "pink", "teal", "mustard"], "trans": ["drop", "left", "drop", "right", "up"],
    },
    # loud tabloid: black, white, yellow, red; for sport, records, money, breaking news
    "tabloid": {
        "cards": {"red": (222, 30, 40), "mustard": (255, 210, 0), "teal": (20, 20, 22), "navy": (36, 36, 40),
                  "newsprint": (236, 234, 228), "kraft": (255, 236, 150), "ink": (12, 12, 12), "cream": (250, 249, 245),
                  "pink": (255, 120, 120), "olive": (90, 90, 90)},
        "accent": "red", "highlight": "mustard", "label": "Anton", "caption": "Archivo",
        "tiles": ["mustard", "ink", "red", "cream"], "trans": ["cut", "cut", "right", "cut", "drop"],
    },
}

# default background order per look, used when a beat does not set "bg"
BG_ORDER = {
    "classic": ["mustard", "red", "teal", "newsprint", "kraft", "navy"],
    "noir": ["ink", "newsprint", "navy", "red", "cream", "teal"],
    "riso": ["newsprint", "red", "teal", "mustard", "cream", "olive"],
    "blueprint": ["navy", "teal", "newsprint", "kraft", "navy", "cream"],
    "pastel": ["cream", "teal", "pink", "mustard", "olive", "kraft"],
    "tabloid": ["mustard", "ink", "red", "newsprint", "mustard", "navy"],
}


def pick(story):
    """The look for a story: its "look", else one chosen from its slug (stable per film, different across films)."""
    name = story.get("look")
    if name in LOOKS:
        return name
    key = story.get("slug") or story.get("title") or "film"
    names = sorted(LOOKS)
    return names[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(names)]
