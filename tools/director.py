"""Shot director: turns one cut-out talking head into a multi-setup, multi-angle edit.

Usage: python tools/director.py SHOTS.json OUT.mp4
SHOTS.json:
{
 "layers": "edit/raw01/layers", "sets": "edit/raw01/sets", "raw": "edit/raw01/final.mp4",
 "faces": "edit/raw01/faces.json", "layout_out": "edit/raw01/layout.json",
 "shots": [{"t0": 0, "t1": 1.0, "set": "lamp", "scale": 1.0, "z": [1.0, 1.06], "face": [[540, 860], [540, 850]],
            "desk": false, "rot": [0, 0], "in": "whip", "fx": [{"type": "brackets", "at": 7.87}]}, ...]
}
- scale: person size (1 = source framing; < 1 needs "desk": true to hide where the body meets the source frame)
- z: camera zoom from start to end of the shot; face: where the (smoothed) face center lands on screen
- in: transition into the shot: cut | whip | zoomblur | flash
- fx: brackets (viewfinder corners on the face), card (editor timeline UI), beforeafter (wipe from the raw room),
      lightswitch (flat light until "at", then warm), bookmark (save icon pop)
Video only; audio is added later. Writes per-shot caption/title heights to layout_out.
"""
import json, math, subprocess, sys
import cv2, numpy as np

W, H, FPS = 1080, 1920, 30
PW, PH = 1620, 2880
DESK_TOP = 1300           # screen y of the desk surface in wide shots
TRANS = 5                 # frames on each side of a cut for whip / zoomblur / flash


def ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def back_out(p):
    p = min(1.0, max(0.0, p)); c = 1.70158
    return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2


def face_track(path, n):
    d = json.load(open(path))
    ts, cx, cy, top, chin = [], [], [], [], []
    for s in d["samples"]:
        if s["faces"]:
            x, y, w, h = s["faces"][0][:4]
            ts.append(s["t"]); cx.append(x + w / 2); cy.append(y + h / 2); top.append(y); chin.append(y + h)
    t = np.arange(n) / FPS
    arr = [np.interp(t, ts, v) for v in (cx, cy, top, chin)]
    k = np.exp(-0.5 * (np.arange(-24, 25) / 9.0) ** 2); k /= k.sum()   # ~0.3 s smoothing: steady, not locked
    sm = [np.convolve(np.pad(v, 24, mode="edge"), k, mode="valid") for v in arr[:2]]
    return sm[0], sm[1], arr[2], arr[3]


def side_contact(alpha_path):
    """Per frame: topmost row where the matte touches the left/right source edge."""
    cap, out = cv2.VideoCapture(alpha_path), []
    ok, f = cap.read()
    while ok:
        a, top = f[..., 0] > 128, H
        for col in (a[:, :3].any(1), a[:, -3:].any(1)):
            rows = np.where(col)[0]
            if len(rows):
                top = min(top, rows[0])
        out.append(top)
        ok, f = cap.read()
    return np.array(out)


class Reader:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path); self.last = None
    def read(self):
        ok, f = self.cap.read()
        if ok:
            self.last = f
        return self.last


def stripes_texture(angle):
    s = np.zeros((H * 2, W * 2), np.float32)
    for y in range(0, H * 2, 150):
        cv2.rectangle(s, (0, y), (W * 2, y + 66), 1.0, -1)
    s = cv2.warpAffine(s, cv2.getRotationMatrix2D((W, H), angle, 1.0), (W * 2, H * 2))
    return cv2.GaussianBlur(s, (0, 0), 16)


def rounded_rect(img, x0, y0, x1, y1, r, color, alpha=1.0):
    over = img.copy()
    cv2.rectangle(over, (x0 + r, y0), (x1 - r, y1), color, -1)
    cv2.rectangle(over, (x0, y0 + r), (x1, y1 - r), color, -1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cv2.circle(over, (cx, cy), r, color, -1, cv2.LINE_AA)
    cv2.addWeighted(over, alpha, img, 1 - alpha, 0, img)


def draw_card(frame, t, t_in, t_out, box):
    """Floating editor-timeline card: rounded, shadowed, tracks with clips and a moving playhead."""
    if not (t_in - 0.01 <= t <= t_out + 0.25):
        return frame
    p = back_out((t - t_in) / 0.35) if t < t_out else 1 - ease((t - t_out) / 0.25)
    x0, y0, x1, y1 = box
    cw, ch = x1 - x0, y1 - y0
    card = np.zeros((ch + 80, cw + 80, 3), np.uint8)
    m = np.zeros((ch + 80, cw + 80), np.uint8)
    rounded_rect(card, 40, 40, 40 + cw, 40 + ch, 34, (218, 233, 243))
    rounded_rect(m, 40, 40, 40 + cw, 40 + ch, 34, 255)
    for i, c in enumerate(((95, 95, 255), (90, 190, 250), (110, 200, 120))):        # window dots
        cv2.circle(card, (80 + i * 34, 82), 10, c, -1, cv2.LINE_AA)
    cv2.putText(card, "Timeline", (180, 92), cv2.FONT_HERSHEY_DUPLEX, 1.0, (60, 60, 70), 2, cv2.LINE_AA)  # card is uint8
    tracks = [((52, 155, 249), [(0.02, 0.30), (0.33, 0.62), (0.66, 0.97)]),
              ((180, 160, 60), [(0.05, 0.45), (0.50, 0.90)]),
              ((170, 100, 190), [(0.02, 0.18), (0.22, 0.55), (0.60, 0.80)])]
    for k, (col, clips) in enumerate(tracks):
        ty = 140 + k * ((ch - 130) // 3)
        for a0, a1 in clips:
            rounded_rect(card, int(60 + a0 * (cw - 40)), ty, int(60 + a1 * (cw - 40)), ty + (ch - 190) // 3, 12, col)
    ph = int(60 + ((t - t_in) / max(0.1, t_out - t_in)) % 1.0 * (cw - 40))
    cv2.line(card, (ph, 120), (ph, 40 + ch - 20), (60, 60, 230), 4, cv2.LINE_AA)
    cv2.circle(card, (ph, 120), 10, (60, 60, 230), -1, cv2.LINE_AA)
    s = 0.85 + 0.15 * p
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    M = np.float32([[s, 0, cx - s * (cw / 2 + 40)], [0, s, cy - s * (ch / 2 + 40)]])
    warped = cv2.warpAffine(card, M, (W, H)).astype(np.float32)
    mk = cv2.warpAffine(m, M, (W, H)).astype(np.float32)[..., None] / 255 * min(1, max(0, p * 1.4))
    Ms = np.float32([[s, 0, M[0, 2] + 8], [0, s, M[1, 2] + 22]])
    shadow = cv2.GaussianBlur(cv2.warpAffine(m, Ms, (W, H)), (0, 0), 22).astype(np.float32)[..., None] / 255 * 0.5 * min(1, p)
    frame = frame * (1 - shadow)
    return frame * (1 - mk) + warped * mk


def editor_layout(comp, bg_plate, t, t0, t1):
    """The shot plays inside a floating video-editor window (preview + timeline) over a dimmed, blurred room."""
    p_in = back_out((t - t0) / 0.45)
    s = 0.90 + 0.10 * min(1.2, p_in)
    out = cv2.GaussianBlur(bg_plate, (0, 0), 10) * 0.55
    x0, y0, x1, y1 = 70, 250, 1010, 1470                 # window
    px0, py0, px1, py1 = x0 + 24, y0 + 70, x1 - 24, 1150  # preview area
    win = np.zeros((H, W, 3), np.float32); m = np.zeros((H, W), np.float32)
    rounded_rect(win, x0, y0, x1, y1, 36, (34, 30, 30)); rounded_rect(m, x0, y0, x1, y1, 36, 1.0)
    for i2, c in enumerate(((95, 95, 255), (90, 190, 250), (110, 200, 120))):
        cv2.circle(win, (x0 + 40 + i2 * 32, y0 + 36), 10, c, -1, cv2.LINE_AA)
    txt = np.zeros((H, W, 3), np.uint8)  # putText needs 8-bit
    cv2.putText(txt, "my_short_final.mp4", (x0 + 150, y0 + 46), cv2.FONT_HERSHEY_DUPLEX, 0.95, (200, 205, 215), 2, cv2.LINE_AA)
    win = np.where(txt > 0, txt.astype(np.float32), win)
    pw, ph = px1 - px0, py1 - py0                          # preview: crop of the full shot around the face area
    sc = pw / W
    crop_h = int(ph / sc)
    cy0 = int(min(H - crop_h, max(0, 860 - crop_h / 2)))
    prev = cv2.resize(comp[cy0:cy0 + crop_h], (pw, ph), interpolation=cv2.INTER_AREA)
    pm = np.zeros((ph, pw), np.float32); rounded_rect(pm, 0, 0, pw - 1, ph - 1, 18, 1.0)
    win[py0:py1, px0:px1] = win[py0:py1, px0:px1] * (1 - pm[..., None]) + prev * pm[..., None]
    tl0 = py1 + 40                                         # timeline
    cv2.line(win, (px0, tl0), (px1, tl0), (90, 90, 100), 2)
    for k2 in range(0, 11):
        xk = int(px0 + k2 * (px1 - px0) / 10)
        cv2.line(win, (xk, tl0 - 8), (xk, tl0 + 8), (120, 120, 130), 2)
    tracks = [((52, 155, 249), [(0.0, 0.28), (0.30, 0.61), (0.63, 1.0)]), ((180, 160, 60), [(0.05, 0.47), (0.52, 0.93)]),
              ((170, 100, 190), [(0.0, 0.2), (0.24, 0.56), (0.6, 0.82)])]
    for k2, (col, clips) in enumerate(tracks):
        ty = tl0 + 26 + k2 * 74
        for a0, a1 in clips:
            rounded_rect(win, int(px0 + a0 * (px1 - px0)), ty, int(px0 + a1 * (px1 - px0)) - 6, ty + 58, 12, col)
    ph_x = int(px0 + ((t - t0) / max(0.1, t1 - t0)) * (px1 - px0))
    cv2.line(win, (ph_x, tl0 - 14), (ph_x, y1 - 26), (70, 70, 240), 4, cv2.LINE_AA)
    cv2.circle(win, (ph_x, tl0 - 14), 11, (70, 70, 240), -1, cv2.LINE_AA)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    Ms = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
    win = cv2.warpAffine(win, Ms, (W, H)); m = cv2.warpAffine(m, Ms, (W, H))[..., None]
    sh_ = cv2.GaussianBlur(cv2.warpAffine(m[..., 0], np.float32([[1, 0, 10], [0, 1, 26]]), (W, H)), (0, 0), 26)[..., None]
    out = out * (1 - 0.6 * sh_)
    return out * (1 - m) + win * m


def draw_brackets(frame, t, at, box):
    if t < at:
        return frame
    p = ease((t - at) / 0.35)
    x, y, w, h = box
    g = 1.45 - 0.37 * p
    cx, cy = x + w / 2, y + h / 2
    x0, x1, y0, y1 = int(cx - w * g / 2), int(cx + w * g / 2), int(cy - h * g / 2), int(cy + h * g / 2)
    L = int(min(w, h) * 0.22)
    over = frame.copy()
    col = (200, 236, 255)
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        cv2.line(over, (px, py), (px + dx * L, py), col, 9, cv2.LINE_AA)
        cv2.line(over, (px, py), (px, py + dy * L), col, 9, cv2.LINE_AA)
    a = min(1.0, p * 1.5)
    return frame * (1 - a) + over * a


def draw_bookmark(frame, t, at, pos):
    if t < at:
        return frame
    p = (t - at) / 0.45
    s = back_out(p) if p < 1 else 1.0
    if s <= 0.01:
        return frame
    cx, cy = pos
    w, h = 120 * s, 160 * s
    pts = np.array([[cx - w / 2, cy - h / 2], [cx + w / 2, cy - h / 2], [cx + w / 2, cy + h / 2],
                    [cx, cy + h / 2 - 50 * s], [cx - w / 2, cy + h / 2]], np.int32)
    over = frame.copy()
    glow = np.zeros((H, W), np.float32)
    cv2.fillPoly(glow, [pts], 1.0)
    glow = cv2.GaussianBlur(glow, (0, 0), 25)[..., None]
    over = over + glow * np.array([30, 120, 250], np.float32) * 0.8
    cv2.fillPoly(over, [pts], (52, 155, 249), cv2.LINE_AA)
    return over


def main():
    cfg = json.load(open(sys.argv[1])); out_path = sys.argv[2]
    rng_t = [float(x) for x in sys.argv[3].split("-")] if len(sys.argv) > 3 else None  # preview: "start-end" seconds
    shots = cfg["shots"]
    n = int(round(shots[-1]["t1"] * FPS))
    first, last = (int(rng_t[0] * FPS), int(rng_t[1] * FPS)) if rng_t else (0, n)
    fx_, fy_, ftop, fchin = face_track(cfg["faces"], n)
    contact_f = side_contact(cfg["layers"] + "/alpha.mp4")
    contact = {k: int(contact_f[int(sh["t0"] * FPS):max(int(sh["t0"] * FPS) + 1, int(sh["t1"] * FPS))].min())
               for k, sh in enumerate(shots)}
    print(f"matte touches the side edges from y={contact}", file=sys.stderr)
    desk_top = {}
    for k, sh in enumerate(shots):  # the desk sits just above where the body meets the source frame edge
        fr = slice(int(sh["t0"] * FPS), max(int(sh["t0"] * FPS) + 1, int(sh["t1"] * FPS)))
        P0 = sh.get("scale", 1.0) * sh["z"][0]
        desk_top[k] = int(min(1500, max(1000, sh["face"][0][1] + (contact[k] - fy_[fr].max()) * P0 - 50)))
    sets = {}
    for s in {sh["set"] for sh in shots}:
        far = cv2.imread(f"{cfg['sets']}/{s}_far.png").astype(np.float32)
        bok = cv2.imread(f"{cfg['sets']}/{s}_bokeh.png").astype(np.float32)
        sets[s] = (far, bok)
    desk = cv2.imread(f"{cfg['sets']}/desk_fg.png", cv2.IMREAD_UNCHANGED).astype(np.float32)
    stripes = stripes_texture(-20)
    warm_r, flat_r, alpha_r, raw_r = (Reader(cfg["layers"] + "/fg_warm.mp4"), Reader(cfg["layers"] + "/fg_flat.mp4"),
                                      Reader(cfg["layers"] + "/alpha.mp4"), Reader(cfg["raw"]))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vignette = (1 - 0.42 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)).clip(0.45, 1)[..., None]
    rng = np.random.default_rng(3)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                             "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    layout = {i: {"chin": 0, "top": H} for i in range(len(shots))}
    bounds = [round(sh["t0"] * FPS) for sh in shots[1:]]

    def shot_at(i):
        for k, sh in enumerate(shots):
            if sh["t0"] * FPS - 1e-6 <= i < sh["t1"] * FPS - 1e-6:
                return k, sh
        return len(shots) - 1, shots[-1]

    def person_matrix(sh, i, p, k):
        z = sh["z"][0] + (sh["z"][1] - sh["z"][0]) * ease(p)
        P = sh.get("scale", 1.0) * z
        (sx0, sy0), (sx1, sy1) = sh["face"]
        sx, sy = sx0 + (sx1 - sx0) * ease(p), sy0 + (sy1 - sy0) * ease(p)
        fx, fy = (W - fx_[i] if sh.get("mirror") else fx_[i]), fy_[i]
        if not sh.get("desk"):
            # keep the source frame edges off screen: the cut-out body must leave the frame at its own edges
            sx = min(max(sx, W - (W - fx) * P), fx * P)
            sy = max(sy, H - (H - fy) * P)
        else:
            sy = max(sy, desk_top[k] + 50 - (contact[k] - fy) * P, desk_top[k] + 50 - (H - fy) * P)
        rot = sh.get("rot", [0, 0]); r = math.radians(rot[0] + (rot[1] - rot[0]) * ease(p))
        c, s_ = math.cos(r) * P, math.sin(r) * P
        return np.float32([[c, -s_, sx - c * fx + s_ * fy], [s_, c, sy - s_ * fx - c * fy]]), P, (sx, sy), z

    for i in range(n):
        if i >= last:
            break
        t = i / FPS
        k, sh = shot_at(i)
        if i < first:
            for r in (warm_r, flat_r, alpha_r, raw_r):
                r.read()
            continue
        p = (t - sh["t0"]) / (sh["t1"] - sh["t0"])
        warm, flat, al, raw = warm_r.read(), flat_r.read(), alpha_r.read(), raw_r.read()
        if sh.get("mirror"):
            warm, flat, al, raw = (cv2.flip(x, 1) for x in (warm, flat, al, raw))
        M, P, (sx, sy), z = person_matrix(sh, i, p, k)
        fxs = {f["type"]: f for f in sh.get("fx", [])}
        ls = fxs.get("lightswitch")
        lit = not ls or t >= ls["at"]
        fg = cv2.warpAffine(warm if lit else flat, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        if P > 1.0:  # soften upscaling artifacts a bit, then restore edge contrast
            fg = cv2.addWeighted(fg, 1.35, cv2.GaussianBlur(fg, (0, 0), 1.6), -0.35, 0)
        a = cv2.warpAffine(al[..., 0], M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
        # background: plate with parallax (moves ~35 % of the person's camera move) + nearer bokeh layer
        far, bok = sets[sh["set"]]
        bz = (W / PW) * (1 + 0.35 * (z - 1)) * (1.0 if sh.get("scale", 1) >= 1 else 0.94)
        dxb, dyb = 0.35 * (sx - W / 2) + 30 * math.sin(t * 0.3), 0.35 * (sy - 860) + 20 * math.sin(t * 0.21)
        Mb = np.float32([[bz, 0, W / 2 - bz * PW / 2 + dxb], [0, bz, H / 2 - bz * PH / 2 + dyb]])
        bg = cv2.warpAffine(far, Mb, (W, H), borderMode=cv2.BORDER_REFLECT)
        Mk = Mb.copy(); Mk[0, 2] += dxb * 0.8; Mk[1, 2] += dyb * 0.8
        bg = bg + cv2.warpAffine(bok, Mk, (W, H), borderMode=cv2.BORDER_REFLECT)
        if not lit:
            bg = bg * 0.55 + bg.mean(axis=2, keepdims=True) * 0.15
        if "beforeafter" in fxs:
            ba = fxs["beforeafter"]
            line = W * (1 - ease((t - ba["at"]) / ba.get("dur", 0.7)))
            rawf = cv2.warpAffine(raw, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        # light wrap at quarter resolution
        small = cv2.resize(bg, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bgblur = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H))
        ainv = cv2.resize(cv2.GaussianBlur(cv2.resize(1 - a[..., 0], (W // 4, H // 4)), (0, 0), 4), (W, H))[..., None]
        edge = np.clip(ainv * a, 0, 1) * (0.45 if lit else 0.15)
        fg = fg * (1 - edge) + bgblur * edge
        comp = fg * a + bg * (1 - a)
        if lit:
            off = int(18 * t) % 150
            st = stripes[H // 2 - off:H // 2 - off + H, W // 2:W // 2 + W][..., None]
            comp = comp * (1 - 0.16 * st * (1 - 0.5 * a)) + np.array([30, 80, 140], np.float32) * 0.22 * st * a
        if sh.get("desk"):
            dy0 = desk_top[k] - 160
            dh = min(desk.shape[0], H - dy0)
            if dy0 + desk.shape[0] < H:  # extend the desk front to the bottom of the frame
                comp[dy0 + dh:] = desk[-1, :, :3] * (desk[-1, :, 3:] / 255) + comp[dy0 + dh:] * (1 - desk[-1, :, 3:] / 255)
            d = desk[:dh]; da = d[..., 3:] / 255
            comp[dy0:dy0 + dh] = comp[dy0:dy0 + dh] * (1 - da) + d[..., :3] * da
        if "beforeafter" in fxs and t >= fxs["beforeafter"]["at"] - 1.0:
            mask = (xx < line)[..., None].astype(np.float32)
            comp = rawf * mask + comp * (1 - mask)
            if 0 < line < W:
                glow = np.exp(-((xx - line) ** 2) / (2 * 6 ** 2))[..., None]
                comp = comp + glow * np.array([120, 200, 255], np.float32) * 0.9
        elif "beforeafter" in fxs:
            comp = rawf
        comp = comp * vignette
        # face box on screen (for brackets and layout)
        fw = (fchin[i] - ftop[i]) * 0.78
        fcx = W - fx_[i] if sh.get("mirror") else fx_[i]
        corners = np.array([[fcx - fw / 2, ftop[i], 1], [fcx + fw / 2, fchin[i], 1]], np.float32) @ M.T
        f_box = (corners[0, 0], corners[0, 1], corners[1, 0] - corners[0, 0], corners[1, 1] - corners[0, 1])
        layout[k]["chin"] = max(layout[k]["chin"], float(corners[1, 1]))
        layout[k]["top"] = min(layout[k]["top"], float(corners[0, 1]))
        if "editor" in fxs:
            comp = editor_layout(comp, bg, t, sh["t0"], sh["t1"])
        if "card" in fxs:
            c = fxs["card"]; comp = draw_card(comp, t, c["at"], c["until"], c["box"])
        if "brackets" in fxs:
            comp = draw_brackets(comp, t, fxs["brackets"]["at"], f_box)
        if "bookmark" in fxs:
            comp = draw_bookmark(comp, t, fxs["bookmark"]["at"], fxs["bookmark"].get("pos", (880, 1180)))
        if ls and abs(t - ls["at"]) < 0.25:
            comp = comp + np.array([120, 200, 255], np.float32) * max(0, 1 - abs(t - ls["at"]) / 0.25) ** 2 * 0.9
        # transitions around cuts
        for b, nxt in zip(bounds, shots[1:]):
            d = i - b  # <0: outgoing shot, >=0: incoming shot
            if -TRANS <= d < TRANS:
                kind = nxt.get("in", "cut")
                q = 1 - (abs(d + 0.5) / TRANS)  # 1 at the cut, 0 at the window edge
                if kind == "whip":
                    shift = (-1 if d < 0 else 1) * W * 0.35 * q ** 2
                    acc = np.zeros_like(comp)
                    for j in range(7):
                        acc += np.roll(comp, int(shift * (0.6 + 0.08 * j)), axis=1)
                    comp = acc / 7
                elif kind == "zoomblur":
                    acc = comp.copy()
                    for j in range(1, 6):
                        s = 1 + 0.035 * j * q
                        Mz = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * 860]])
                        acc += cv2.warpAffine(comp, Mz, (W, H), borderMode=cv2.BORDER_REFLECT)
                    comp = acc / 6
                elif kind == "flash" and d >= -2:
                    comp = comp + np.array([150, 215, 255], np.float32) * q ** 2 * 1.1
        comp = comp + rng.normal(0, 2.6, (H, W, 1)).astype(np.float32)
        proc.stdin.write(np.clip(comp, 0, 255).astype(np.uint8).tobytes())
        if i % 60 == 0:
            print(f"  {t:5.1f}s shot {k}", file=sys.stderr)
    proc.stdin.close(); proc.wait()
    lay = []
    for k, sh in enumerate(shots):
        cap_y = int(min(1570, max(1400, layout[k]["chin"] + 95)))
        title_y = int(min(640, max(270, layout[k]["top"] - 130)))
        lay.append({"t0": sh["t0"], "t1": sh["t1"], "caption_y": cap_y, "title_y": title_y, "chin": round(layout[k]["chin"]),
                    "face_top": round(layout[k]["top"])})
    if not rng_t:
        json.dump(lay, open(cfg["layout_out"], "w"), indent=1)


if __name__ == "__main__":
    main()
