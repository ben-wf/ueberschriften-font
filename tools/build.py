"""Build the ÜBERSCHRIFTEN family from the checked-in DINish 4.007 sources."""
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib import builder as var_builder  # registers VarData methods

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "upstream/fonts"
OUT = ROOT / "fonts"
GLYPH = "slash_slash"
FAMILY = "ÜBERSCHRIFTEN"
PS_FAMILY = "Ueberschriften"
VERSION = "1.000"
# Condensed SemiBold proof: slash advance 304, second origin 264, pair advance 563.
SECOND = 264 / 304
BEARING_SHIFT = -36 / 304
PAIR_WIDTH = 563 / 304


def strokes(font, pen):
    glyphs = font.getGlyphSet()
    width = font["hmtx"]["slash"][0]
    for origin in (BEARING_SHIFT, BEARING_SHIFT + SECOND):
        transform = Transform(1.15, 0, 0.03, 1.15, origin * width, -52)
        glyphs["slash"].draw(TransformPen(pen, transform))


def add_static_outline(font, width):
    cff = font["CFF "].cff
    top = cff.topDictIndex[0]
    pen = T2CharStringPen(width - top.Private.nominalWidthX, None)
    strokes(font, pen)
    charstring = pen.getCharString(top.Private, cff.GlobalSubrs)
    chars = top.CharStrings
    chars.charStrings[GLYPH] = len(chars.charStringsIndex)
    chars.charStringsIndex.append(charstring)
    top.charset = [*top.charset, GLYPH]
    font.setGlyphOrder(top.charset)
    bounds = BoundsPen(None)
    charstring.draw(bounds)
    return int(bounds.bounds[0])


def add_variable_outline(font):
    glyf = font["glyf"]
    pen = TTGlyphPen(None)
    strokes(font, pen)
    order = [*font.getGlyphOrder(), GLYPH]
    glyf[GLYPH] = pen.glyph()
    font.setGlyphOrder(order)
    glyph = glyf[GLYPH]
    glyph.recalcBounds(glyf)

    # The transformed outlines and spacing are linear in the original slash
    # points and advance. Apply the same linear map to each variation delta.
    variations = []
    for source in font["gvar"].variations["slash"]:
        points = source.coordinates
        assert len(points) == 8 and None not in points
        left, right = points[-4:-2]
        assert left == (0, 0)
        advance_delta = right[0] - left[0]
        deltas = []
        for origin in (BEARING_SHIFT, BEARING_SHIFT + SECOND):
            for dx, dy in points[:-4]:
                deltas.append((otRound(1.15 * dx + 0.03 * dy + origin * advance_delta),
                               otRound(1.15 * dy)))
        deltas.extend([(0, 0), (otRound(PAIR_WIDTH * advance_delta), 0), (0, 0), (0, 0)])
        variations.append(TupleVariation(source.axes, deltas))
    font["gvar"].variations[GLYPH] = variations

    # Engines using HVAR instead of phantom points need the same advance.
    hvar = font["HVAR"].table
    index = hvar.AdvWidthMap.mapping["slash"]
    data = hvar.VarStore.VarData[index >> 16]
    hvar.AdvWidthMap.mapping[GLYPH] = (index & 0xFFFF0000) | len(data.Item)
    data.Item.append([otRound(PAIR_WIDTH * d) for d in data.Item[index & 0xFFFF]])
    data.ItemCount = len(data.Item)
    data.calculateNumShorts()
    return glyph.xMin


def add_ligature(font):
    width = otRound(font["hmtx"]["slash"][0] * PAIR_WIDTH)
    lsb = add_variable_outline(font) if "fvar" in font else add_static_outline(font, width)
    font["hmtx"][GLYPH] = width, lsb
    font["maxp"].numGlyphs = len(font.getGlyphOrder())
    font["GDEF"].table.GlyphClassDef.classDefs[GLYPH] = 2
    scratch = TTFont()
    scratch.setGlyphOrder(font.getGlyphOrder())
    addOpenTypeFeaturesFromString(scratch, f"feature liga {{ sub slash slash by {GLYPH}; }} liga;")
    table = font["GSUB"].table
    lookups = table.LookupList
    index = len(lookups.Lookup)
    lookups.Lookup.append(scratch["GSUB"].table.LookupList.Lookup[0])
    lookups.LookupCount = len(lookups.Lookup)
    features = table.FeatureList.FeatureRecord
    liga_index, = [i for i, r in enumerate(features) if r.FeatureTag == "liga"]
    liga = features[liga_index].Feature
    liga.LookupListIndex.append(index)
    liga.LookupCount = len(liga.LookupListIndex)
    for script in table.ScriptList.ScriptRecord:
        languages = [script.Script.DefaultLangSys, *(r.LangSys for r in script.Script.LangSysRecord)]
        for language in languages:
            if language and liga_index not in language.FeatureIndex:
                language.FeatureIndex = sorted([*language.FeatureIndex, liga_index])
                language.FeatureCount = len(language.FeatureIndex)


def rename(font, path, is_variable):
    names = font["name"]
    def upstream_name(i):
        return names.getDebugName(i).replace("DINish", FAMILY)
    if is_variable:
        ps = PS_FAMILY + "Variable"
        full = FAMILY + " Variable"
        style = "Regular"
    else:
        ps = path.stem.replace("DINish", PS_FAMILY)
        full = upstream_name(4)
        style = full.removeprefix(FAMILY + " ")
    values = {1:upstream_name(1), 2:upstream_name(2), 3:f"{VERSION};ben-wf;{ps}",
              4:full, 5:"Version " + VERSION, 6:ps, 16:FAMILY, 17:style,
              11:"https://github.com/ben-wf/ueberschriften-font"}
    if is_variable:
        values[25] = ps
        for inst in font["fvar"].instances:
            if inst.postscriptNameID != 0xFFFF:
                i = inst.postscriptNameID
                values[i] = names.getDebugName(i).replace("DINish", ps)
    for i, value in values.items():
        records = [n for n in names.names if n.nameID == i]
        for n in records:
            names.setName(value, i, n.platformID, n.platEncID, n.langID)
        if not records:
            names.setName(value, i, 3, 1, 0x409)
    font["head"].fontRevision = float(VERSION)
    if "CFF " in font:
        cff = font["CFF "].cff
        cff.fontNames[0] = ps
        top = cff.topDictIndex[0]
        top.FullName = full.replace(FAMILY, PS_FAMILY)
        top.FamilyName = PS_FAMILY
        top.version = VERSION


def build(path, is_variable=False):
    font = TTFont(path, recalcTimestamp=False)
    add_ligature(font)
    rename(font, path, is_variable)
    if is_variable:
        stem = "ueberschriften-variable"
    else:
        words = re.findall(r"Condensed|Expanded|SemiBold|Medium|Bold|Light|Regular|Black|Heavy|Italic", path.stem)
        stem = "ueberschriften-" + "-".join(w.lower() for w in words)
    for ext in (path.suffix[1:], "woff2"):
        dest = OUT / ext / (stem + "." + ext)
        dest.parent.mkdir(exist_ok=True, parents=True)
        font.flavor = "woff2" if ext == "woff2" else None
        font.save(dest)
    if is_variable:
        return None
    width = {3:75, 5:100, 7:125}[font["OS/2"].usWidthClass]
    italic = bool(font["OS/2"].fsSelection & 1)
    return f"""@font-face {{
  font-family: "ÜBERSCHRIFTEN";
  src: url("./woff2/{stem}.woff2") format("woff2");
  font-style: {"italic" if italic else "normal"};
  font-weight: {font["OS/2"].usWeightClass};
  font-stretch: {width}%;
  font-display: swap;
}}"""


def main():
    paths = sorted((SOURCES / "otf").rglob("*.otf"))
    assert len(paths) == 42
    rules = [build(p) for p in paths]
    (OUT / "ueberschriften.css").write_text("\n\n".join(rules) + "\n", encoding="utf-8")
    variable, = (SOURCES / "ttf/variable").glob("*.ttf")
    build(variable, is_variable=True)
    package = ROOT / "download/ueberschriften.zip"
    package.parent.mkdir(exist_ok=True)
    with ZipFile(package, "w") as archive:
        for path in [ROOT / "OFL.txt", ROOT / "Herkunft.txt", *sorted(OUT.rglob("*"))]:
            if path.is_file():
                entry = ZipInfo(path.relative_to(ROOT).as_posix())
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())


if __name__ == "__main__":
    main()
