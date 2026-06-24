#!/usr/bin/env python3
"""Generate labeled SVG diagrams for the Treatment Volume Localization chapter."""
import os
BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

TEAL="#1f7fa0"; DARK="#0e3a4f"; AMBER="#d98a1f"; RED="#c0392b"; GRAY="#7a8794"
GREEN="#2e8b57"; LIGHT="#eef6f9"; INK="#1b2733"
FONT='font-family="DejaVu Sans, Arial, sans-serif"'

def wrap(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'{FONT}><rect x="0" y="0" width="{w}" height="{h}" fill="white"/>{body}</svg>')

figs = {}

# 1. Nested ICRU target volumes
def swatch(x, y, fill, stroke, dash, label):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<rect x="{x}" y="{y}" width="22" height="16" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>'
            f'<text x="{x+30}" y="{y+13}" font-size="12.5" fill="{INK}">{label}</text>')
cx, cy = 235, 200
nested = (
    f'<ellipse cx="{cx}" cy="{cy}" rx="170" ry="135" fill="{TEAL}" fill-opacity="0.06" stroke="{TEAL}" stroke-width="2" stroke-dasharray="6 4"/>'
    f'<ellipse cx="{cx}" cy="{cy}" rx="125" ry="98" fill="{TEAL}" fill-opacity="0.12" stroke="{TEAL}" stroke-width="1.6"/>'
    f'<ellipse cx="{cx}" cy="{cy}" rx="84" ry="64" fill="{TEAL}" fill-opacity="0.22" stroke="{TEAL}" stroke-width="1.6"/>'
    f'<ellipse cx="{cx}" cy="{cy}" rx="44" ry="32" fill="{RED}" fill-opacity="0.80" stroke="#8e2a1c" stroke-width="1.6"/>'
    f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" font-weight="bold" fill="white">GTV</text>'
    # inner labels for the rings
    f'<text x="{cx}" y="{cy-72}" text-anchor="middle" font-size="11.5" fill="{DARK}">CTV</text>'
    f'<text x="{cx}" y="{cy-108}" text-anchor="middle" font-size="11.5" fill="{DARK}">ITV</text>'
    f'<text x="{cx}" y="{cy-146}" text-anchor="middle" font-size="11.5" fill="{DARK}">PTV</text>'
)
legend = (
    swatch(450, 96,  f"{RED}", "#8e2a1c", "", "GTV — gross visible tumor (no margin)")
    + swatch(450, 132, f"{TEAL}", TEAL, "", "CTV — + microscopic spread &amp; nodes")
    + swatch(450, 168, f"{TEAL}", TEAL, "", "ITV — + internal motion (from 4D-CT)")
    + swatch(450, 204, "white", TEAL, "5 3", "PTV — + setup uncertainty")
    + f'<circle cx="461" cy="252" r="9" fill="{GRAY}"/>'
    + f'<circle cx="461" cy="252" r="15" fill="none" stroke="{GRAY}" stroke-width="1.4" stroke-dasharray="4 3"/>'
    + f'<text x="480" y="256" font-size="12.5" fill="{INK}">OAR + PRV — organ at risk + its margin</text>'
)
figs["fig6-target-volumes.svg"] = wrap(860, 400,
    f'<text x="430" y="30" text-anchor="middle" font-size="17" font-weight="bold" fill="{DARK}">ICRU Target Volumes (nested)</text>'
    + nested + legend
    + f'<text x="430" y="384" text-anchor="middle" font-size="11.5" fill="{GRAY}">Each volume contains the one inside it and adds exactly one kind of uncertainty.</text>')

# 2. Image match -> 6DOF couch correction
def darrow(x1,y1,x2,y2,color):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>'
            f'<polygon points="{x2},{y2} {x2-7},{y2-4} {x2-7},{y2+4}" fill="{color}"/>'
            f'<polygon points="{x1},{y1} {x1+7},{y1-4} {x1+7},{y1+4}" fill="{color}"/>')
left = (
    f'<text x="170" y="60" text-anchor="middle" font-size="14" font-weight="bold" fill="{DARK}">1 · Match the images</text>'
    # reference (orange) outline + tumor
    f'<ellipse cx="150" cy="150" rx="58" ry="74" fill="none" stroke="{AMBER}" stroke-width="2.5"/>'
    f'<circle cx="150" cy="150" r="12" fill="none" stroke="{AMBER}" stroke-width="2.5"/>'
    # today (blue) outline, offset + slight rotate
    f'<g transform="rotate(7 196 168)"><ellipse cx="186" cy="166" rx="58" ry="74" fill="none" stroke="{TEAL}" stroke-width="2.5"/>'
    f'<circle cx="186" cy="166" r="12" fill="none" stroke="{TEAL}" stroke-width="2.5"/></g>'
    f'<text x="86" y="250" font-size="11.5" fill="{AMBER}">reference = orange (plan)</text>'
    f'<text x="86" y="267" font-size="11.5" fill="{TEAL}">today = blue (CBCT)</text>'
    f'<path d="M250,150 q34,0 34,28" stroke="{DARK}" stroke-width="2" fill="none"/>'
    f'<polygon points="284,178 279,166 290,168" fill="{DARK}"/>'
    f'<text x="170" y="316" text-anchor="middle" font-size="12" fill="{GRAY}">slide &amp; rotate blue → orange</text>'
)
# right: 6DOF legend
def tline(y, icon, name, desc, color):
    return (icon + f'<text x="437" y="{y+5}" font-size="12.5" font-weight="bold" fill="{color}">{name}</text>'
            f'<text x="487" y="{y+5}" font-size="12" fill="{INK}">{desc}</text>')
def transicon(y):
    return darrow(396,y,424,y,TEAL)
def roticon(y):
    return (f'<path d="M398,{y+6} A12 12 0 1 1 420,{y-2}" stroke="{AMBER}" stroke-width="2" fill="none"/>'
            f'<polygon points="420,{y-2} 414,{y-8} 424,{y-9}" fill="{AMBER}"/>')
right = (
    f'<text x="500" y="60" text-anchor="middle" font-size="14" font-weight="bold" fill="{DARK}">2 · Couch correction (6 DOF)</text>'
    f'<text x="388" y="86" font-size="12" font-weight="bold" fill="{TEAL}">Translations (slide)</text>'
    + tline(112, transicon(112), "Lat", "left ↔ right", TEAL)
    + tline(140, transicon(140), "Long", "head ↔ feet", TEAL)
    + tline(168, transicon(168), "Vert", "up ↕ down", TEAL)
    + f'<text x="388" y="210" font-size="12" font-weight="bold" fill="{AMBER}">Rotations (tilt / twist)</text>'
    + tline(236, roticon(236), "Pitch", "nod — “yes”", AMBER)
    + tline(264, roticon(264), "Roll", "tilt head to shoulder", AMBER)
    + tline(292, roticon(292), "Yaw", "turn — “no”", AMBER)
)
figs["fig6-igrt-6dof.svg"] = wrap(740, 340,
    f'<text x="370" y="26" text-anchor="middle" font-size="17" font-weight="bold" fill="{DARK}">Image Match → 6-DOF Couch Correction</text>'
    + f'<g transform="translate(0,10)">{left}</g>'
    + f'<line x1="350" y1="50" x2="350" y2="320" stroke="#dde6ec"/>'
    + f'<g transform="translate(0,10)">{right}</g>')

for name, svg in figs.items():
    with open(os.path.join(FIG, name), "w", encoding="utf-8") as f:
        f.write(svg)
print("wrote", len(figs), "Ch6 figures")
for n in figs: print(" -", n)
