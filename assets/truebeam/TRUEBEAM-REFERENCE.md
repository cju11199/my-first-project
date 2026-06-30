# Varian TrueBeam — Parts & Appearance Reference (for the 3D model)

> Compiled by a multi-agent research pass (architecture · head · imaging · couch · covers).
> Sizes/hexes are best-fit modelling approximations from product photography + radiotherapy-physics
> domain knowledge, not certified Varian spec. Treat ±10–20% on sizes as fine for a low-poly model.

## 1. Overall form

Open **C-arm** medical linac: one radiation head swings in a vertical circle around a patient in
free, open space — **not** a closed CT/MRI bore. Defining silhouette: a large rotating off-white
**drum** emerging from a clean rectangular floor **stand**, the treatment **head** cantilevered off
the drum, and a flat carbon-fibre **couch** projecting horizontally into the open arc so the target
sits at isocentre. Smoothly-radiused matte off-white/cream shells, no visible fasteners, broken only
by one warm **beige collimator/accessory face** at the beam exit and a restrained blue **trueBEAM**
wordmark on the drum. Three foldout flat-panel arms (kV source, kV detector, MV/EPID) fan into a
perpendicular cross when deployed and tuck flat when stowed.

Geometry: origin = isocentre, metres, IEC 61217. SAD = 1.000 m. Iso ≈ 1.28 m above floor. kV SAD
1.00 m / kV SDD ≈ 1.50 m / MV EPID SID ≈ 1.50 m. Radial clearance iso→nearest head face ≈ 0.40–0.45 m.

## 2. Parts list

### A. Gantry / Stand
- **A1 Fixed drive stand** — rounded-rectangular off-white plinth ~1.5–2.0 w × 0.7–1.5 d × 1.5–2.2 h m, behind iso (front face ~0.4–0.5 m behind iso). Houses rotation drive, bearing, counterweights.
- **A2 Rotating gantry drum** ★★ — large circular off-white disc/"clock face", dia ~1.4–1.8 m, axial depth ~0.5–0.8 m, faint concentric ring, carries the blue trueBEAM mark. Rotates ±185°.
- **A3 C-arm gantry arm** — thick smoothly-curved open-C cream arm, ~0.4–0.6 m cross-section, holds the MV source at exactly 1.000 m from iso. Open arch, patient visible inside.
- **A5 Counterweight** (internal) — model proportions "massive and planted", not on legs.

### B. Treatment Head (top→bottom). Externally visible = head shell + beige face.
- **B6 Secondary jaws (X & Y)** — 4 dark tungsten blocks, set up to 40×40 cm field.
- **B7 MLC** — comb of thin tungsten leaves, two banks of 60. Millennium 120 (central 5 mm) or HD120 (central 2.5 mm).
- **B8 Rotating collimator** — whole secondary stack rotates about the beam (±180°); the circular head underside IS this.
- **B9 Circular collimator face** ★ — large flat/slightly-domed **beige** disc ~0.5–0.6 m dia, central aperture + cross-wire graticule. The iconic "look up into a TrueBeam" view.
- **B10 Beige accessory/wedge tray + slide rails** ★ — warm-beige bezel ~30–40 cm, horizontal rails, slotted/ribbed, warmer/darker than the white shells. Lowest face of the head.
- **B11 Head shell** — rounded off-white box ~0.6–0.8 m, cantilevered at SAD, beige on its lower beam-exit face.

### C. On-Board Imaging (three foldout arms, two axes)
- **C1 kV source (KVS)** ★ — multi-segment cream robotic "Exact arm" ending in a chunky ~25×25×30 cm kV tube + blade collimator, mounted 90° to MV beam, deploys to kV SAD 100 cm. Folds flush when stowed.
- **C2 kV detector (KVD)** ★ — matching cream arm holding a thin a-Si flat panel (~30×40 active, ~40×40 housing, 3–5 cm thick), opposite KVS at kV SDD ≈ 150 cm. **Slides laterally** (centred ↔ offset 14.6 cm).
- **C3 MV EPID (aS1200)** ★ — folding cream arm with a flat a-Si panel ~40×40 cm active, **visibly thicker (~6–10 cm)** than the kV panel; hangs opposite the head along the MV axis (below couch at G0), SID ~150 cm.
- **C4 CBCT** — functional mode: both kV arms held out, sweeping with the gantry.

### D. Treatment Couch (6DOF, side cantilever, no leg under the patient end)
- **D1 Floor base** — low rounded off-white plinth ~0.9–1.1 × 0.6–0.8 × 0.12–0.18 m.
- **D2 Vertical column** — smooth white tower ~0.9–1.3 m tall, telescopes; Vrt travel ~0.44 m.
- **D3 Long/Lat carriage** — white box projecting forward from the column top; Lng ~1.25 m, Lat ±0.20 m.
- **D4 PerfectPitch 2DOF module** ★ — compact **bare brushed-metal grey** wedge ~12 cm tall under the tabletop (deliberately mechanical vs the white shells). Pitch/Roll/Yaw ±3°.
- **D5 Exact IGRT carbon tabletop** — thin **charcoal/near-black carbon-twill** plank, two-tier (thick proximal ~7.5 cm → thin distal blade ~5 cm), ~2.0–2.2 × 0.5 m.
- **D6 Indexed side rails** — slim strips with notches + engraved scales down both long edges.

### E. Covers / Branding / Vault
- **E1 trueBEAM wordmark** — lowercase "true" + bold "BEAM", Varian blue, on the drum face.
- **E4 Room lasers** — thin **green** crosshair lines from wall/ceiling projectors converging exactly on isocentre (model as emissive lines).
- **E5 Vault** (optional) — wall setup monitors, LED cove lighting, ceiling mural, pale neutral walls, light floor.

## 3. "Tells" — reads as a TrueBeam (prioritise)
1. Open C-arm arch, patient visible, **no bore/ring**.
2. Large cream **drum face** with the blue **trueBEAM** logo, out of a clean rectangular stand.
3. Single warm **beige** collimator/accessory face on an otherwise off-white machine.
4. **Three-arm iso cluster**: head + opposite EPID (thicker) + perpendicular kV source/detector (detector slides).
5. All-rounded seamless matte cream shells.
6. **Stepped metallic 6DOF couch** (bare PerfectPitch wedge) on white pedestal, charcoal carbon plank, indexed rails, cantilevered.
7. **Green** crosshair lasers converging on iso.

## 4. Colour / material palette
| Element | Hex | Finish |
|---|---|---|
| Main shells (gantry/stand/drum/couch pedestal) — warm off-white, NOT pure white | `#EDEAE3`–`#F2EFE8` | matte/satin moulded polymer |
| Collimator face / accessory tray — beige/tan | `#D8CDB8`–`#CBBE9E` | matte, warmer/darker than white |
| Varian accent / trueBEAM logo | `#0093D0`–`#0077C8` | semi-gloss graphic (accent only) |
| Couch tabletop — charcoal carbon twill | `#2A2C2E` | matte carbon |
| 6DOF PerfectPitch stage — brushed metal grey | `#B8BBBE` | bare anodised/brushed metal |
| MLC / jaws — dull machined grey | `#5A5A5C` | tungsten |
| Room lasers — green | `#37E737` | emissive |

**Notes:** white shells are a **warm low-saturation off-white, matte** (pure `#FFFFFF` reads as a toy);
every cover edge generously filleted (~15–40 mm); beige face a clear shade warmer/darker than the white;
the couch deliberately **shows** its bare-metal 6DOF stage.
