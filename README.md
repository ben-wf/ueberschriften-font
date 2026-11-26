# ÜBERSCHRIFTEN

Eine Haus­schrift auf Basis von DINish v4.007. Die Standardligatur `//` bildet den Abschluss einer Überschrift. Ihre beiden Striche sind aus dem Slash des jeweiligen Schnitts gezeichnet. Im Text bleiben zwei U+002F erhalten.

## Schnitte

[Komplettes Schriftpaket herunterladen](https://github.com/ben-wf/ueberschriften-font/raw/refs/heads/main/download/ueberschriften.zip)

| Breiten | Gewichte | Lagen |
| --- | --- | --- |
| Condensed · Normal · Expanded | Light 300 · Regular 400 · Medium 500 · SemiBold 600 · Bold 700 · Heavy 800 · Black 900 | Aufrecht · Kursiv |

Alle 42 Kombinationen liegen als [OpenType für den Desktop](fonts/otf) und [WOFF2 für das Web](fonts/woff2) vor. Der Ausgangspunkt der Gestaltung ist [Condensed SemiBold](fonts/otf/ueberschriften-condensed-semibold.otf). Die Namen der Dateien sind kleingeschrieben und verwenden ASCII. Der typografische Familienname lautet **ÜBERSCHRIFTEN**.

## Im Web

Den Ordner `fonts/` mit seiner Verzeichnisstruktur auf den Webserver kopieren. Das Stylesheet enthält alle 42 Schnitte. Der Browser lädt die für den jeweiligen Text benötigten Dateien.

```html
<link rel="stylesheet" href="/fonts/ueberschriften.css">
<h1>ÜBERSCHRIFTEN&nbsp;//</h1>
```

```css
h1 {
  font-family: "ÜBERSCHRIFTEN", sans-serif;
  font-stretch: 75%;
  font-weight: 600;
  font-style: normal;
}
```

Ein einzelnes `/` bleibt der ursprüngliche Slash. Die Standardligatur greift überall bei zwei aufeinanderfolgenden Slashes, auch in URLs. Für die ursprüngliche Darstellung an einer bestimmten Stelle genügt `font-variant-ligatures: no-common-ligatures`. Das geschützte Leerzeichen hält das Zeichenpaar beim Umbruch am vorigen Wort.

## Variable Schrift

Die Familie steht auch als [variable TrueType-Datei](fonts/ttf/ueberschriften-variable.ttf) und [variabler Webfont](fonts/woff2/ueberschriften-variable.woff2) bereit. Sie enthält die Achsen `wdth` 75–125, `wght` 300–900 und `slnt` −12–0. Auch die Ligatur verändert Form und Laufweite mit den Achsen. Für eine Installation auf dem Desktop entweder die statischen OTFs oder die variable Datei auswählen.

```css
@font-face {
  font-family: "ÜBERSCHRIFTEN Variable";
  src: url("./fonts/woff2/ueberschriften-variable.woff2") format("woff2");
  font-weight: 300 900;
  font-stretch: 75% 125%;
  font-style: oblique 0deg 12deg;
  font-display: swap;
}
```

## Herstellung und Prüfung

Der Ordner [upstream](upstream) enthält den Originalstand der DINish-Quellen einschließlich der vom Originalprojekt gebauten Fonts. Die Git-Historie des Forks schließt an den Release-Commit `56416a590a5b4ef7f121d1c20cbbd173ebbfab51` an. Das Buildskript leitet die statischen CFF-Konturen aus den 42 Original-OTFs ab und ergänzt die Ligatur und ihre Achsendaten in der variablen TTF. Aus denselben fertigen Schriften entstehen die WOFF2-Dateien.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build.py
```

Für die Prüfung auf macOS wird zusätzlich HarfBuzz mit `hb-shape` und Core-Text-Unterstützung benötigt. `.venv/bin/python tools/verify.py` prüft die Desktopdateien und die aus WOFF2 zurückgelesenen Fonts mit beiden Satzengines. Die variablen Konturen und Laufweiten werden in allen benannten Instanzen und an zwei Zwischenpositionen geprüft.

## Lizenz und Herkunft

ÜBERSCHRIFTEN steht unter der [SIL Open Font License 1.1](OFL.txt). Bei Weitergabe der Fonts den Copyrightvermerk und den Lizenztext beilegen. Die ursprünglichen Copyright- und Lizenzangaben sind in den Fontdateien erhalten. Der Fork ergänzt eigene Familien- und PostScript-Namen sowie die neue Ligatur.

Copyright 2021 The DINish Project Authors. Das [Originalprojekt](https://github.com/playbeing/dinish/releases/tag/v4.007) nennt außerdem Stefan Peev (2023–2024), Bert Driehuis (2021–2025), Altinn (2019) und Datto Inc. (2017). [Herkunft und Credits](upstream/README.md#information-for-contributors)
