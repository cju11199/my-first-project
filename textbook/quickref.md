# Appendix A - Quick Reference: Formulas & Key Values

A condensed reference of the formulas, units, regulatory limits, and clinical anchor values most often tested on radiation-therapy registry reviews.

## Core formulas

```
D2 = D1 x (d1 / d2)^2
```
Inverse-square law: dose falls off with the square of distance from a point source.

```
Equivalent square = 2ab / (a + b)   (= 4 x Area / Perimeter)
```
Converts a rectangular field (sides a and b) to the side of the square field with the same scatter/output.

```
PDD = (Dose at depth / Dose at dmax) x 100   [SSD setup]
```
Percent depth dose: the central-axis dose at a given depth relative to the dose maximum, at fixed SSD.

```
MU = Dose / (D0 x TMR x Sc x Sp x WF x TF)   [SAD / isocentric]
```
Monitor units for an isocentric setup; uses tissue-maximum ratio (TMR) rather than PDD.

```
MU = Dose / (D0 x (PDD / 100) x Sc x Sp x WF x TF)   [SSD]
```
Monitor units for a fixed-SSD setup; depth dependence carried by PDD.

```
BED = n x d x (1 + d / (a/b))
```
Biologically effective dose for n fractions of dose d; the (1 + d/(a/b)) term is the relative effectiveness per fraction.

```
EQD2 = BED / (1 + 2 / (a/b))
```
Equivalent dose in 2 Gy fractions: normalizes a BED to a standard 2 Gy/fraction schedule for comparison.

```
Gap = (L / 2) x (d / SSD)   [per field]
```
Field-junction skin gap for two adjacent fields, computed for each field at the matching depth d (half-field length L) and summed.

```
HVL: 100% -> 50% -> 25% -> 12.5% -> 6.25% ...
```
Each half-value layer of attenuating material halves the beam intensity (one HVL per step).

```
R90 ~ E / 3.2 (cm)        Rp ~ E / 2 (cm)
```
Electron beam depth rules of thumb: therapeutic depth (90% / R90) and practical range (Rp) from beam energy E in MeV.

## Units & conversions

| Quantity | SI unit | Symbol | Conversion | Note |
|---|---|---|---|---|
| Absorbed dose | gray | Gy | 1 Gy = 100 rad | Energy deposited per unit mass (J/kg) |
| Equivalent / effective dose | sievert | Sv | 1 Sv = 100 rem | Absorbed dose weighted for radiation/tissue effect |
| Activity | becquerel | Bq | 1 Ci = 3.7 x 10^10 Bq | Decays per second |

For therapy photon and electron beams (radiation weighting factor = 1), 1 Gy ~ 1 Sv.

## NRC dose limits (10 CFR 20)

| Exposed group | Limit (SI) | Limit (conventional) |
|---|---|---|
| Occupational, whole body (annual) | 50 mSv/yr | 5 rem/yr |
| Occupational, cumulative | 10 mSv x age (years) | 1 rem x age |
| General public (annual) | 1 mSv/yr | 100 mrem/yr |
| Declared-pregnant worker, embryo/fetus | 5 mSv over gestation | 0.5 rem over gestation |
| Lens of the eye (annual) | 150 mSv/yr | 15 rem/yr |
| Skin / extremities (annual) | 500 mSv/yr | 50 rem/yr |

## Radiobiology values

| Concept | Value / definition |
|---|---|
| a/b ratio - tumor / early-responding tissue | ~10 Gy |
| a/b ratio - late-responding (normal) tissue | ~3 Gy |
| Oxygen enhancement ratio (OER) | ~2.5-3 (well-oxygenated vs hypoxic) |
| Low-LET radiation | Photons / electrons - sparse ionization, RBE ~1 |
| High-LET radiation | Alpha / neutron / carbon - dense ionization, RBE > 1 |
| Deterministic effect | Threshold dose; severity rises with dose (e.g. cataract, skin erythema) |
| Stochastic effect | No threshold; probability (not severity) rises with dose (e.g. cancer, heritable) |
| The Four R's | Repair, Reassortment (redistribution), Repopulation, Reoxygenation |

## Photon interactions

| Interaction | Dominant when | Key dependence | Outcome |
|---|---|---|---|
| Photoelectric | Low energy, high-Z material | ~ Z^3 | Photon fully absorbed; characteristic x-ray / Auger emitted |
| Compton | Megavoltage therapy range | Independent of Z (electron density) | Partial energy transfer; scattered photon + recoil electron |
| Pair production | High energy, > 1.02 MeV | Increases with Z and energy | Photon converts to electron-positron pair near the nucleus |

## Brachytherapy isotopes

| Use | Isotope |
|---|---|
| HDR remote afterloading | Ir-192 |
| LDR intracavitary | Cs-137 |
| Permanent prostate seeds | I-125 |

## Typical dose/fractionation anchors (protocol-dependent)

These are common textbook examples only - actual prescriptions vary by protocol, institution, and patient.

| Indication | Typical example |
|---|---|
| Conventional fractionation | 1.8-2 Gy/fraction |
| Glioblastoma | 60 Gy / 30 fx + concurrent temozolomide |
| Head & neck (definitive) | ~70 Gy / 35 fx |
| Whole-breast hypofractionation | 40-42.5 Gy / 15 fx |
| Lung SBRT | e.g. 50 Gy / 5 fx |
| Palliative bone metastasis | 30 Gy / 10 fx, 20 Gy / 5 fx, or 8 Gy x 1 |

*Values are typical and protocol-dependent. Educational use only; not affiliated with or endorsed by the ARRT.*
