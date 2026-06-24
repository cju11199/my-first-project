# Chapter 3 — Radiation Physics & Radiobiology

## What you'll learn

- Where therapy radiation comes from, and how Cobalt-60 and linear-accelerator x-rays are produced.
- How beams are described by energy and "quality," and how they fade as they pass through matter.
- The three ways photons hand their energy to tissue, and which one rules at the energies you use every day.
- The units of radiation — Gray, Sievert, Becquerel — and how to keep them straight.
- How cells respond to dose, the linear-quadratic model, the α/β (alpha-beta) ratio, and the Four R's of radiobiology.
- How to do fractionation math (BED and EQD2) and tell deterministic from stochastic effects.

## Why this matters

Every plan you deliver is physics made personal: a beam of known energy, aimed with millimeter care, depositing dose that biology then turns into a clinical result. If you understand how the beam is made, how it interacts, and how cells respond, you can reason about why a regimen is written the way it is — and catch the rare error before it reaches a patient.

## Radiation Sources

### Cobalt-60: a radioactive source

Cobalt-60 (written Co-60) is a radioactive isotope sealed inside a treatment head. It decays steadily, and as it does it emits two **gamma rays** — high-energy photons born in the nucleus — with energies of **1.17 MeV and 1.33 MeV**. (One **MeV**, or million electron volts, is a unit of energy; the *average* photon energy of a Co-60 beam is about 1.25 MeV.)

Co-60 has a **half-life of 5.27 years**. Half-life is the time for half of the radioactive atoms to decay. Think of it like a pile of popcorn kernels popping at random: after one half-life, half are "popped" (decayed). This matters clinically because the source weakens over time, so the machine takes longer to deliver the same dose as it ages, and the source must eventually be replaced.

> **Key Point:** Co-60 emits 1.17 and 1.33 MeV gammas (mean ≈ 1.25 MeV) and has a 5.27-year half-life. Its output decays predictably, so treatment times lengthen as the source ages.

### Linac x-rays: bremsstrahlung and characteristic x-rays

A medical **linear accelerator (linac)** does not use a radioactive source. Instead it accelerates electrons to high speed and slams them into a metal **target** (usually tungsten). Two kinds of x-rays come out.

**Bremsstrahlung** (German for "braking radiation") is the main one. When a fast electron passes near a heavy nucleus, the nucleus's positive charge tugs on it and bends its path. The electron slows and swerves, and the energy it loses is released as an x-ray photon. Picture a car braking hard and throwing off heat — except here the "heat" is an x-ray. Bremsstrahlung produces a *spectrum* of energies, from very low up to the full energy of the incoming electron.

**Characteristic x-rays** are the second kind. An incoming electron can knock an inner-shell electron out of a target atom. An outer electron then drops down to fill the gap, releasing a photon whose energy equals the difference between the two shells. Because that energy gap is fixed for each element, these photons have sharp, "characteristic" energies — a fingerprint of the target material.

## Beam Quality and Attenuation

### Energy ranges: kV vs MV

Beams are grouped by energy. **Kilovoltage (kV)** beams — thousands of volts — are low energy, used for superficial skin lesions and for imaging. **Megavoltage (MV)** beams — millions of volts — are high energy and penetrate deep, which is what you need to treat tumors inside the body. Most external-beam treatment uses MV photons (commonly 6–18 MV).

### Half-value layer (HVL)

Energy alone does not fully describe a kV beam, because it is a mix of energies. So we add **half-value layer (HVL)**: the thickness of a chosen material (often aluminum or copper) that cuts the beam intensity in half. A "harder" (more penetrating) beam needs a thicker HVL. HVL is a practical stand-in for beam quality, especially in the kV range.

### Exponential attenuation

As a photon beam passes through material, it gets weaker — it is **attenuated**. For a narrow beam this follows an exponential law:

> I = I₀ · e^(−µx)

Reading the symbols:
- **I** is the intensity that comes out the far side.
- **I₀** ("I-naught") is the intensity going in.
- **e** is the mathematical constant ≈ 2.718.
- **µ** ("mu") is the **linear attenuation coefficient** — how strongly this material absorbs this beam (units of per-centimeter).
- **x** is the thickness of material.

The exponential shape means the beam never quite reaches zero; each equal slab removes the same *fraction*, not the same amount. After one HVL, I = ½·I₀; after two HVLs, ¼·I₀; after three, ⅛·I₀, and so on.

## The Three Photon Interactions

When a photon deposits energy in tissue, it does so through one of three main interactions. Which one dominates depends mostly on **photon energy** and on **Z**, the atomic number of the material (the number of protons; higher Z means a "heavier," more electron-rich atom).

| Interaction | Dominant energy range | Z dependence | Plain-language picture |
|---|---|---|---|
| Photoelectric | Low (kV) | Strong (≈ Z³) | Photon is fully absorbed; ejects an inner electron |
| Compton scatter | Megavoltage therapy | Nearly none | Photon glances off an outer electron, like a billiard break |
| Pair production | Above 1.02 MeV (matters at high MV) | Increases with Z | Photon converts into an electron–positron pair |

### Photoelectric effect

A low-energy photon is **completely absorbed** by an atom, which then ejects an inner-shell electron. Because the probability rises sharply with atomic number (roughly Z³), bone (higher Z, due to calcium) absorbs far more than soft tissue at kV energies. That strong Z dependence is exactly what makes bone show up bright on a diagnostic x-ray — and why the photoelectric effect dominates in the kV range.

### Compton scatter

At **megavoltage therapy energies, Compton scatter dominates.** Here the photon strikes a loosely bound outer electron, knocks it loose, and **scatters** off in a new direction with less energy — like one billiard ball striking another and ricocheting. The key clinical fact: Compton probability barely depends on Z. That is why MV beams treat bone, fat, and muscle fairly uniformly, and why dense bone does not cast the heavy shadows on MV images that it does on kV images.

> **Key Point:** At the MV energies used for treatment, **Compton scatter is the dominant interaction**, and it is nearly independent of atomic number — so dose deposits relatively evenly across tissue types.

### Pair production

If a photon carries more than **1.02 MeV**, it can pass near a nucleus and convert its energy into matter: an electron and a positron (its antimatter twin). That 1.02 MeV is the **threshold** because the two particles together require that much energy to exist (each rest mass is 0.511 MeV; 0.511 + 0.511 = 1.022). Pair production becomes meaningful only at high MV energies and increases with Z.

## The Inverse-Square Law

Radiation from a point source spreads out as it travels, so intensity drops with distance. The **inverse-square law** lets you scale dose from one distance to another:

> D₂ = D₁ × (d₁ / d₂)²

where **D₁** is the dose (or dose rate) at distance **d₁**, and **D₂** is the dose at the new distance **d₂**. The relationship is squared, so doubling the distance cuts intensity to one-quarter, and tripling it to one-ninth.

A quick example: if the dose rate is 100 cGy/min at 100 cm, what is it at 200 cm?

D₂ = 100 × (100 / 200)² = 100 × (0.5)² = 100 × 0.25 = **25 cGy/min**.

Think of a flashlight: step back and the same light spreads over a much larger wall, so any one spot looks dimmer.

## Units of Radiation

Three quantities, three units — keep them separate.

| Quantity | SI unit | What it measures | Legacy unit | Conversion |
|---|---|---|---|---|
| Absorbed dose | **Gray (Gy)** | Energy absorbed per mass = 1 joule/kg | rad | 1 Gy = 100 rad |
| Equivalent dose | **Sievert (Sv)** | Dose weighted for biological harm | rem | 1 Sv = 100 rem |
| Activity | **Becquerel (Bq)** | Decays per second of a source | curie (Ci) | — |
| Exposure (legacy) | — | Ionization of air | roentgen (R) | — |

- **Gray** is the workhorse of treatment. One Gray equals one joule of energy deposited per kilogram of tissue.
- **Sievert** adjusts the dose for how damaging the radiation type is (more on that under RBE). For the photons and electrons you use, the numerical Gray and Sievert values are essentially the same.
- **Becquerel** counts radioactive decays per second — it describes a *source*, not a patient's dose.

> **Common mix-up:** *Gray vs Sievert.* Gray is pure physical energy deposited (1 J/kg). Sievert is that energy **weighted for biological effect**, used in radiation protection. In therapy you prescribe and report in **Gray**; you'll see Sievert mostly in dose-limit and safety contexts.

## Calibration Basics (TG-51)

Before a beam can be trusted, it must be **calibrated** — its output measured against a standard. In North America, photon and electron beams are calibrated using the **AAPM TG-51** protocol [3], which is based on absorbed dose to water.

- For **photon beams**, the reference measurement is taken with an ion chamber at **10 cm depth in water**. Water is used because it closely mimics soft tissue.
- For **electron beams**, beam quality is specified by **R50** — the depth in water at which the dose has fallen to **50%** of its maximum. R50 stands in for electron energy, much as HVL stands in for kV photon quality.

## Cell Survival and the Linear-Quadratic Model

Radiobiology asks: when you deliver dose, how many cells survive? Plotting surviving fraction against dose gives a **cell survival curve**. The most-used description is the **linear-quadratic (LQ) model**:

> S = e^(−αD − βD²)

Reading it:
- **S** is the surviving fraction (the share of cells still able to divide).
- **D** is the dose in Gray.
- **α** ("alpha") describes damage proportional to dose — single, lethal, "one-hit" hits.
- **β** ("beta") describes damage proportional to dose-squared — two separate sublethal hits that combine to kill.

At low dose the α term (the straight part) leads; at higher dose the β term (the curving "shoulder") bends the curve down more steeply.

### The α/β ratio

The **α/β ratio** (in Gray) is the dose at which the α-kill and β-kill are equal. It captures how a tissue responds to fraction size:

- **≈ 10 Gy** for most tumors and **early-responding** tissues (skin, gut lining) — they tolerate larger fractions relatively well.
- **≈ 3 Gy** for **late-responding** tissues (spinal cord, lung, kidney) — they are *more* sensitive to large fraction sizes.

This single number is why we fractionate: many small daily doses spare low-α/β late-responding normal tissue while still controlling the tumor.

## The Four R's of Radiobiology

These explain why splitting dose into fractions works [5]:

1. **Repair** — Between fractions, normal cells repair sublethal damage better than tumor cells, so the gap favors healthy tissue.
2. **Repopulation** — Surviving cells divide to replace losses. Helpful for normal tissue; a problem if a tumor repopulates during a long course.
3. **Reoxygenation** — After each fraction, previously oxygen-starved (hypoxic) tumor cells gain oxygen and become more radiosensitive for the next dose.
4. **Reassortment (redistribution)** — Cells move through the cell cycle and tend to redistribute into more radiosensitive phases between fractions.

> **Key Point:** Fractionation exploits the Four R's — chiefly **Repair** and **Reoxygenation** — to widen the gap between tumor kill and normal-tissue damage.

## The Oxygen Effect, LET, and RBE

### Oxygen effect

Oxygen makes radiation damage permanent by "fixing" it chemically. So well-oxygenated cells are killed more easily than hypoxic ones; **hypoxia causes radioresistance**. We quantify this with the **oxygen enhancement ratio (OER)** — the dose needed without oxygen divided by the dose needed with oxygen for the same effect. For low-LET radiation, **OER ≈ 2.5–3.0**, meaning a hypoxic cell needs up to about three times the dose.

### LET and RBE

**LET (linear energy transfer)** is how densely a particle deposits energy along its track. Photons and electrons are **low-LET** — they sprinkle energy sparsely, like light rain. Alpha particles, neutrons, and carbon ions are **high-LET** — they dump energy in a dense trail, like a knife cut, causing clustered, hard-to-repair damage.

**RBE (relative biological effectiveness)** compares radiation types: the dose of a reference (low-LET) beam divided by the dose of the test beam that produces the *same* biological effect.

> **Key Point:** Low-LET photons/electrons have RBE ≈ 1. **High-LET** radiation (alpha, neutron, carbon) packs damage densely, so its **RBE > 1**, and high-LET damage is also less oxygen-dependent (lower OER).

## Fractionation Math: BED and EQD2

Two formulas let you compare regimens with different fraction sizes on a common biological scale.

**Biologically Effective Dose (BED):**

> BED = n · d · (1 + d / (α/β))

- **n** = number of fractions
- **d** = dose per fraction (Gy)
- **n · d** = total physical dose
- the bracket adds the extra "punch" of larger fractions

**Equivalent Dose in 2-Gy fractions (EQD2)** rescales BED into the familiar 2 Gy/fraction world:

> EQD2 = BED / (1 + 2 / (α/β))

### Fully worked example

A lung SBRT (stereotactic body radiation therapy) regimen delivers **50 Gy in 5 fractions**. Convert it to BED and EQD2, using **α/β = 10 Gy** (tumor).

**Step 1 — find dose per fraction (d):**
d = total dose ÷ number of fractions = 50 Gy ÷ 5 = **10 Gy per fraction**. And n = 5.

**Step 2 — compute the bracket for BED:**
d / (α/β) = 10 / 10 = 1.
1 + 1 = **2**.

**Step 3 — compute BED:**
BED = n · d · (bracket) = 5 × 10 × 2 = **100 Gy** (often written 100 Gy₁₀ to note α/β = 10).

**Step 4 — compute the EQD2 denominator:**
2 / (α/β) = 2 / 10 = 0.2.
1 + 0.2 = **1.2**.

**Step 5 — compute EQD2:**
EQD2 = BED ÷ 1.2 = 100 ÷ 1.2 ≈ **83.3 Gy**.

So 50 Gy in 5 fractions is biologically like delivering about **83 Gy** in standard 2 Gy fractions — far more potent than its 50 Gy physical dose suggests, which is exactly why SBRT controls tumors so well in few fractions.

## Deterministic vs Stochastic Effects

Radiation effects fall into two camps.

**Deterministic effects** have a **threshold** dose; below it nothing happens, and above it **severity rises with dose**. Examples: skin erythema (reddening), cataract, and sterility. Think of a dam: nothing spills until the water passes the rim, then more water means more flooding.

**Stochastic effects** have **no threshold**; instead the **probability** rises with dose, while severity does not depend on dose. Examples: cancer and heritable (genetic) effects. Here every drop adds a little to the *chance* of an event, but a cancer that occurs is no "worse" because the dose was higher [4].

> **Common mix-up:** *Deterministic vs stochastic.* Deterministic = threshold + dose-dependent **severity** (tissue reactions). Stochastic = no threshold + dose-dependent **probability** (cancer, heritable). A useful tag: deterministic effects you can *see at the bedside*; stochastic effects are statistical risks.

## Tissue Tolerance (TD5/5 Examples)

**TD5/5** is the tolerance dose expected to cause a serious complication in 5% of patients within 5 years. A few values worth knowing:

| Tissue | Approximate limit |
|---|---|
| Spinal cord | ~45–50 Gy |
| Lung | mean dose ≤ ~20 Gy, or V20 ≤ ~35% |
| Eye lens | ~0.5 Gy |

(Here **V20** means the percentage of lung volume receiving 20 Gy or more.) The eye lens is strikingly sensitive — a cataract (a deterministic effect) can follow a dose far below what other tissues tolerate, which is why we shield eyes whenever the plan allows.

## Check yourself

**1. Which interaction dominates at megavoltage therapy energies, and does it depend on atomic number?**
*Compton scatter dominates at MV therapy energies, and it is nearly independent of atomic number — so MV dose deposits fairly evenly across bone, fat, and muscle.*

**2. A source reads 80 cGy/min at 100 cm. What is the dose rate at 50 cm?**
*Using D₂ = D₁ × (d₁/d₂)²: D₂ = 80 × (100/50)² = 80 × 4 = 320 cGy/min.*

**3. What is the difference between a Gray and a Sievert?**
*A Gray is absorbed dose — pure energy deposited (1 joule/kg). A Sievert is equivalent dose — that energy weighted for biological harm, used in radiation protection.*

**4. A regimen is 60 Gy in 3 fractions (20 Gy/fx), α/β = 10. What is the BED?**
*BED = n·d·(1 + d/(α/β)) = 3 × 20 × (1 + 20/10) = 60 × 3 = 180 Gy.*

**5. Erythema, cataract, and sterility are which kind of effect, and why?**
*Deterministic — they have a threshold dose, below which they do not occur, and their severity increases with dose.*

**6. Why does hypoxia make a tumor harder to treat, and what number describes it?**
*Oxygen "fixes" radiation damage, so oxygen-poor (hypoxic) cells are more radioresistant. The oxygen enhancement ratio (OER ≈ 2.5–3.0 for low-LET radiation) quantifies how much more dose hypoxic cells need.*

## Chapter references

1. Khan FM, Gibbons JP. *Khan's The Physics of Radiation Therapy.* Wolters Kluwer / Lippincott Williams & Wilkins. (Radiation sources, photon interactions, attenuation, inverse-square law, units, calibration.)
2. Hall EJ, Giaccia AJ. *Radiobiology for the Radiologist.* Wolters Kluwer. (Cell survival, linear-quadratic model, α/β ratio, Four R's, oxygen effect, LET/RBE, fractionation.)
3. Almond PR, et al. AAPM TG-51: Protocol for clinical reference dosimetry of high-energy photon and electron beams. *Medical Physics*. (Photon calibration at 10 cm depth in water; electron beam quality by R50.)
4. International Commission on Radiological Protection (ICRP) and U.S. Nuclear Regulatory Commission (NRC). Radiation units, deterministic vs stochastic effects, and dose-limit context. (Gray, Sievert, Becquerel; legacy rad/rem/roentgen.)
5. Centers for Disease Control and Prevention (CDC). Radiation health effects: deterministic (tissue reactions) and stochastic (cancer, heritable) effects. (Public-health framing of dose-response.)
