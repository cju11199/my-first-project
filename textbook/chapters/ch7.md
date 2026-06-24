# Chapter 7 — Prescription & Dose Calculation

## What you'll learn

- How a radiation oncologist's prescription turns into numbers you can calculate: total dose, dose per fraction, and beam energy.
- How to describe a treatment field's size and shape, and how to turn a rectangle into its **equivalent square**.
- The difference between an **SSD** (source-to-surface) setup and an **SAD/isocentric** (source-to-axis) setup, and which depth-dose table each one uses.
- The depth-dose functions — **PDD, TMR, TPR, TAR** — and the **inverse-square law**, all explained one symbol at a time.
- How to calculate **monitor units (MU)** for an isocentric beam, step by step.
- A first look at tissue inhomogeneity corrections, field-junction gaps, electron ranges, and plan-quality metrics.

## Why this matters

Every treatment you deliver starts as a prescription written in plain clinical language, and ends as a number of monitor units you punch into the machine. The math in between is what keeps the right dose landing in the right place. If you can move calmly from "prescribe 200 cGy" to "deliver 235 MU," you understand the heart of what a radiation therapist does. We'll go slowly, define every letter, and show every arithmetic step — no skipped lines.

---

## 1. Dose specification: reading the prescription

A radiation oncologist prescribes a **total dose** delivered in small daily pieces called **fractions**. Splitting the dose up (fractionation) lets healthy tissue repair between treatments while the tumor falls behind on repair.

The relationship is simple multiplication:

```
Total dose = (dose per fraction) × (number of fractions)
```

Example: 200 cGy per fraction × 35 fractions = 7000 cGy = 70 Gy total.

> **Key Point:** 1 Gray (Gy) = 100 centigray (cGy). Most clinics talk in cGy day-to-day because doses per fraction are tidy whole numbers (like 180 or 200 cGy). Keep your units straight and most "hard" problems become easy.

### Where is the dose prescribed *to*?

The dose has to be specified at a defined point so everyone agrees on what "70 Gy" means. The **ICRU reference point** is that agreed-upon spot — usually at or near the center of the target (often the isocenter for an isocentric plan). It is chosen to be in a region of uniform dose, away from steep gradients and away from tissue boundaries, so the number is reproducible and clinically meaningful [3].

### Choosing beam energy by depth

Higher-energy photon beams penetrate deeper before their dose peaks and fall off more slowly. So a deep tumor (like a pelvic target) usually gets a higher energy (say 15–18 MV), while a shallow target may use 6 MV. The rule of thumb: **deeper target → higher energy.**

### Beam modifiers (wedges)

A **wedge** tilts the dose distribution to compensate for a sloping patient surface or to blend two beams.

- A **physical wedge** is a literal metal block placed in the beam.
- A **dynamic (or virtual) wedge** is created by moving a collimator jaw across the field while the beam is on, sweeping the dose into a wedge shape — no metal needed.

Either way, the wedge absorbs some beam, so it changes your MU calculation through the **wedge factor (WF)**, which we'll meet later.

---

## 2. Geometry: field size, shape, and depth

### Field size and the equivalent square

Treatment fields are often rectangles, but our depth-dose tables are built for **squares**. So we convert a rectangle into the square that scatters radiation the same way. That square is the **equivalent square**.

For a rectangle with sides **a** and **b**:

```
Equivalent square side = 2ab / (a + b)
```

where:
- **a** = length of one side (cm)
- **b** = length of the other side (cm)

An equivalent way to write the same idea is **4 × Area / Perimeter**, since Area = a×b and Perimeter = 2a + 2b. Both give the identical answer; use whichever feels natural.

> **Common mix-up:** Don't just average the two sides. The equivalent square is **not** (a + b)/2. It uses the **2ab/(a+b)** formula, which weights toward the smaller side because scatter depends on field area and edges, not a plain average.

### Measuring depth

**Depth (d)** is how far below the skin surface your point of interest sits, measured in cm along the beam. The special depth where the dose first reaches its maximum is **dmax** (also written d_max). For a 6 MV photon beam, dmax is about 1.5 cm; higher energies have a deeper dmax.

### Two setup styles: SSD vs SAD

This is one of the most important distinctions in the whole chapter.

| | **SSD setup** | **SAD / isocentric setup** |
|---|---|---|
| Stands for | Source-to-**Surface** Distance | Source-to-**Axis** Distance |
| What's fixed | Distance from source to skin | Distance from source to isocenter |
| Reference point | Often dmax under the skin | The isocenter (axis), usually inside the patient |
| Table used | **PDD** | **TMR** or **TPR** |
| Typical use | Single fields, simple setups | Multi-field plans rotating around one point |

> **Key Point:** **SSD pairs with PDD. SAD pairs with TMR/TPR.** Memorize this pairing. If a problem says "isocentric," your brain should immediately reach for TMR.

In an **SAD** setup the machine rotates around a fixed point (the isocenter, "the axis"), so every beam aims at the same spot inside the patient. That's why it's so popular — you set up once and treat from many angles.

---

## 3. Depth-dose functions

These are all just ratios that describe how dose changes with depth. Don't let the acronyms scare you; each is a fraction comparing dose at one place to dose at another.

### Percent Depth Dose (PDD) — used with SSD

```
PDD = (dose at depth d / dose at dmax) × 100
```

- **dose at depth d** = the dose at your point of interest
- **dose at dmax** = the dose at the depth of maximum buildup
- The ×100 turns the fraction into a percent.

PDD answers: "Compared to the peak, what percent of the dose survives down at depth d?" It's measured at a fixed SSD, so it's the natural partner for SSD setups.

### Tissue-Maximum Ratio (TMR) and Tissue-Phantom Ratio (TPR) — used with SAD

TMR is the dose at depth d divided by the dose at dmax, **but measured at the same distance from the source** (the point stays at the axis while tissue is added or removed). Because the point-to-source distance doesn't change, TMR is **distance-independent** — perfect for isocentric setups where the isocenter is always at the same distance.

**TPR** is the same idea but the reference is a fixed depth (commonly 10 cm) instead of dmax. TMR is just the special case of TPR where the reference depth is dmax.

> **Common mix-up:** **PDD vs TMR.** PDD changes if you change the SSD (it bakes in an inverse-square effect). TMR/TPR are built to be distance-independent. That's exactly why SSD work uses PDD and isocentric work uses TMR/TPR.

### Tissue-Air Ratio (TAR) — the older one

**TAR** compares dose at depth in tissue to dose at the same point "in air" (in a tiny bit of tissue, no full phantom). It's largely historical for photons today but still appears in registry questions, so recognize the name.

---

## 4. The inverse-square law

Radiation spreads out as it travels, like light from a flashlight. Double the distance and the same energy covers four times the area, so intensity drops to one-quarter. That's the inverse-square law:

```
D2 = D1 × (d1 / d2)²
```

where:
- **D1** = known dose (or dose rate) at the first distance
- **D2** = the dose you're solving for at the new distance
- **d1** = the original distance from the source
- **d2** = the new distance from the source

Notice the order: the **original** distance is on top, the **new** distance is on the bottom, and the whole ratio is **squared**.

> **Key Point:** If you get farther away, dose goes **down** — so your answer should be smaller than D1. If it came out bigger, you flipped the ratio. Use that sanity check every time.

---

## 5. Monitor-unit (MU) calculation

A **monitor unit** is the machine's internal "click" of output. The linac is calibrated so that under reference conditions, 1 MU delivers a known dose. Our job is to figure out how many MU produce the prescribed dose for *this* patient's geometry.

### The SAD (isocentric) formula

```
MU = Dose / (D0 × TMR × Sc × Sp × WF × TF)
```

Let's define every term:

| Symbol | Name | What it means |
|---|---|---|
| **Dose** | prescribed dose | cGy you want at the point (e.g., isocenter) |
| **D0** | reference dose rate | cGy delivered per MU at calibration conditions (often ≈ 1.000 cGy/MU) |
| **TMR** | tissue-maximum ratio | depth-dose factor for this depth & field size |
| **Sc** | collimator (head) scatter factor | extra dose from scatter in the machine head as field size changes |
| **Sp** | phantom scatter factor | extra dose from scatter inside the patient as field size changes |
| **WF** | wedge factor | fraction of beam transmitted through a wedge (≤ 1) |
| **TF** | tray factor | fraction transmitted through a blocking tray (≤ 1) |

You'll also see **Scp = Sc × Sp**, the combined "total scatter factor," when the two are tabulated together.

> **Common mix-up:** **Sc vs Sp.** **Sc** is scatter from the machine **head/collimator** (set by the jaw/collimator opening). **Sp** is scatter from inside the **patient/phantom**. One happens before the beam reaches the patient; the other happens in the patient. Both grow as the field gets bigger.

### The SSD form

For an SSD setup you swap the depth-dose term: replace **TMR** with **PDD/100**.

```
MU = Dose / (D0 × (PDD/100) × Sc × Sp × WF × TF)
```

We divide PDD by 100 because PDD is a percent and we need a plain fraction.

### Electrons

Electron beams are calibrated and normalized at **dmax** (not at depth), and they have their own scatter/output factors that depend strongly on the cutout shape. The structure of the formula is similar, but the normalization point is dmax. We cover electron ranges in Section 8.

The TG-71 report is the standard reference for these hand-calculation formulas [1].

---

## Worked Example A — Equivalent square

**Problem:** A treatment field is 10 cm × 6 cm. What is its equivalent square?

**Step 1 — Write the formula.**
```
Equivalent square side = 2ab / (a + b)
```

**Step 2 — Plug in a = 10 cm, b = 6 cm.**
```
= 2 × 10 × 6 / (10 + 6)
```

**Step 3 — Do the top (numerator).**
```
2 × 10 × 6 = 120
```

**Step 4 — Do the bottom (denominator).**
```
10 + 6 = 16
```

**Step 5 — Divide.**
```
120 / 16 = 7.5
```

**Answer:** The 10 × 6 field behaves like a **7.5 cm × 7.5 cm square**. You'd look up TMR, PDD, Sc, and Sp using a 7.5 cm field size.

---

## Worked Example B — Inverse-square law

**Problem:** A beam delivers 100 cGy at a distance of 100 cm from the source. What is the dose at 110 cm?

**Step 1 — Write the formula.**
```
D2 = D1 × (d1 / d2)²
```

**Step 2 — Identify the numbers.**
- D1 = 100 cGy (the known dose)
- d1 = 100 cm (original distance)
- d2 = 110 cm (new distance)

**Step 3 — Form the distance ratio (original over new).**
```
d1 / d2 = 100 / 110 = 0.9091
```

**Step 4 — Square the ratio.**
```
0.9091² = 0.8264
```

**Step 5 — Multiply by D1.**
```
D2 = 100 × 0.8264 = 82.64 cGy
```

**Answer:** About **82.6 cGy.** Sanity check: we moved farther away, so the dose dropped below 100 — exactly what we expect.

---

## Worked Example C — Monitor units (SAD setup)

**Problem:** Prescribe **200 cGy** to the isocenter on an isocentric beam. Reference dose rate **D0 = 1.000 cGy/MU**, **TMR = 0.85**, **Sc = 1.00**, **Sp = 1.00**, **WF = 1.00**, **TF = 1.00**. Find the MU. Then redo it with a wedge of **WF = 0.70**.

**Step 1 — Write the SAD formula.**
```
MU = Dose / (D0 × TMR × Sc × Sp × WF × TF)
```

**Step 2 — Plug in the open-field numbers.**
```
MU = 200 / (1.000 × 0.85 × 1.00 × 1.00 × 1.00 × 1.00)
```

**Step 3 — Multiply the denominator.** Everything except TMR is 1.00, so:
```
1.000 × 0.85 × 1.00 × 1.00 × 1.00 × 1.00 = 0.85
```

**Step 4 — Divide.**
```
MU = 200 / 0.85 = 235.3
```

**Open-field answer: ≈ 235 MU.**

**Now add a wedge (WF = 0.70).**

**Step 5 — Rebuild the denominator with the wedge.**
```
1.000 × 0.85 × 1.00 × 1.00 × 0.70 × 1.00 = 0.595
```

**Step 6 — Divide again.**
```
MU = 200 / 0.595 = 336.1
```

**Wedged answer: ≈ 336 MU.**

**Why did MU go up?** The wedge absorbs about 30% of the beam (WF = 0.70 means only 70% gets through). To still deliver 200 cGy, the machine must run longer — more MU. Anything that *blocks* the beam (smaller WF or TF) makes MU **rise**; that's a great built-in sanity check.

---

## 6. Tissue inhomogeneity corrections

Our basic tables assume the patient is uniform water. Real bodies are not. **Lung** is much less dense than water, so the beam passes through more easily (less attenuation, higher dose downstream). **Bone** is denser, so it attenuates more.

To account for this, planning systems apply **heterogeneity (inhomogeneity) corrections**:

- **Effective-depth (ratio of TAR) method** — replaces physical depth with a "water-equivalent" depth that accounts for the actual densities the beam crossed.
- **Batho power-law method** — a more refined correction that weights each tissue layer's density.
- **Modern convolution/superposition and Monte Carlo** — today's treatment-planning systems model scatter and electron transport directly, which is far more accurate, especially near lung and air cavities.

AAPM Report 85 (Task Group 65) is the classic reference on tissue inhomogeneity corrections [4].

> **Key Point:** Ignore inhomogeneities in the lung and you can be off by 10% or more. This is why we no longer hand-calculate complex thoracic plans the old way.

---

## 7. Field-junction gap

When two adjacent fields meet — think **craniospinal irradiation**, where a brain field abuts a spine field — the beams diverge and would either overlap (a **hot spot**) or leave a cold strip at depth. To make them meet cleanly *at depth*, we leave a small skin **gap** between the field edges.

For each field, the gap contribution is:

```
Gap (per field) = (L / 2) × (d / SSD)
```

where:
- **L** = field length at the surface (cm)
- **d** = depth at which you want the fields to match (cm)
- **SSD** = source-to-surface distance (cm)

You compute this for each field and add the two contributions to get the total skin gap. The idea: the beam edges fan outward with depth, so a calculated surface gap lets the diverging edges meet exactly where the target sits.

---

## 8. Electron specifics: ranges

Electrons behave very differently from photons. They deposit dose to a fairly uniform depth and then stop, which is great for shallow targets. Key range terms:

| Term | Meaning |
|---|---|
| **dmax** | depth of maximum dose |
| **R90** | the **therapeutic range** — depth where dose falls to 90% of max; this is the deepest point you can usually treat |
| **R50** | depth where dose falls to 50% of max (used to define beam energy) |
| **Rp** | the **practical range** — where the falling dose curve, extrapolated, hits the background; essentially the deepest electron penetration |

A couple of handy approximations for the depth in **cm of tissue**, where **E** is the electron energy in MeV:

```
Therapeutic range R90  ≈  E / 3.2  to  E / 4   (cm)
Practical range Rp     ≈  E / 2            (cm, rough)
```

Example: a 12 MeV beam has R90 ≈ 12 / 4 = 3 cm to 12 / 3.2 ≈ 3.75 cm — so it treats nicely down to roughly 3 cm.

> **Key Point:** For electrons, **dmax and range both increase with energy.** Pick the energy from how deep the target sits — a useful rule is that R90 (cm) ≈ energy (MeV) divided by about 3 to 4.

---

## 9. Plan-quality metrics

Once a plan exists, we grade it with numbers:

- **Dose-Volume Histogram (DVH):** a graph showing what volume of each structure receives what dose. You read it as "X% of the target gets at least Y dose." It's the single most useful picture in planning.
- **Homogeneity Index (HI):** how *uniform* the dose is inside the target. Lower (closer to a flat dose) is better. A common form is (D2% − D98%) / D50% — small spread, small index.
- **Conformity Index (CI):** how well the prescription dose *wraps* the target without spilling into normal tissue. Closer to 1.0 means the high-dose region matches the target shape.

You don't usually hand-calculate these on the registry, but you should recognize what each one tells you: **DVH = the whole picture, HI = uniformity inside the target, CI = tightness around the target.**

---

## Check yourself

**1.** A field is 20 cm × 5 cm. What is its equivalent square?
*Use 2ab/(a+b) = 2 × 20 × 5 / (20 + 5) = 200 / 25 = 8 cm. The equivalent square is 8 × 8 cm.*

**2.** Which depth-dose table goes with an isocentric (SAD) setup — PDD or TMR?
*TMR (or TPR). PDD is for SSD setups. Remember: SSD–PDD, SAD–TMR.*

**3.** A point gets 150 cGy at 100 cm from the source. What does it get at 120 cm?
*D2 = 150 × (100/120)² = 150 × (0.8333)² = 150 × 0.6944 = 104.2 cGy. It dropped because we moved farther away.*

**4.** In an MU calculation, what's the difference between Sc and Sp?
*Sc is collimator/head scatter (from the machine), and Sp is phantom scatter (from inside the patient). Both increase with field size.*

**5.** You add a physical wedge (WF = 0.75) to a beam that needed 200 MU open. Will the MU go up or down, and roughly to what?
*Up, because the wedge blocks part of the beam. New MU ≈ 200 / 0.75 = 267 MU.*

**6.** Why is TMR called "distance-independent" while PDD is not?
*TMR keeps the measurement point at the same distance from the source while changing the tissue, so it removes the inverse-square effect. PDD is measured at a fixed SSD and includes inverse-square changes, so it shifts when SSD changes.*

---

## Chapter references

1. Gibbons JP, et al. *Monitor Unit Calculations for External Photon and Electron Beams* — AAPM Task Group 71 (TG-71). Report of the AAPM Therapy Physics Committee Task Group No. 71, 2014. [1]
2. Khan FM, Gibbons JP. *Khan's The Physics of Radiation Therapy.* Wolters Kluwer / Lippincott Williams & Wilkins. [2]
3. International Commission on Radiation Units and Measurements (ICRU). Reports on prescribing, recording, and reporting photon-beam therapy (reference-point dose specification). [3]
4. Papanikolaou N, et al. *Tissue Inhomogeneity Corrections for Megavoltage Photon Beams* — AAPM Report No. 85 (Task Group 65). Medical Physics Publishing, 2004. [4]

*This is an independent educational text with original explanations. It is not affiliated with the ARRT, and the questions here are not actual ARRT exam items.*
