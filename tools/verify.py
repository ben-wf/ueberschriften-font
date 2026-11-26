"""Check every distributed face, its layout cases and the variable contours."""
import json
from pathlib import Path
from subprocess import check_output
from tempfile import TemporaryDirectory

from fontTools.misc.roundTools import otRound
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from build import FAMILY, GLYPH, OUT, PAIR_WIDTH, SOURCES, strokes


def shape(path, text, *options):
    return json.loads(check_output(["hb-shape", "--output-format=json", *options, path, text]))


def glyphs(path, text, *options):
    return [item["g"] for item in shape(path, text, *options)]


def outline(font, name):
    gs = font.getGlyphSet()
    pen = RecordingPen()
    gs[name].draw(pen)
    return pen.value


def verify_face(path, original, temp):
    font = TTFont(path)
    source = TTFont(original)
    assert font["name"].getDebugName(16) == FAMILY
    assert font.getBestCmap() == source.getBestCmap()
    assert font.getGlyphOrder() == [*source.getGlyphOrder(), GLYPH]
    assert outline(font, "slash") == outline(source, "slash")
    web = TTFont(OUT / "woff2" / (path.stem + ".woff2"))
    web.flavor = None
    restored = temp / ("restored" + path.suffix)
    web.save(restored)
    for p in (path, restored):
        for engine in ("ot", "coretext"):
            shaper = "--shapers=" + engine
            assert glyphs(p, "//", shaper) == [GLYPH]
            assert glyphs(p, "//", shaper, "--features=liga=0") == ["slash", "slash"]
            assert glyphs(p, "/", shaper) == ["slash"]
            assert glyphs(p, "A/B", shaper) == glyphs(original, "A/B", shaper)
            for text in ("Nr. 8", "Nr. 942", "ÜBERSCHRIFTEN", "fi"):
                assert shape(p, text, shaper) == shape(original, text, shaper)
            for text in ("TEXT //", "ÜBERSCHRIFTEN //", "ТЕКСТ //"):
                assert glyphs(p, text, shaper)[-1] == GLYPH
                assert glyphs(p, text, shaper, "--features=liga=0")[-2:] == ["slash", "slash"]
        assert shape(p, "//")[0]["ax"] == font["hmtx"][GLYPH][0]
    return font["name"].getDebugName(6)


def verify_variations(path):
    font = TTFont(path)
    locations = [i.coordinates for i in font["fvar"].instances]
    assert len(locations) == 42
    locations.extend(({"wdth":88, "wght":625, "slnt":-5}, {"wdth":119,"wght":830,"slnt":-9}))
    for loc in locations:
        instance = instantiateVariableFont(font, loc)
        expected = RecordingPen()
        strokes(instance, expected)
        actual = outline(instance, GLYPH)
        assert len(expected.value) == len(actual)
        for (op1, pts1), (op2, pts2) in zip(expected.value, actual):
            assert op1 == op2
            for a, b in zip(pts1, pts2):
                assert max(abs(v-w) for v,w in zip(a,b)) <= 3, (loc,a,b)
        expected_width = otRound(instance["hmtx"]["slash"][0] * PAIR_WIDTH)
        axes = "--variations=" + ",".join(f"{k}={v}" for k,v in loc.items())
        for engine in ("ot", "coretext"):
            shaped, = shape(path, "//", axes, "--shapers=" + engine)
            assert shaped["g"] == GLYPH and abs(shaped["ax"] - expected_width) <= 3, (loc,shaped)


def main():
    paths = sorted((OUT / "otf").glob("*.otf"))
    assert len(paths) == 42
    assert len(list((OUT / "woff2").glob("*.woff2"))) == 43
    by_name = {p.stem:p for p in (SOURCES / "otf").rglob("*.otf")}
    names = set()
    with TemporaryDirectory() as folder:
        for path in paths:
            ps = TTFont(path)["name"].getDebugName(6)
            names.add(verify_face(path, by_name[ps.replace("Ueberschriften","DINish")], Path(folder)))
        variable = OUT / "ttf/ueberschriften-variable.ttf"
        verify_face(variable, next((SOURCES / "ttf/variable").glob("*.ttf")), Path(folder))
        verify_variations(variable)
    assert len(names) == 42
    print("42 OTFs, 43 WOFF2s and the variable TTF passed.")


if __name__ == "__main__":
    main()
