#!/usr/bin/env python3
"""Generate labeled SVG diagrams for the dose-calculation (math) chapter."""
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

# 1. SSD vs SAD setup geometry
def setup_panel(title, dist_label, surface_y, point_y, point_label, tables, iso=False):
    src = (f'<rect x="148" y="40" width="48" height="18" rx="2" fill="{DARK}"/>'
           f'<text x="172" y="53" text-anchor="middle" font-size="11" fill="white">source</text>')
    beam = (f'<line x1="172" y1="58" x2="88" y2="288" stroke="{GRAY}" stroke-width="1"/>'
            f'<line x1="172" y1="58" x2="256" y2="288" stroke="{GRAY}" stroke-width="1"/>')
    surface = (f'<line x1="78" y1="{surface_y}" x2="266" y2="{surface_y}" stroke="{INK}" stroke-width="1.5"/>'
               f'<text x="270" y="{surface_y+4}" font-size="10" fill="{INK}">skin</text>')
    # fixed-distance double arrow at x=44
    arrow = (f'<line x1="44" y1="58" x2="44" y2="{point_y if iso else surface_y}" stroke="{AMBER}" stroke-width="1.5"/>'
             f'<polygon points="44,58 40,68 48,68" fill="{AMBER}"/>'
             f'<polygon points="44,{(point_y if iso else surface_y)} 40,{(point_y if iso else surface_y)-10} 48,{(point_y if iso else surface_y)-10}" fill="{AMBER}"/>'
             f'<text x="20" y="175" font-size="11" fill="{AMBER}" transform="rotate(-90 20 175)">{dist_label}</text>')
    pt = (f'<line x1="172" y1="{surface_y}" x2="172" y2="{point_y}" stroke="{TEAL}" stroke-width="1.4" stroke-dasharray="3 3"/>'
          f'<circle cx="172" cy="{point_y}" r="5" fill="{TEAL}"/>'
          f'<text x="182" y="{point_y+4}" font-size="10" fill="{TEAL}">{point_label}</text>')
    cross = ''
    if iso:
        cross = (f'<line x1="162" y1="{point_y}" x2="182" y2="{point_y}" stroke="{TEAL}" stroke-width="1.4"/>')
    t = (f'<text x="172" y="26" text-anchor="middle" font-size="13" font-weight="bold" fill="{DARK}">{title}</text>'
         f'<text x="172" y="322" text-anchor="middle" font-size="12" fill="{TEAL}">{tables}</text>')
    return t+arrow+src+beam+surface+pt+cross
left = setup_panel("SSD (fixed-distance) setup", "SSD 100 cm: source → skin",
                   200, 270, "point at depth d", "uses PDD tables", iso=False)
right = setup_panel("SAD (isocentric) setup", "SAD 100 cm: source → isocenter",
                    210, 280, "isocenter at depth d", "uses TMR / TPR tables", iso=True)
figs["fig7-ssd-vs-sad.svg"] = wrap(720, 340,
    f'<g>{left}</g><line x1="360" y1="20" x2="360" y2="320" stroke="#dde6ec"/><g transform="translate(360,0)">{right}</g>')

# 2. Equivalent square
figs["fig7-equivalent-square.svg"] = wrap(580, 270, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Equivalent Square of a Rectangle</text>
<rect x="70" y="70" width="150" height="90" fill="{TEAL}" fill-opacity="0.18" stroke="{TEAL}" stroke-width="2"/>
<text x="145" y="180" text-anchor="middle" font-size="12" fill="{DARK}">a = 10 cm</text>
<text x="56" y="118" text-anchor="middle" font-size="12" fill="{DARK}" transform="rotate(-90 56 118)">b = 6 cm</text>
<text x="250" y="120" font-size="26" fill="{GRAY}">→</text>
<rect x="300" y="78" width="112" height="112" fill="{AMBER}" fill-opacity="0.18" stroke="{AMBER}" stroke-width="2"/>
<text x="356" y="208" text-anchor="middle" font-size="12" fill="{DARK}">7.5 cm × 7.5 cm</text>
<text x="290" y="248" text-anchor="middle" font-size="13" fill="{INK}">Equivalent square = 2ab/(a+b) = 2(10)(6)/16 = 7.5 cm</text>
''')

# 3. Anatomy of the MU equation
figs["fig7-mu-anatomy.svg"] = wrap(660, 320, f'''
<text x="330" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Anatomy of the SAD Monitor-Unit Equation</text>
<text x="330" y="92" text-anchor="middle" font-size="20" fill="{INK}">MU = Dose ÷ ( D₀ × TMR × S_c × S_p × WF × TF )</text>
<line x1="150" y1="105" x2="150" y2="150" stroke="{TEAL}" stroke-width="1.3"/>
<text x="150" y="170" text-anchor="middle" font-size="11" fill="{TEAL}">D₀: machine</text>
<text x="150" y="184" text-anchor="middle" font-size="11" fill="{TEAL}">output (cGy/MU)</text>
<line x1="245" y1="105" x2="245" y2="205" stroke="{AMBER}" stroke-width="1.3"/>
<text x="245" y="225" text-anchor="middle" font-size="11" fill="{AMBER}">TMR: depth +</text>
<text x="245" y="239" text-anchor="middle" font-size="11" fill="{AMBER}">field-size factor</text>
<line x1="330" y1="105" x2="330" y2="150" stroke="{DARK}" stroke-width="1.3"/>
<text x="330" y="170" text-anchor="middle" font-size="11" fill="{DARK}">S_c: collimator</text>
<text x="330" y="184" text-anchor="middle" font-size="11" fill="{DARK}">(head) scatter</text>
<line x1="395" y1="105" x2="395" y2="205" stroke="{GREEN}" stroke-width="1.3"/>
<text x="395" y="225" text-anchor="middle" font-size="11" fill="{GREEN}">S_p: phantom</text>
<text x="395" y="239" text-anchor="middle" font-size="11" fill="{GREEN}">(patient) scatter</text>
<line x1="470" y1="105" x2="470" y2="150" stroke="{RED}" stroke-width="1.3"/>
<text x="470" y="170" text-anchor="middle" font-size="11" fill="{RED}">WF: wedge</text>
<text x="470" y="184" text-anchor="middle" font-size="11" fill="{RED}">factor</text>
<line x1="525" y1="105" x2="525" y2="205" stroke="{GRAY}" stroke-width="1.3"/>
<text x="525" y="225" text-anchor="middle" font-size="11" fill="{GRAY}">TF: tray /</text>
<text x="525" y="239" text-anchor="middle" font-size="11" fill="{GRAY}">block factor</text>
<text x="330" y="285" text-anchor="middle" font-size="12" fill="{GRAY}">Every factor in the denominator that makes less dose per MU → more MUs are needed.</text>
''')

# 4. Wedge isodose tilt
figs["fig7-wedge.svg"] = wrap(560, 300, f'''
<text x="280" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">A Wedge Tilts the Isodose Lines</text>
<!-- beam arrows -->
<line x1="150" y1="45" x2="150" y2="78" stroke="{AMBER}" stroke-width="2"/><polygon points="150,78 145,68 155,68" fill="{AMBER}"/>
<line x1="280" y1="45" x2="280" y2="78" stroke="{AMBER}" stroke-width="2"/><polygon points="280,78 275,68 285,68" fill="{AMBER}"/>
<line x1="410" y1="45" x2="410" y2="78" stroke="{AMBER}" stroke-width="2"/><polygon points="410,78 405,68 415,68" fill="{AMBER}"/>
<text x="280" y="42" text-anchor="middle" font-size="11" fill="{AMBER}">beam</text>
<!-- wedge (triangle): thick on left -->
<polygon points="120,85 450,85 450,120 120,150" fill="{DARK}" fill-opacity="0.85"/>
<text x="150" y="110" font-size="11" fill="white">thick (heel)</text>
<text x="380" y="112" font-size="11" fill="white">thin (toe)</text>
<!-- patient box -->
<rect x="120" y="160" width="330" height="110" fill="{LIGHT}" stroke="#cdd9e0"/>
<!-- tilted isodose lines -->
<line x1="135" y1="200" x2="440" y2="180" stroke="{TEAL}" stroke-width="2"/>
<line x1="135" y1="230" x2="440" y2="208" stroke="{TEAL}" stroke-width="2"/>
<line x1="135" y1="258" x2="440" y2="236" stroke="{TEAL}" stroke-width="2"/>
<text x="455" y="184" font-size="10" fill="{TEAL}">isodose</text>
<text x="455" y="196" font-size="10" fill="{TEAL}">lines tilt</text>
''')

# 5. Field junction gap
figs["fig7-gap.svg"] = wrap(580, 320, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Field-Junction Gap</text>
<rect x="40" y="44" width="80" height="16" rx="2" fill="{DARK}"/><text x="80" y="57" text-anchor="middle" font-size="10" fill="white">field 1</text>
<rect x="460" y="44" width="80" height="16" rx="2" fill="{DARK}"/><text x="500" y="57" text-anchor="middle" font-size="10" fill="white">field 2</text>
<!-- skin line -->
<line x1="40" y1="150" x2="540" y2="150" stroke="{INK}" stroke-width="1.5"/>
<text x="544" y="154" font-size="10" fill="{INK}">skin</text>
<!-- diverging edges of field 1 (from source1 at 80,60) -->
<line x1="80" y1="60" x2="250" y2="250" stroke="{TEAL}" stroke-width="1.8"/>
<line x1="80" y1="60" x2="200" y2="150" stroke="{GRAY}" stroke-width="1" stroke-dasharray="3 3"/>
<!-- diverging edges of field 2 (from source2 at 500,60) -->
<line x1="500" y1="60" x2="330" y2="250" stroke="{AMBER}" stroke-width="1.8"/>
<line x1="500" y1="60" x2="380" y2="150" stroke="{GRAY}" stroke-width="1" stroke-dasharray="3 3"/>
<!-- gap bracket at skin -->
<line x1="200" y1="138" x2="380" y2="138" stroke="{RED}" stroke-width="1.4"/>
<text x="290" y="132" text-anchor="middle" font-size="12" fill="{RED}">gap at skin (g)</text>
<!-- meeting point at depth -->
<circle cx="290" cy="250" r="5" fill="{GREEN}"/>
<text x="300" y="254" font-size="11" fill="{GREEN}">fields meet at depth d</text>
<text x="290" y="298" text-anchor="middle" font-size="12" fill="{GRAY}">Gap = (L/2) × (d / SSD) per field — leave a skin gap so the beams meet at depth.</text>
''')

# 6. Electron depth dose with Rp, R90, R50
figs["fig7-electron-depthdose.svg"] = wrap(580, 330, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Electron Depth Dose</text>
<line x1="70" y1="270" x2="540" y2="270" stroke="{INK}" stroke-width="1.5"/>
<line x1="70" y1="270" x2="70" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="305" y="305" text-anchor="middle" font-size="13" fill="{INK}">Depth in tissue (cm) →</text>
<text x="40" y="165" text-anchor="middle" font-size="12" fill="{INK}" transform="rotate(-90 40 165)">% dose →</text>
<!-- high surface dose, quick dmax, steep fall, brems tail -->
<path d="M70,110 C100,85 120,72 150,72 C185,72 215,120 250,180 C275,222 300,250 330,262 C370,276 440,276 540,276" stroke="{TEAL}" stroke-width="3" fill="none"/>
<!-- dmax -->
<line x1="150" y1="72" x2="150" y2="270" stroke="{AMBER}" stroke-dasharray="4 3"/>
<text x="120" y="64" font-size="11" fill="{AMBER}">d_max (100%)</text>
<!-- R90 -->
<line x1="205" y1="100" x2="205" y2="270" stroke="{GRAY}" stroke-dasharray="3 3"/>
<text x="196" y="92" font-size="10" fill="{GRAY}">R₉₀</text>
<!-- R50 -->
<line x1="278" y1="172" x2="278" y2="270" stroke="{GRAY}" stroke-dasharray="3 3"/>
<text x="270" y="166" font-size="10" fill="{GRAY}">R₅₀</text>
<!-- Rp: extrapolate steep slope to axis -->
<line x1="250" y1="180" x2="360" y2="270" stroke="{RED}" stroke-width="1.2" stroke-dasharray="5 4"/>
<text x="350" y="262" font-size="10" fill="{RED}">R_p</text>
<text x="400" y="250" font-size="10" fill="{GRAY}">bremsstrahlung tail</text>
<text x="80" y="100" font-size="10" fill="{TEAL}">high surface dose</text>
''')

# 7. Dose-volume histogram
figs["fig7-dvh.svg"] = wrap(580, 320, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Reading a Dose-Volume Histogram (DVH)</text>
<line x1="75" y1="265" x2="540" y2="265" stroke="{INK}" stroke-width="1.5"/>
<line x1="75" y1="265" x2="75" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="305" y="300" text-anchor="middle" font-size="13" fill="{INK}">Dose (% of prescription) →</text>
<text x="42" y="165" text-anchor="middle" font-size="12" fill="{INK}" transform="rotate(-90 42 165)">Volume (%) →</text>
<!-- target: flat near 100% then sharp cliff near 100% dose -->
<path d="M75,70 L360,70 C400,70 415,120 430,200 C438,240 445,262 470,265" stroke="{TEAL}" stroke-width="3" fill="none"/>
<text x="150" y="62" font-size="11" fill="{TEAL}">target (want a sharp cliff near Rx)</text>
<!-- OAR: drops early/left -->
<path d="M75,70 C120,120 160,200 220,245 C260,262 300,265 340,265" stroke="{RED}" stroke-width="3" fill="none"/>
<text x="250" y="150" font-size="11" fill="{RED}">organ at risk (want it low &amp; to the left)</text>
''')

for name, svg in figs.items():
    with open(os.path.join(FIG, name), "w", encoding="utf-8") as f:
        f.write(svg)
print("wrote", len(figs), "Ch7 figures")
for n in figs: print(" -", n)
