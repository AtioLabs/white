"""Tests for White's pixel faces. Run: python -m pytest plugins/white-core -q"""

import json
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))

import white_face as F  # noqa: E402


def test_seed_is_deterministic_and_valid():
    a, b = F.Face.from_seed(7), F.Face.from_seed(7)
    assert a == b
    a.validate()
    assert list(F.render_face(a).getdata()) == list(F.render_face(b).getdata())


def test_every_trait_value_renders():
    for trait, values in F.OPTIONS.items():
        for v in values:
            img = F.render_face(F.Face.from_seed(3, **{trait: v}))
            assert img.size == (F.SIZE, F.SIZE)
            colors = set(img.getdata())
            assert colors <= {(0, 0, 0), (255, 255, 255)}, f"{trait}={v} is not 1-bit"


def test_invalid_trait_rejected():
    with pytest.raises(ValueError):
        F.Face.from_seed(1, hair="mohawk")


def test_make_installs_avatar_and_tweaks_keep_the_rest(tmp_path):
    out = F.make(tmp_path, seed=11)
    assert Path(out["avatar"]) == tmp_path / "assets" / "avatar.png"
    first = out["face"]
    tweaked = F.make(tmp_path, traits={"glasses": "round"})["face"]
    assert tweaked["glasses"] == "round" and tweaked["hair"] == first["hair"] and tweaked["seed"] == 11
    meta = json.loads((tmp_path / "white" / "face.json").read_text())
    assert meta["source"] == "traits" and meta["face"]["glasses"] == "round"


def test_photo_is_dithered_and_never_stored(tmp_path):
    photo = tmp_path / "me.jpg"
    im = Image.new("L", (300, 400), 200)
    d = ImageDraw.Draw(im)
    d.ellipse((80, 80, 220, 260), fill=230); d.ellipse((110, 150, 130, 160), fill=30); d.ellipse((170, 150, 190, 160), fill=30)
    im.save(photo)
    out = F.make(tmp_path, photo=str(photo))
    img = Image.open(out["avatar"])
    assert set(img.convert("RGB").getdata()) <= {(0, 0, 0), (255, 255, 255)}
    stored = [p.name for p in tmp_path.rglob("*") if p.is_file()]
    assert "me.jpg" in stored and stored.count("me.jpg") == 1  # only the user's original, no copy made
    assert json.loads((tmp_path / "white" / "face.json").read_text()) == {"source": "photo"}


def test_old_avatar_formats_removed(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "avatar.jpg").write_bytes(b"x")
    F.make(tmp_path, seed=2)
    assert not (tmp_path / "assets" / "avatar.jpg").exists()


def test_choices_sheet(tmp_path):
    out = F.choices(tmp_path, start=100, n=4)
    assert Path(out["sheet"]).is_file() and out["seeds"] == [100, 101, 102, 103]
