"""White's face: 1-bit pixel portraits, so every founder's White looks like their own.

Three ways in:
  - traits:  pick hair, eyes, glasses, beard, mouth, clothes (or leave any to the seed)
  - seed:    a number that always produces the same face; reroll until you like one
  - photo:   your own picture, cropped and dithered to 1-bit locally (never uploaded)

Output is a square PNG (black on white, crisp pixels) used as the Hermes profile avatar
(<profile>/assets/avatar.png), plus white/face.json so the face can be re-made or tweaked.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageOps

G = 48            # pixel grid
SCALE = 10        # 48 * 10 = 480 px, padded to 512
SIZE = 512
INK, PAPER = 0, 255

OPTIONS = {
    "face": ["oval", "round", "long"],
    "hair": ["short", "side_part", "curly", "long", "bun", "buzz", "bald", "cap"],
    "eyes": ["dots", "open", "sleepy", "wink"],
    "brows": ["flat", "raised", "none"],
    "glasses": ["none", "round", "square"],
    "nose": ["line", "hook", "dot"],
    "mouth": ["smile", "flat", "smirk", "grin"],
    "beard": ["none", "stubble", "full", "mustache"],
    "clothes": ["tee", "collar", "turtleneck", "hoodie"],
}


@dataclass
class Face:
    face: str = "oval"
    hair: str = "short"
    eyes: str = "dots"
    brows: str = "flat"
    glasses: str = "none"
    nose: str = "line"
    mouth: str = "smile"
    beard: str = "none"
    clothes: str = "tee"
    seed: int = 0

    @classmethod
    def from_seed(cls, seed: int, **fixed) -> "Face":
        rng = random.Random(seed)
        picks = {k: rng.choice(v) for k, v in OPTIONS.items()}
        # keep combinations sensible
        if picks["hair"] == "cap" and rng.random() < 0.5:
            picks["brows"] = "flat"
        picks.update({k: v for k, v in fixed.items() if v})
        f = cls(seed=seed, **picks)
        f.validate()
        return f

    def validate(self) -> None:
        for fld in fields(self):
            if fld.name == "seed":
                continue
            val = getattr(self, fld.name)
            if val not in OPTIONS[fld.name]:
                raise ValueError(f"{fld.name} must be one of {OPTIONS[fld.name]}, got {val!r}")


# ---------- drawing on the 48x48 grid ----------

class Canvas:
    def __init__(self):
        self.img = Image.new("L", (G, G), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def px(self, x, y, c=INK):
        if 0 <= x < G and 0 <= y < G:
            self.img.putpixel((int(x), int(y)), c)

    def line(self, pts, c=INK):
        self.d.line(pts, fill=c, width=1)

    def ellipse(self, box, outline=INK, fill=None):
        self.d.ellipse(box, outline=outline, fill=fill, width=1)

    def rect(self, box, outline=None, fill=None):
        self.d.rectangle(box, outline=outline, fill=fill)

    def dither(self, box, mask_fn=None, density=2):
        """Checkerboard shading inside box (optionally limited by mask_fn(x, y))."""
        x0, y0, x1, y1 = box
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x + y) % density == 0 and (mask_fn is None or mask_fn(x, y)):
                    self.px(x, y)


def _head_box(face: str):
    return {"oval": (14, 9, 33, 34), "round": (13, 10, 34, 33), "long": (15, 8, 32, 35)}[face]


def render_face(f: Face) -> Image.Image:
    f.validate()
    c = Canvas()
    hx0, hy0, hx1, hy1 = _head_box(f.face)
    cx = (hx0 + hx1) // 2

    # shoulders / clothes (drawn first, head covers the top)
    c.line([(6, 47), (10, 41), (17, 38), (cx - 3, 37)])
    c.line([(41, 47), (37, 41), (30, 38), (cx + 3, 37)])
    if f.clothes == "collar":
        c.line([(cx - 4, 37), (cx, 42), (cx + 4, 37)])
        c.line([(cx - 4, 37), (cx - 7, 41)]); c.line([(cx + 4, 37), (cx + 7, 41)])
    elif f.clothes == "turtleneck":
        c.rect((cx - 5, 34, cx + 5, 38), fill=INK)
        c.rect((9, 41, 38, 47), fill=INK)
        c.d.polygon([(6, 47), (10, 41), (17, 38), (30, 38), (37, 41), (41, 47)], fill=INK)
    elif f.clothes == "hoodie":
        c.line([(cx - 8, 36), (cx - 4, 41), (cx, 39), (cx + 4, 41), (cx + 8, 36)])
        c.line([(cx - 2, 41), (cx - 2, 45)]); c.line([(cx + 2, 41), (cx + 2, 45)])
    else:  # tee
        c.line([(cx - 4, 37), (cx, 40), (cx + 4, 37)])
    # neck
    c.line([(cx - 3, hy1 - 1), (cx - 3, 37)]); c.line([(cx + 3, hy1 - 1), (cx + 3, 37)])

    # head
    c.ellipse((hx0, hy0, hx1, hy1), fill=PAPER)
    # ears
    ey = (hy0 + hy1) // 2
    c.ellipse((hx0 - 2, ey - 2, hx0 + 1, ey + 3), fill=PAPER)
    c.ellipse((hx1 - 1, ey - 2, hx1 + 2, ey + 3), fill=PAPER)
    c.ellipse((hx0, hy0, hx1, hy1))  # re-stroke head edge over ears

    # hair
    top = hy0
    if f.hair == "short":
        c.d.chord((hx0, hy0 - 2, hx1, hy0 + 12), 180, 360, fill=INK)
    elif f.hair == "side_part":
        c.d.chord((hx0 - 1, hy0 - 2, hx1 + 1, hy0 + 13), 180, 360, fill=INK)
        c.d.polygon([(hx0 + 2, hy0 + 6), (cx + 4, hy0 + 2), (hx1 - 1, hy0 + 7), (hx1 - 1, hy0 + 4), (cx, hy0)], fill=INK)
        c.line([(hx0 + 7, hy0 + 1), (hx0 + 9, hy0 + 6)], c=PAPER)
    elif f.hair == "curly":
        c.d.chord((hx0 - 2, hy0 - 4, hx1 + 2, hy0 + 12), 180, 360, fill=INK)
        rng = random.Random(f.seed)
        # scalloped outline: small curls along the hair edge
        for k in range(13):
            import math as _m
            a = _m.pi + _m.pi * k / 12
            x = cx + (hx1 - hx0 + 4) / 2 * _m.cos(a)
            y = hy0 + 4 + 8 * _m.sin(a)
            r = 2 + rng.random() * 0.8
            c.ellipse((x - r, y - r, x + r, y + r), fill=INK)
        # a few light flecks for texture
        for _ in range(10):
            x = rng.randint(hx0 + 1, hx1 - 1)
            y = rng.randint(hy0 - 2, hy0 + 3)
            c.px(x, y, PAPER)
    elif f.hair == "long":
        c.d.chord((hx0 - 2, hy0 - 2, hx1 + 2, hy0 + 14), 180, 360, fill=INK)
        c.rect((hx0 - 2, hy0 + 6, hx0 + 1, hy1 + 2), fill=INK)
        c.rect((hx1 - 1, hy0 + 6, hx1 + 2, hy1 + 2), fill=INK)
    elif f.hair == "bun":
        c.d.chord((hx0, hy0 - 1, hx1, hy0 + 11), 180, 360, fill=INK)
        c.ellipse((cx - 4, hy0 - 7, cx + 4, hy0 + 1), fill=INK)
    elif f.hair == "buzz":
        c.dither((hx0 + 1, hy0, hx1 - 1, hy0 + 5), mask_fn=lambda x, y: ((x - cx) ** 2) / 100 + ((y - hy0 - 6) ** 2) / 40 <= 1.1)
    elif f.hair == "cap":
        c.d.chord((hx0 - 1, hy0 - 3, hx1 + 1, hy0 + 11), 180, 360, fill=INK)
        c.rect((hx0 - 1, hy0 + 3, hx1 + 9, hy0 + 4), fill=INK)  # brim
        c.px(cx, hy0 - 3, PAPER)
    # bald: nothing

    # face features
    ex_l, ex_r, eye_y = cx - 5, cx + 4, ey - 1
    if f.brows == "flat":
        c.line([(ex_l - 2, eye_y - 3), (ex_l + 2, eye_y - 3)]); c.line([(ex_r - 2, eye_y - 3), (ex_r + 2, eye_y - 3)])
    elif f.brows == "raised":
        c.line([(ex_l - 2, eye_y - 3), (ex_l, eye_y - 4), (ex_l + 2, eye_y - 4)])
        c.line([(ex_r - 2, eye_y - 4), (ex_r, eye_y - 4), (ex_r + 2, eye_y - 3)])

    def eye(x, kind):
        if kind == "dots":
            c.rect((x, eye_y, x + 1, eye_y + 1), fill=INK)
        elif kind == "open":
            c.ellipse((x - 2, eye_y - 1, x + 2, eye_y + 2)); c.px(x, eye_y); c.px(x, eye_y + 1)
        elif kind == "sleepy":
            c.line([(x - 2, eye_y + 1), (x + 2, eye_y + 1)]); c.px(x, eye_y + 2)
        elif kind == "closed":
            c.line([(x - 2, eye_y + 1), (x, eye_y + 2), (x + 2, eye_y + 1)])
    eye(ex_l, f.eyes if f.eyes != "wink" else "dots")
    eye(ex_r, f.eyes if f.eyes != "wink" else "closed")

    if f.glasses == "round":
        c.ellipse((ex_l - 3, eye_y - 2, ex_l + 3, eye_y + 3)); c.ellipse((ex_r - 3, eye_y - 2, ex_r + 3, eye_y + 3))
        c.line([(ex_l + 3, eye_y), (ex_r - 3, eye_y)])
    elif f.glasses == "square":
        c.rect((ex_l - 3, eye_y - 2, ex_l + 3, eye_y + 3), outline=INK); c.rect((ex_r - 3, eye_y - 2, ex_r + 3, eye_y + 3), outline=INK)
        c.line([(ex_l + 3, eye_y), (ex_r - 3, eye_y)])
        c.line([(hx0, eye_y), (ex_l - 3, eye_y)]); c.line([(ex_r + 3, eye_y), (hx1, eye_y)])

    ny = eye_y + 3
    if f.nose == "line":
        c.line([(cx, ny), (cx, ny + 4), (cx + 1, ny + 4)])
    elif f.nose == "hook":
        c.line([(cx, ny), (cx - 1, ny + 3), (cx + 1, ny + 5)])
    else:
        c.px(cx - 1, ny + 4); c.px(cx + 1, ny + 4)

    my = ny + 7
    if f.beard == "stubble":
        c.dither((hx0 + 2, my - 3, hx1 - 2, hy1), density=2,
                 mask_fn=lambda x, y: ((x - cx) ** 2) / 81 + ((y - my) ** 2) / 49 <= 1 and not (abs(x - cx) <= 3 and abs(y - my) <= 1))
    elif f.beard == "full":
        c.d.chord((hx0 + 1, my - 10, hx1 - 1, hy1 + 1), 0, 180, fill=INK)
        c.rect((cx - 2, my, cx + 2, my), fill=PAPER)  # thin mouth line cut into the beard
    elif f.beard == "mustache":
        c.line([(cx - 4, my - 1), (cx - 1, my - 2), (cx + 1, my - 2), (cx + 4, my - 1)])

    mouth_col = PAPER if f.beard == "full" else INK
    if f.mouth == "smile":
        c.line([(cx - 3, my), (cx - 2, my + 1), (cx + 2, my + 1), (cx + 3, my)], c=mouth_col)
    elif f.mouth == "flat":
        c.line([(cx - 2, my + 1), (cx + 2, my + 1)], c=mouth_col)
    elif f.mouth == "smirk":
        c.line([(cx - 2, my + 1), (cx + 2, my + 1), (cx + 3, my)], c=mouth_col)
    else:  # grin
        c.rect((cx - 3, my, cx + 3, my + 2), outline=mouth_col); c.line([(cx - 2, my + 1), (cx + 2, my + 1)], c=mouth_col)

    return _finish(c.img)


def render_photo(path: Path, contrast: float = 1.6) -> Image.Image:
    """Turn a photo into a 1-bit pixel portrait, entirely on this machine."""
    from PIL import ImageEnhance
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("L")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = max(0, (h - side) // 3)  # bias up: faces sit high in portraits
    im = im.crop((left, top, left + side, top + side))
    im = ImageOps.autocontrast(im, cutoff=2)
    from PIL import ImageStat
    mean = ImageStat.Stat(im).mean[0]
    if mean < 120:  # dark photo: lift midtones so the 1-bit result isn't mostly black
        gamma = 0.55 if mean < 80 else 0.75
        im = im.point(lambda v: int(255 * (v / 255) ** gamma))
    im = ImageEnhance.Contrast(im).enhance(contrast)
    small = im.resize((G, G), Image.LANCZOS)
    bw = small.convert("1", dither=Image.Dither.FLOYDSTEINBERG).convert("L")
    # line-art pass: strong edges (face outline, jaw, collar) inked on top, like hand-drawn bitmaps
    from PIL import ImageChops, ImageFilter
    edges = small.filter(ImageFilter.FIND_EDGES).point(lambda v: 0 if v > 60 else 255)
    ImageDraw.Draw(edges).rectangle((0, 0, G - 1, G - 1), outline=255)  # the filter's frame artifact
    bw = ImageChops.darker(bw, edges)
    return _finish(bw)


def _finish(grid: Image.Image) -> Image.Image:
    big = grid.resize((G * SCALE, G * SCALE), Image.NEAREST)
    out = Image.new("L", (SIZE, SIZE), PAPER)
    off = (SIZE - G * SCALE) // 2
    out.paste(big, (off, off))
    return out.convert("RGB")


def contact_sheet(faces: list[Face], cols: int = 4, labels: bool = True) -> Image.Image:
    tile, pad, lab = 256, 16, (34 if labels else 0)
    rows = (len(faces) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tile + pad) + pad, rows * (tile + pad + lab) + pad), (235, 235, 230))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(faces):
        x = pad + (i % cols) * (tile + pad)
        y = pad + (i // cols) * (tile + pad + lab)
        sheet.paste(render_face(f).resize((tile, tile), Image.NEAREST), (x, y))
        if labels:
            d.text((x + tile / 2, y + tile + 17), f"seed {f.seed}", fill=(40, 40, 40), anchor="mm")
    return sheet


def make(home: Path, *, seed: Optional[int] = None, photo: Optional[str] = None,
         traits: Optional[dict] = None) -> dict:
    """Create and install White's face. Keeps the previous traits when only tweaking some."""
    traits = {k: v for k, v in (traits or {}).items() if v}
    if photo:
        p = Path(photo).expanduser()
        if not p.is_file():
            raise ValueError(f"No photo at {p}")
        img = render_photo(p)
        path = save_avatar(home, img, {"source": "photo"})  # the photo itself is never copied or stored
        return {"avatar": str(path), "source": "photo"}
    base = load_face(home)
    if seed is None and base is not None:
        merged = {**{k: v for k, v in asdict(base).items() if k != "seed"}, **traits}
        face = Face(seed=base.seed, **merged)
    else:
        face = Face.from_seed(seed if seed is not None else random.randrange(1, 100000), **traits)
    face.validate()
    path = save_avatar(home, render_face(face), {"source": "traits", "face": asdict(face)})
    return {"avatar": str(path), "source": "traits", "face": asdict(face)}


def choices(home: Path, start: Optional[int] = None, n: int = 12, traits: Optional[dict] = None) -> dict:
    """A sheet of n faces to pick from, by seed."""
    start = start if start is not None else random.randrange(1, 90000)
    faces = [Face.from_seed(start + i, **(traits or {})) for i in range(n)]
    out = home / "founder" / "faces"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"choices-{start}.png"
    contact_sheet(faces).save(path)
    return {"sheet": str(path), "seeds": [f.seed for f in faces]}


def save_avatar(home: Path, img: Image.Image, meta: dict) -> Path:
    assets = home / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for ext in ("jpg", "webp"):  # Hermes picks the first existing avatar.*; keep only ours
        old = assets / f"avatar.{ext}"
        if old.exists():
            old.unlink()
    path = assets / "avatar.png"
    img.save(path)
    (home / "white").mkdir(parents=True, exist_ok=True)
    (home / "white" / "face.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def load_face(home: Path) -> Optional[Face]:
    p = home / "white" / "face.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("source") != "traits":
        return None
    return Face(**{k: v for k, v in data.get("face", {}).items() if k in {f.name for f in fields(Face)}})
