# Chapter 7 — Prescription & Dose Calculation

## What you'll learn

- What a radiation prescription actually specifies, and where the dose is "prescribed to."
- The single most important setup distinction in dose calculation: **SSD versus SAD**, and which depth-dose table each one uses.
- How to turn a rectangular field into an **equivalent square**, and why we bother.
- What **PDD, TMR, TPR, and TAR** mean — in plain words — and how to read a dose off them.
- How to do a **monitor-unit (MU) calculation** step by step, for both setups, including wedges and trays.
- The special cases that trip people up: tissue inhomogeneity, field-junction gaps, and electron-beam ranges.
- How we judge a finished plan with the homogeneity index, conformity index, and the dose-volume histogram.

If math makes you tense, take a breath — this chapter is built for you. Every formula is introduced in words first, then shown with a fully worked example where we write out *every* step. You will never be asked to do anything more complicated than multiply, divide, and square a number. Go slowly, keep a calculator handy, and let each example sink in before moving on.

## Part 1 · The prescription and the language of dose

A radiation **prescription** is the physician's order. At minimum it names the **total dose**, the **dose per fraction**, the **number of fractions**, and the **technique and energy**. For example, "60 Gy in 30 fractions, 6 MV, IMRT" means 2 Gy each day for 30 days.

Dose has to be prescribed **to a point or volume**, because dose is not the same everywhere in the beam. Historically we prescribed to the **ICRU reference point** — a clearly defined point (often at or near the isocenter, in the center of the target) chosen so that different clinics report dose the same way. Modern conformal and intensity-modulated plans usually prescribe so that a chosen **isodose line** covers the target, but the ICRU reference point is still how we talk about and report the dose.

> **Key Point:** "Dose" always comes with a *location*. A prescription of 200 cGy means 200 cGy *at the prescription point or isodose line* — not everywhere in the beam.

The physician also picks a **beam energy** based on how deep the target is (Chapter 3: higher energy = deeper d_max and more penetration) and may add **beam modifiers** such as **wedges** to shape the dose. All of these choices feed into the calculation that tells the machine how long to stay on — the monitor-unit calculation we build toward in this chapter.

## Part 2 · Two ways to set up: SSD versus SAD

Before any numbers, you must know **how the patient is set up**, because it decides which table you use. There are two setups, and confusing them is the number-one dose-calc mistake.

![SSD versus SAD setup geometry](figures/fig7-ssd-vs-sad.svg)

*Figure 7.1 — In an SSD setup the fixed 100 cm runs from the source to the patient's skin, and the target sits at some depth below it. In an SAD setup the fixed 100 cm runs all the way to the isocenter inside the patient. The difference decides which depth-dose table you use.*

- **SSD (Source-to-Surface Distance) setup.** You fix the distance from the source to the **skin** (commonly 100 cm). The target is then at some depth *below* that fixed point. SSD setups use **PDD** tables.
- **SAD (Source-to-Axis Distance) setup**, also called **isocentric**. You fix the distance from the source to the **isocenter**, which sits *inside* the patient at the target. The skin is somewhere above it. SAD setups use **TMR** (or TPR) tables. This is the standard for modern linac treatments because you can rotate the gantry all the way around without moving the patient.

> **Common mix-up:** In **SSD** the fixed distance lands on the **skin**; in **SAD** the fixed distance lands on the **isocenter inside the patient**. SSD → PDD. SAD → TMR/TPR. Lock this pairing in and half the chapter falls into place.

## Part 3 · Field size and the equivalent square

The beam's **field size** (set by the jaws and the multileaf collimator) affects how much scattered dose reaches a point — a bigger field means more scatter and a bit more dose. Our depth-dose tables are written for **square** fields, but real fields are often **rectangular**. So we convert a rectangle into the square that behaves the same way: its **equivalent square**.

![Equivalent square of a rectangle](figures/fig7-equivalent-square.svg)

*Figure 7.2 — A 10 cm × 6 cm rectangle scatters dose like a 7.5 cm × 7.5 cm square. We use the equivalent-square size to look up depth-dose and scatter factors.*

> **Key Point:** **Equivalent square = 2ab / (a + b)** (the same as 4 × Area ÷ Perimeter), where *a* and *b* are the rectangle's sides.

**Worked example.** A field is 10 cm × 6 cm. What is its equivalent square?

```
Equivalent square = 2ab / (a + b)
                  = 2 × 10 × 6 / (10 + 6)
                  = 120 / 16
                  = 7.5 cm
```

So you would look up your depth-dose and scatter numbers for a **7.5 cm × 7.5 cm** field.

## Part 4 · Depth-dose functions

These four "ratios" all describe how dose changes with depth. You do not have to derive them — you just need to know what each one means and which setup it belongs to.

- **PDD (Percent Depth Dose).** The dose at a depth, written as a percentage of the dose at d_max:

> **Key Point:** **PDD = (dose at depth d ÷ dose at d_max) × 100.** PDD belongs to **SSD** setups. PDD goes *up* with higher energy, larger field size, and longer SSD; it goes *down* with depth.

  **Worked example.** A beam deposits 100 cGy at d_max. If the PDD at 10 cm is 66%, what is the dose at 10 cm depth?

```
Dose at depth = dose at d_max × (PDD ÷ 100)
              = 100 cGy × (66 ÷ 100)
              = 66 cGy
```

- **TMR (Tissue-Maximum Ratio).** The dose at a depth divided by the dose at d_max **at the same point in space** — so it does not change when you move the source closer or farther. That distance-independence is exactly what an isocentric (**SAD**) setup needs.
- **TPR (Tissue-Phantom Ratio).** Almost the same as TMR, but the reference depth is a fixed depth (often 10 cm) instead of d_max. Also used for SAD.
- **TAR (Tissue-Air Ratio).** An older ratio (dose in tissue ÷ dose in air at the same point). You should recognize the name, but TMR has largely replaced it for high-energy beams.

> **Common mix-up:** **PDD changes with distance** (it is tied to a fixed SSD), while **TMR/TPR do not** (they are tied to a fixed point). That is the whole reason isocentric treatments use TMR.

## Part 5 · The inverse-square law, revisited

Recall from Chapter 3 (Figure 3.3) that dose rate falls with the **square** of the distance from the source: **D₂ = D₁ × (d₁/d₂)²**. In dose calculation this is how you correct for treating at a distance other than the calibration distance.

**Worked example.** A machine gives 200 cGy at 100 cm. What is the dose rate at 120 cm?

```
D2 = D1 × (d1 / d2)²
   = 200 × (100 / 120)²
   = 200 × (0.833)²
   = 200 × 0.694
   ≈ 139 cGy
```

## Part 6 · Scatter, wedges, and trays — the correction factors

A real calculation includes a handful of multiplying factors. Each one answers "how much does *this* change the dose per MU?"

- **Collimator (head) scatter, S_c.** Extra dose scattered from the machine head as the field opens up. It depends on the **collimator setting**, measured in air.
- **Phantom (patient) scatter, S_p.** Extra dose scattered from the **patient's own tissue**. It depends on the field size at the patient. Together, **S_cp = S_c × S_p** is the total scatter factor.

> **Common mix-up:** **S_c is scatter from the machine** (collimator/head, measured in air); **S_p is scatter from the patient** (phantom). Both grow as the field gets bigger.

- **Wedge factor, WF.** A **wedge** is a metal block, thick on one side, that sits in the beam to tilt the dose. Because it absorbs part of the beam, it lowers the dose per MU — so you need *more* MUs. Its effect is captured by the wedge factor (a number less than 1, e.g., 0.70 for a steep wedge).

![A wedge tilts the isodose lines](figures/fig7-wedge.svg)

*Figure 7.3 — A wedge is thick on one edge (the heel) and thin on the other (the toe). The thick heel absorbs more of the beam, so the isodose lines tilt — useful for matching sloping surfaces or blending adjacent fields.*

- **Tray (block) factor, TF.** A tray that holds shielding blocks also absorbs a little beam (often around 0.97), so it too is a factor in the calculation.

## Part 7 · Putting it together: the monitor-unit calculation

A **monitor unit (MU)** is how a linac measures its output — roughly, "how long the beam stays on." The MU calculation asks: *given everything above, how many MUs deliver the prescribed dose?* The logic is always the same — **divide the dose you want by the dose you get per MU**, after accounting for every factor.

![Anatomy of the monitor-unit equation](figures/fig7-mu-anatomy.svg)

*Figure 7.4 — Reading the SAD monitor-unit equation factor by factor. Anything in the denominator that lowers the dose per MU (a wedge, depth, a tray) means more monitor units are needed to reach the prescribed dose.*

For an **isocentric (SAD)** setup:

```
MU = Dose ÷ ( D0 × TMR × Sc × Sp × WF × TF )
   D0  = machine output (cGy per MU) at the reference conditions
   TMR = tissue-maximum ratio at the treatment depth & field size
   Sc, Sp = collimator and phantom scatter factors
   WF, TF = wedge and tray factors
```

**Worked example (SAD, open field).** Prescribe **200 cGy** to the isocenter. The machine is calibrated to **1.000 cGy/MU**. At this depth and field size, **TMR = 0.85**; **S_c = 1.00**, **S_p = 1.00**; no wedge or tray (WF = TF = 1.00).

```
MU = 200 ÷ (1.000 × 0.85 × 1.00 × 1.00 × 1.00 × 1.00)
   = 200 ÷ 0.85
   ≈ 235 MU
```

**Now add a wedge.** Keep everything the same but insert a wedge with **WF = 0.70**.

```
MU = 200 ÷ (1.000 × 0.85 × 0.70)
   = 200 ÷ 0.595
   ≈ 336 MU
```

See how adding the wedge — which *lowers* dose per MU — *raises* the MUs from 235 to 336. Every factor below 1 in the denominator pushes the MU count up.

For an **SSD** setup, the only change is that **PDD/100 replaces TMR**:

```
MU = Dose ÷ ( D0 × (PDD/100) × Sc × Sp × WF × TF )
```

**Worked example (SSD).** Deliver **200 cGy** to a depth where **PDD = 66%**, with D0 = 1.000 cGy/MU and all other factors = 1.00.

```
MU = 200 ÷ (1.000 × 0.66)
   ≈ 303 MU
```

For **electron beams**, the dose is normalized at **d_max** rather than at depth, and electron-specific output factors are used — but the same "dose ÷ dose-per-MU" logic applies.

## Part 8 · Corrections and special cases

### Tissue inhomogeneity

Our basic tables assume the body is all water. Real patients contain **lung** (low density — the beam passes through more easily, so dose downstream is *higher* than the water assumption) and **bone** (high density — more attenuation). Treatment-planning systems correct for this. Older hand methods include the **effective-depth** method and the **Batho power-law** method; modern systems use convolution or Monte Carlo algorithms that handle it automatically. The takeaway for you: **ignoring lung and bone can be off by 5–20%**, which is why these corrections matter most in the chest.

### Field-junction gaps

When two beams sit next to each other (for example, treating the spine in two segments), their edges **diverge** outward as they go deeper. If you butt them right together at the skin, they will **overlap** at depth and create a hot spot. The fix is to leave a small **gap at the skin** so the field edges meet cleanly at the target depth.

![Field-junction gap geometry](figures/fig7-gap.svg)

*Figure 7.5 — Each beam spreads as it goes deeper. Leaving a calculated gap at the skin lets the diverging edges meet at the treatment depth instead of overlapping (a hot spot) or separating (a cold spot).*

> **Key Point:** **Gap = (L/2) × (d / SSD)** for each field, where L is the field length, d is the junction depth, and SSD is the source-to-surface distance. Add the two fields' contributions for the total skin gap.

**Worked example.** Two fields, each **20 cm** long, are to join at a depth of **8 cm**, with **SSD = 100 cm**.

```
Each field's contribution = (L / 2) × (d / SSD)
                          = (20 / 2) × (8 / 100)
                          = 10 × 0.08
                          = 0.8 cm
Total gap = 0.8 cm + 0.8 cm = 1.6 cm
```

### Electron beams: ranges and energy choice

Electrons are wonderful for **superficial** targets because they deposit dose and then **stop**, sparing whatever is behind them. Three "range" numbers describe an electron beam's depth-dose curve:

![Electron depth dose with R90, R50, and Rp](figures/fig7-electron-depthdose.svg)

*Figure 7.6 — Electrons give a high surface dose, a quick d_max, then a steep fall-off and a small bremsstrahlung tail. R₉₀ (the therapeutic range) is the depth that still gets 90% of the dose; R₅₀ is the half-dose depth; Rp is the practical range where the steep slope, extended, hits the axis.*

- **R₉₀** — the depth still receiving 90% of the dose. This is the **therapeutic range**: cover your target inside R₉₀.
- **R₅₀** — the depth of 50% dose (used to define the beam's quality/energy).
- **Rp** — the **practical range**, where the steepest part of the curve, extended down, crosses the axis.

A handy rule of thumb is that **R₉₀ ≈ E ÷ 3.2** (in cm, for energy E in MeV), and the practical range **Rp ≈ E ÷ 2**. Both depths get **deeper as energy rises**.

**Worked example.** A lesion needs coverage to **3 cm** deep. Roughly what electron energy do you need?

```
We need R90 ≥ 3 cm.
R90 ≈ E / 3.2   →   E ≈ 3.2 × R90 = 3.2 × 3 = ~10 MeV
Pick the next available energy up (e.g., 12 MeV) to be safe.
```

## Part 9 · Judging the plan: HI, CI, and the DVH

Once a plan exists, we score it with a few quick numbers:

- **Homogeneity Index (HI)** — how *uniform* the dose is across the target. A common form is HI = D₅ ÷ D₉₅ (the dose to the hottest 5% over the dose to the coldest 95%); closer to **1.0** is more uniform.
- **Conformity Index (CI)** — how tightly the prescription dose *wraps* the target: the volume covered by the prescription isodose ÷ the target volume. Around **1.0** is ideal (covers the target without spilling dose into normal tissue).
- **Dose-Volume Histogram (DVH)** — the single most useful plan-evaluation picture.

![Reading a dose-volume histogram](figures/fig7-dvh.svg)

*Figure 7.7 — A DVH plots, for each structure, the volume receiving at least a given dose. You want the target curve to stay high and then drop in a sharp cliff near the prescription dose, and each organ-at-risk curve to fall away early (low and to the left).*

> **Key Point:** On a DVH, a **good target** curve holds near 100% volume and then falls off a cliff right at the prescription dose; a **well-spared organ at risk** drops off early, staying low and to the left.

## Check yourself

**1. Which depth-dose table goes with an SSD setup, and which goes with a SAD setup?**
*SSD uses PDD; SAD (isocentric) uses TMR (or TPR).*

**2. Find the equivalent square of a 15 cm × 5 cm field.**
*2ab/(a+b) = 2 × 15 × 5 / (15 + 5) = 150 / 20 = 7.5 cm.*

**3. A beam gives 100 cGy at d_max. If the PDD at 12 cm is 60%, what is the dose at 12 cm?**
*100 × (60/100) = 60 cGy.*

**4. Calculate the MU for 250 cGy to the isocenter with D0 = 1.000 cGy/MU, TMR = 0.80, and all other factors = 1.00.**
*MU = 250 ÷ (1.000 × 0.80) = 312.5 ≈ 313 MU.*

**5. You insert a wedge (WF = 0.75) into the setup in question 4. What happens to the MU, and what is the new value?**
*The MU goes up: MU = 250 ÷ (0.80 × 0.75) = 250 ÷ 0.60 ≈ 417 MU.*

**6. Two 18 cm fields join at 6 cm depth, SSD = 100 cm. What is the total skin gap?**
*Each field: (18/2) × (6/100) = 9 × 0.06 = 0.54 cm. Total = 0.54 + 0.54 = 1.08 cm.*

**7. Why do we use electron beams for superficial lesions?**
*Electrons deposit their dose over a short range and then stop, sparing the deeper tissue behind the target.*

**8. On a DVH, what does an ideal target curve look like?**
*It stays near 100% volume across the lower doses and then drops in a sharp cliff right around the prescription dose — meaning the whole target gets the dose and little more.*

## Chapter references

1. AAPM Task Group 71. *Monitor unit calculations for external photon and electron beams.* (Equivalent square, S_c/S_p, MU formalism for SSD and SAD, electron MU.)
2. Khan FM, Gibbons JP. *The Physics of Radiation Therapy.* Wolters Kluwer. (PDD, TMR/TPR/TAR, inverse-square, wedges, field separation/gaps, electron ranges.)
3. International Commission on Radiation Units & Measurements (ICRU). *Reference-point dose specification and reporting* (Reports 50/62/83).
4. AAPM Report 85 / Task Group 65. *Tissue inhomogeneity corrections for megavoltage photon beams.*

*This chapter offers original educational explanations. It is not affiliated with or endorsed by the ARRT and does not reproduce actual exam questions.*
