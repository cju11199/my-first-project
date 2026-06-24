#!/usr/bin/env python3
"""Generate labeled SVG diagrams for the radiation physics chapter."""
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

# 1. Cobalt-60 decay scheme
figs["fig-co60-decay.svg"] = wrap(560, 320, f'''
<text x="280" y="28" text-anchor="middle" font-size="17" font-weight="bold" fill="{DARK}">Cobalt-60 Decay Scheme</text>
<line x1="70" y1="70" x2="230" y2="70" stroke="{DARK}" stroke-width="3"/>
<text x="70" y="60" font-size="14" fill="{DARK}">⁶⁰Co  (half-life 5.27 yr)</text>
<line x1="300" y1="135" x2="490" y2="135" stroke="{TEAL}" stroke-width="3"/>
<text x="300" y="125" font-size="13" fill="{TEAL}">⁶⁰Ni* (excited)</text>
<!-- beta arrow -->
<line x1="150" y1="70" x2="360" y2="133" stroke="{GREEN}" stroke-width="2.5"/>
<polygon points="360,133 348,124 350,136" fill="{GREEN}"/>
<text x="232" y="108" font-size="13" fill="{GREEN}">β⁻  (~0.31 MeV)</text>
<line x1="300" y1="205" x2="490" y2="205" stroke="{TEAL}" stroke-width="3"/>
<!-- gamma 1 -->
<line x1="395" y1="135" x2="395" y2="203" stroke="{AMBER}" stroke-width="2.5"/>
<polygon points="395,203 389,190 401,190" fill="{AMBER}"/>
<text x="405" y="175" font-size="14" fill="{AMBER}">γ₁ = 1.17 MeV</text>
<line x1="300" y1="275" x2="490" y2="275" stroke="{DARK}" stroke-width="3"/>
<text x="300" y="297" font-size="13" fill="{DARK}">⁶⁰Ni (stable)</text>
<!-- gamma 2 -->
<line x1="395" y1="205" x2="395" y2="273" stroke="{AMBER}" stroke-width="2.5"/>
<polygon points="395,273 389,260 401,260" fill="{AMBER}"/>
<text x="405" y="245" font-size="14" fill="{AMBER}">γ₂ = 1.33 MeV</text>
''')

# 2. Bremsstrahlung production
figs["fig-bremsstrahlung.svg"] = wrap(560, 280, f'''
<text x="280" y="28" text-anchor="middle" font-size="17" font-weight="bold" fill="{DARK}">Bremsstrahlung ("braking radiation")</text>
<!-- nucleus -->
<circle cx="300" cy="150" r="22" fill="{DARK}"/>
<text x="300" y="155" text-anchor="middle" font-size="13" fill="white">+</text>
<text x="300" y="200" text-anchor="middle" font-size="12" fill="{GRAY}">nucleus (high Z, e.g. tungsten)</text>
<!-- incoming electron -->
<line x1="60" y1="150" x2="262" y2="150" stroke="{TEAL}" stroke-width="2.5"/>
<polygon points="262,150 248,143 248,157" fill="{TEAL}"/>
<text x="70" y="140" font-size="13" fill="{TEAL}">fast electron (e⁻)</text>
<!-- deflected electron -->
<path d="M322,140 Q400,110 470,80" stroke="{TEAL}" stroke-width="2.5" fill="none"/>
<polygon points="470,80 456,82 462,93" fill="{TEAL}"/>
<text x="430" y="70" font-size="12" fill="{TEAL}">slowed, bent e⁻</text>
<!-- emitted photon (wavy) -->
<path d="M312,168 q10,12 20,0 q10,-12 20,0 q10,12 20,0 q10,-12 20,0 q10,12 20,0" stroke="{AMBER}" stroke-width="2.5" fill="none"/>
<polygon points="432,168 418,161 418,175" fill="{AMBER}"/>
<text x="345" y="205" font-size="13" fill="{AMBER}">X-ray photon</text>
<text x="60" y="250" font-size="12" fill="{GRAY}">The electron is deflected by the nucleus, loses energy, and that lost energy leaves as an x-ray.</text>
''')

# 3. Three photon interactions (3 panels)
def atom(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{GRAY}" stroke-width="1.5"/>'
            f'<circle cx="{cx}" cy="{cy}" r="9" fill="{DARK}"/>')
panelW=240
pA=f'''<text x="120" y="30" text-anchor="middle" font-size="14" font-weight="bold" fill="{DARK}">Photoelectric</text>
{atom(120,120)}
<line x1="20" y1="120" x2="92" y2="120" stroke="{AMBER}" stroke-width="2.5"/>
<polygon points="92,120 80,114 80,126" fill="{AMBER}"/>
<text x="20" y="110" font-size="11" fill="{AMBER}">photon</text>
<line x1="120" y1="111" x2="185" y2="60" stroke="{TEAL}" stroke-width="2.5"/>
<polygon points="185,60 172,66 178,73" fill="{TEAL}"/>
<text x="150" y="52" font-size="11" fill="{TEAL}">photoelectron</text>
<text x="120" y="175" text-anchor="middle" font-size="11" fill="{GRAY}">photon fully absorbed</text>
<text x="120" y="192" text-anchor="middle" font-size="11" fill="{GRAY}">low energy · high Z</text>'''
pB=f'''<text x="120" y="30" text-anchor="middle" font-size="14" font-weight="bold" fill="{DARK}">Compton scatter</text>
{atom(120,120)}
<line x1="20" y1="120" x2="92" y2="120" stroke="{AMBER}" stroke-width="2.5"/>
<polygon points="92,120 80,114 80,126" fill="{AMBER}"/>
<text x="20" y="110" font-size="11" fill="{AMBER}">photon</text>
<path d="M148,108 l50,-34" stroke="{AMBER}" stroke-width="2.5" fill="none" stroke-dasharray="1 0"/>
<polygon points="198,74 185,79 191,86" fill="{AMBER}"/>
<text x="170" y="66" font-size="11" fill="{AMBER}">scattered photon</text>
<line x1="120" y1="129" x2="180" y2="170" stroke="{TEAL}" stroke-width="2.5"/>
<polygon points="180,170 167,164 165,176" fill="{TEAL}"/>
<text x="150" y="188" font-size="11" fill="{TEAL}">recoil e⁻</text>
<text x="120" y="205" text-anchor="middle" font-size="11" fill="{RED}">dominant at MV therapy energies</text>'''
pC=f'''<text x="120" y="30" text-anchor="middle" font-size="14" font-weight="bold" fill="{DARK}">Pair production</text>
{atom(120,120)}
<line x1="20" y1="120" x2="92" y2="120" stroke="{AMBER}" stroke-width="2.5"/>
<polygon points="92,120 80,114 80,126" fill="{AMBER}"/>
<text x="20" y="110" font-size="11" fill="{AMBER}">photon</text>
<line x1="120" y1="120" x2="190" y2="78" stroke="{TEAL}" stroke-width="2.5"/>
<polygon points="190,78 177,83 183,90" fill="{TEAL}"/>
<text x="193" y="74" font-size="12" fill="{TEAL}">e⁻</text>
<line x1="120" y1="120" x2="190" y2="162" stroke="{RED}" stroke-width="2.5"/>
<polygon points="190,162 177,157 183,150" fill="{RED}"/>
<text x="193" y="166" font-size="12" fill="{RED}">e⁺</text>
<text x="120" y="188" text-anchor="middle" font-size="11" fill="{GRAY}">threshold &gt; 1.02 MeV</text>'''
body3 = (f'<g transform="translate(0,12)">{pA}</g>'
         f'<line x1="244" y1="20" x2="244" y2="225" stroke="#dde6ec"/>'
         f'<g transform="translate(244,12)">{pB}</g>'
         f'<line x1="488" y1="20" x2="488" y2="225" stroke="#dde6ec"/>'
         f'<g transform="translate(488,12)">{pC}</g>')
figs["fig-photon-interactions.svg"] = wrap(732, 250, body3)

# 4. Interaction dominance vs energy and Z
figs["fig-interaction-dominance.svg"] = wrap(580, 360, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Which interaction dominates?</text>
<line x1="70" y1="300" x2="540" y2="300" stroke="{INK}" stroke-width="1.5"/>
<line x1="70" y1="300" x2="70" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="305" y="335" text-anchor="middle" font-size="13" fill="{INK}">Photon energy  →  (0.01 → 100 MeV, log scale)</text>
<text x="34" y="180" text-anchor="middle" font-size="13" fill="{INK}" transform="rotate(-90 34 180)">Atomic number Z →</text>
<!-- left curve: PE = Compton -->
<path d="M120,300 C150,200 175,120 220,60" stroke="{TEAL}" stroke-width="2.5" fill="none"/>
<!-- right curve: Compton = Pair -->
<path d="M360,300 C400,200 430,120 480,60" stroke="{AMBER}" stroke-width="2.5" fill="none"/>
<text x="95" y="120" font-size="14" font-weight="bold" fill="{TEAL}">Photoelectric</text>
<text x="100" y="138" font-size="11" fill="{GRAY}">(low E, high Z)</text>
<text x="250" y="250" font-size="14" font-weight="bold" fill="{RED}">Compton</text>
<text x="232" y="268" font-size="11" fill="{GRAY}">(the megavoltage therapy band)</text>
<text x="470" y="150" font-size="14" font-weight="bold" fill="{AMBER}">Pair</text>
<text x="455" y="168" font-size="14" font-weight="bold" fill="{AMBER}">production</text>
<text x="452" y="186" font-size="11" fill="{GRAY}">(high E, high Z)</text>
''')

# 5. Inverse square law
figs["fig-inverse-square.svg"] = wrap(580, 300, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Inverse-Square Law</text>
<circle cx="60" cy="160" r="9" fill="{AMBER}"/>
<text x="40" y="195" font-size="12" fill="{AMBER}">source</text>
<!-- diverging rays -->
<line x1="60" y1="160" x2="520" y2="60" stroke="{GRAY}" stroke-width="1"/>
<line x1="60" y1="160" x2="520" y2="260" stroke="{GRAY}" stroke-width="1"/>
<!-- squares at 1d, 2d, 3d -->
<rect x="180" y="135" width="50" height="50" fill="{TEAL}" fill-opacity="0.30" stroke="{TEAL}"/>
<rect x="320" y="110" width="100" height="100" fill="{TEAL}" fill-opacity="0.18" stroke="{TEAL}"/>
<rect x="455" y="85" width="65" height="150" fill="none"/>
<text x="205" y="210" text-anchor="middle" font-size="12" fill="{DARK}">1d</text>
<text x="370" y="232" text-anchor="middle" font-size="12" fill="{DARK}">2d</text>
<text x="180" y="125" font-size="11" fill="{DARK}">area ×1</text>
<text x="322" y="100" font-size="11" fill="{DARK}">area ×4</text>
<text x="180" y="270" font-size="13" fill="{TEAL}">intensity 1</text>
<text x="322" y="270" font-size="13" fill="{TEAL}">→ 1/4</text>
<text x="430" y="270" font-size="13" fill="{TEAL}">→ 1/9 …</text>
<text x="300" y="293" text-anchor="middle" font-size="12" fill="{GRAY}">Double the distance → one-quarter the dose rate.  D₂ = D₁ × (d₁/d₂)²</text>
''')

# 6. Exponential attenuation & HVL
figs["fig-attenuation-hvl.svg"] = wrap(580, 320, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Exponential Attenuation &amp; Half-Value Layer</text>
<line x1="70" y1="270" x2="540" y2="270" stroke="{INK}" stroke-width="1.5"/>
<line x1="70" y1="270" x2="70" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="305" y="305" text-anchor="middle" font-size="13" fill="{INK}">Thickness of shielding  →</text>
<text x="40" y="165" text-anchor="middle" font-size="13" fill="{INK}" transform="rotate(-90 40 165)">Beam intensity →</text>
<path d="M70,70 C150,150 210,205 290,228 C360,247 440,258 540,263" stroke="{TEAL}" stroke-width="3" fill="none"/>
<!-- HVL markers -->
<line x1="70" y1="70" x2="540" y2="70" stroke="#dde6ec" stroke-dasharray="3 3"/>
<line x1="187" y1="149" x2="187" y2="270" stroke="{AMBER}" stroke-dasharray="4 3"/>
<line x1="304" y1="189" x2="304" y2="270" stroke="{AMBER}" stroke-dasharray="4 3"/>
<line x1="421" y1="229" x2="421" y2="270" stroke="{AMBER}" stroke-dasharray="4 3"/>
<text x="46" y="74" font-size="11" fill="{GRAY}">100%</text>
<text x="150" y="144" font-size="11" fill="{AMBER}">50% (1 HVL)</text>
<text x="300" y="184" font-size="11" fill="{AMBER}">25% (2)</text>
<text x="405" y="223" font-size="11" fill="{AMBER}">12.5% (3)</text>
''')

# 7. Percent depth dose / buildup
figs["fig-depth-dose.svg"] = wrap(580, 320, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Depth Dose of a Megavoltage Beam</text>
<line x1="70" y1="270" x2="540" y2="270" stroke="{INK}" stroke-width="1.5"/>
<line x1="70" y1="270" x2="70" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="305" y="305" text-anchor="middle" font-size="13" fill="{INK}">Depth in tissue (cm)  →</text>
<text x="40" y="165" text-anchor="middle" font-size="13" fill="{INK}" transform="rotate(-90 40 165)">% dose →</text>
<path d="M70,205 C95,150 125,80 165,72 C230,60 330,150 540,250" stroke="{TEAL}" stroke-width="3" fill="none"/>
<line x1="165" y1="72" x2="165" y2="270" stroke="{AMBER}" stroke-dasharray="4 3"/>
<text x="150" y="64" font-size="12" fill="{AMBER}">d_max (100%)</text>
<circle cx="70" cy="205" r="4" fill="{RED}"/>
<text x="78" y="200" font-size="11" fill="{RED}">low skin dose</text>
<text x="95" y="150" font-size="11" fill="{GRAY}">build-up</text>
<text x="100" y="165" font-size="11" fill="{GRAY}">region</text>
<text x="330" y="200" font-size="11" fill="{GRAY}">fall-off with depth</text>
''')

# 8. Cell survival curve (LQ), low vs high LET
figs["fig-cell-survival.svg"] = wrap(580, 330, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Cell Survival Curve (Linear-Quadratic)</text>
<line x1="80" y1="280" x2="540" y2="280" stroke="{INK}" stroke-width="1.5"/>
<line x1="80" y1="280" x2="80" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="310" y="312" text-anchor="middle" font-size="13" fill="{INK}">Dose (Gy)  →</text>
<text x="40" y="170" text-anchor="middle" font-size="12" fill="{INK}" transform="rotate(-90 40 170)">Surviving fraction (log) →</text>
<text x="52" y="72" font-size="10" fill="{GRAY}">1</text>
<text x="44" y="170" font-size="10" fill="{GRAY}">0.1</text>
<text x="36" y="268" font-size="10" fill="{GRAY}">0.01</text>
<!-- low-LET curve: shoulder then bend -->
<path d="M80,70 C150,78 200,100 260,150 C320,200 400,255 520,278" stroke="{TEAL}" stroke-width="3" fill="none"/>
<text x="300" y="150" font-size="12" fill="{TEAL}">low-LET (x-rays): shoulder</text>
<!-- high-LET: straight steep -->
<path d="M80,70 L300,278" stroke="{RED}" stroke-width="2.5" fill="none" stroke-dasharray="6 4"/>
<text x="150" y="250" font-size="12" fill="{RED}">high-LET: straighter, steeper</text>
<text x="120" y="100" font-size="11" fill="{GRAY}">shoulder = repair of</text>
<text x="120" y="115" font-size="11" fill="{GRAY}">sublethal damage</text>
''')

# 9. Oxygen effect
figs["fig-oxygen-effect.svg"] = wrap(580, 320, f'''
<text x="290" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">The Oxygen Effect (OER)</text>
<line x1="80" y1="275" x2="540" y2="275" stroke="{INK}" stroke-width="1.5"/>
<line x1="80" y1="275" x2="80" y2="55" stroke="{INK}" stroke-width="1.5"/>
<text x="310" y="305" text-anchor="middle" font-size="13" fill="{INK}">Dose (Gy)  →</text>
<text x="40" y="165" text-anchor="middle" font-size="12" fill="{INK}" transform="rotate(-90 40 165)">Surviving fraction (log) →</text>
<!-- oxic curve (more sensitive, left) -->
<path d="M80,68 C140,90 190,140 250,205 C290,248 320,265 360,272" stroke="{TEAL}" stroke-width="3" fill="none"/>
<text x="150" y="150" font-size="12" fill="{TEAL}">oxygenated (sensitive)</text>
<!-- hypoxic curve (resistant, right) -->
<path d="M80,68 C170,82 250,120 330,180 C400,232 450,260 510,272" stroke="{RED}" stroke-width="3" fill="none"/>
<text x="360" y="150" font-size="12" fill="{RED}">hypoxic (resistant)</text>
<!-- OER bracket -->
<line x1="300" y1="230" x2="430" y2="230" stroke="{DARK}" stroke-dasharray="3 3"/>
<text x="312" y="222" font-size="12" fill="{DARK}">OER ≈ 2.5–3×</text>
''')

# 10. Deterministic vs stochastic
figs["fig-deterministic-stochastic.svg"] = wrap(640, 290, f'''
<text x="320" y="26" text-anchor="middle" font-size="16" font-weight="bold" fill="{DARK}">Deterministic vs. Stochastic Effects</text>
<!-- left: deterministic -->
<line x1="60" y1="240" x2="290" y2="240" stroke="{INK}" stroke-width="1.5"/>
<line x1="60" y1="240" x2="60" y2="60" stroke="{INK}" stroke-width="1.5"/>
<path d="M60,240 L150,240 C190,240 200,120 240,90 C255,80 270,76 285,74" stroke="{TEAL}" stroke-width="3" fill="none"/>
<line x1="150" y1="240" x2="150" y2="60" stroke="{AMBER}" stroke-dasharray="4 3"/>
<text x="155" y="80" font-size="12" fill="{AMBER}">threshold</text>
<text x="175" y="270" text-anchor="middle" font-size="13" fill="{DARK}">Deterministic</text>
<text x="175" y="287" text-anchor="middle" font-size="10" fill="{GRAY}">severity rises after a threshold</text>
<text x="20" y="150" font-size="11" fill="{INK}" transform="rotate(-90 20 150)">severity →</text>
<!-- right: stochastic -->
<line x1="370" y1="240" x2="600" y2="240" stroke="{INK}" stroke-width="1.5"/>
<line x1="370" y1="240" x2="370" y2="60" stroke="{INK}" stroke-width="1.5"/>
<line x1="370" y1="240" x2="585" y2="80" stroke="{RED}" stroke-width="3"/>
<text x="485" y="270" text-anchor="middle" font-size="13" fill="{DARK}">Stochastic</text>
<text x="485" y="287" text-anchor="middle" font-size="10" fill="{GRAY}">probability rises, no threshold</text>
<text x="330" y="150" font-size="11" fill="{INK}" transform="rotate(-90 330 150)">probability →</text>
<text x="378" y="248" font-size="10" fill="{GRAY}">0</text>
''')

for name, svg in figs.items():
    with open(os.path.join(FIG, name), "w", encoding="utf-8") as f:
        f.write(svg)
print("wrote", len(figs), "figures to", FIG)
for n in figs: print(" -", n)
