# Chapter 3 — Radiation Physics & Radiobiology

## What you'll learn

- Where therapy radiation comes from — radioactive decay and machine-made x-rays.
- How a beam weakens with distance (the inverse-square law) and with shielding (attenuation and the half-value layer).
- The three ways photons interact with matter, and why **Compton scatter** is the one that matters most in treatment.
- The units we measure radiation in — gray, sievert, and becquerel — and what each one really means.
- How radiation damages cells, why we split treatment into many small fractions, and the math behind it (the linear-quadratic model, BED, and EQD2).
- The difference between deterministic and stochastic effects, and what normal-tissue tolerance means.

Physics is the part of the registry that worries students the most, so we are going to slow down, build each idea from the ground up, and lean on pictures. Nothing here requires fancy math — just a willingness to take it one step at a time. Every concept ties back to a real job you will do at the machine: choosing an energy, keeping yourself safe, and understanding why the prescription is written the way it is.

## Part 1 · Where radiation comes from

### The atom, in sixty seconds

Everything starts with the atom: a tiny, dense **nucleus** (protons and neutrons, positively charged) surrounded by **electrons** in shells. Radiation therapy is all about adding enough energy to knock electrons loose. When a photon or particle has enough energy to eject an electron from an atom, we call it **ionizing radiation**, and the atom left behind is now an **ion**. That single act — ionization — is the seed of everything that follows, from the image on your screen to the DNA break inside a tumor cell.

> **Key Point:** "Ionizing" means "able to knock electrons off atoms." That is the dividing line between the radiation we use to treat cancer and the harmless radiation of, say, a radio wave.

### Radioactive sources and decay

Some atoms are unstable and shed energy over time — they are **radioactive**. The classic therapy example is **Cobalt-60**. Cobalt-60 first emits a beta particle, turning into an excited nickel atom, which then releases its extra energy as **two gamma rays** of 1.17 MeV and 1.33 MeV. (An *MeV*, mega-electron-volt, is just a unit of energy.) Because the two gammas come out together, we usually treat the average therapy energy as about **1.25 MeV**.

![Cobalt-60 decay scheme](figures/fig-co60-decay.svg)

*Figure 3.1 — Cobalt-60 decays by beta emission to excited nickel-60, which drops to its stable ground state by releasing two gamma rays. Their average energy (~1.25 MeV) is the effective treatment energy.*

Two terms describe a radioactive source:

- **Half-life** — the time for half of the atoms to decay. Cobalt-60's half-life is **5.27 years**, which is why cobalt units must eventually have their source replaced: after about five years, the source is only half as "bright."
- **Activity** — how many atoms decay per second. The modern unit is the **becquerel (Bq)** = 1 decay per second. The older unit is the **curie (Ci)**, where 1 Ci = 3.7 × 10¹⁰ Bq.

> **Common mix-up:** Half-life is about *time* (how fast a source weakens); activity is about *rate* (how many decays happen each second). They are related but not the same number.

### Machine-made x-rays

Most modern treatment uses a **linear accelerator (linac)**, which makes x-rays on demand rather than relying on a radioactive source. It speeds electrons up to high energy and slams them into a metal **target** (usually tungsten). Two things happen:

- **Bremsstrahlung** ("braking radiation," Figure 3.2). An electron passes close to a nucleus, gets deflected and slowed, and the energy it loses flies off as an x-ray. This is the **main** source of the treatment beam. The higher the electron energy, the more — and more penetrating — the x-rays.
- **Characteristic x-rays.** An incoming electron knocks out an inner-shell electron; when an outer electron drops in to fill the gap, it releases an x-ray whose energy is *characteristic* of that element. These make up a small part of the beam.

![Bremsstrahlung production](figures/fig-bremsstrahlung.svg)

*Figure 3.2 — Bremsstrahlung: a fast electron is deflected by a nucleus, loses energy, and that energy leaves as an x-ray photon. This is how a linac builds its treatment beam.*

## Part 2 · How a beam travels and weakens

### Photon energy: kV versus MV

Beam energy is described by voltage. **Kilovoltage (kV)** beams (tens to a few hundred kV) are low energy — good for superficial skin lesions and for the crisp, bony-contrast images you match at the machine. **Megavoltage (MV)** beams (typically 6–18 MV from a linac) are high energy and penetrating — that is what reaches deep tumors. Keeping this kV-versus-MV distinction in mind explains a lot, including why your setup images and your treatment beam look so different.

### The inverse-square law

Radiation spreads out from its source like light from a bare bulb. As it travels, the same energy is smeared over a larger and larger area, so the intensity drops — and it drops with the **square** of the distance.

![Inverse-square law](figures/fig-inverse-square.svg)

*Figure 3.3 — The same rays cover four times the area at twice the distance, so the dose rate falls to one-quarter. At three times the distance it is one-ninth.*

We write it as:

> **Key Point:** **D₂ = D₁ × (d₁/d₂)²**, where d₁ and d₂ are distances from the source.

**Worked example.** A point source delivers 100 cGy at 80 cm. What is the dose rate at 100 cm?

```
D2 = D1 × (d1 / d2)²
D2 = 100 × (80 / 100)²
D2 = 100 × (0.8)²
D2 = 100 × 0.64  =  64 cGy
```

Notice the dose did not drop by 20% just because the distance grew by 20% — it dropped by 36%, because of the squaring. This is also your friend in radiation protection: **stepping back a little buys a lot of safety** (more on that in Chapter 4).

### Attenuation and the half-value layer

Distance is one way a beam weakens; passing through material is the other. As photons travel through tissue or shielding, some are absorbed or scattered away. This follows an **exponential** pattern: each equal thickness removes the *same fraction* of what is left, not the same amount.

The handiest measure of this is the **half-value layer (HVL)** — the thickness of a material that cuts the beam intensity in half.

![Exponential attenuation and HVL](figures/fig-attenuation-hvl.svg)

*Figure 3.4 — Each half-value layer removes half of the remaining beam: 100% → 50% → 25% → 12.5%. Because it is always "half of what's left," the beam approaches zero but never quite gets there.*

**Worked example.** A beam starts at 100%. If the HVL of a shielding material is 1.2 cm, how much gets through 3.6 cm?

```
3.6 cm ÷ 1.2 cm = 3 half-value layers
After 1 HVL: 50%
After 2 HVL: 25%
After 3 HVL: 12.5%
```

So 12.5% of the beam comes through. HVL is also a measure of **beam quality** (penetrating power): a higher-energy, more penetrating beam has a larger HVL because it takes more material to halve it.

> **Common mix-up:** Attenuation is **exponential**, not linear. Three HVLs do not block "150%" — each layer halves what remains, so you get 50% → 25% → 12.5%.

## Part 3 · How photons interact with matter

When a photon does interact, it does so in one of three main ways. Knowing them explains image contrast, beam penetration, and why MV beams are skin-sparing.

![Three photon interactions](figures/fig-photon-interactions.svg)

*Figure 3.5 — The three photon interactions. Photoelectric: the photon is fully absorbed and an inner electron is ejected. Compton: the photon scatters off an outer electron, giving up part of its energy. Pair production: a high-energy photon converts into an electron–positron pair near the nucleus.*

- **Photoelectric effect.** The photon hands **all** of its energy to a tightly bound inner-shell electron, which is ejected; no scattered photon survives. It dominates at **low energies** and is very sensitive to atomic number — roughly proportional to **Z³**. That strong Z dependence is exactly why **bone (high Z, calcium) shows up bright on kV images**: bone soaks up low-energy photons far more than soft tissue does. This is the physics behind the crisp skeletal detail you use when you bone-match a setup image.
- **Compton scatter.** The photon strikes a loosely bound **outer** electron, gives up part of its energy, and **scatters** off in a new direction while the electron recoils. Compton is almost independent of atomic number and **dominates across the megavoltage therapy range**. Two consequences follow: MV treatment beams deposit dose similarly in bone and soft tissue (so MV images have poor bone contrast), and scattered photons are the reason treatment rooms need **secondary** shielding (Chapter 4).
- **Pair production.** Only above a **threshold of 1.02 MeV**, a photon passing near a nucleus can convert into an **electron–positron pair** (matter created from energy). It becomes significant only at high energies and high Z, so it plays a minor role at common therapy energies.

![Which interaction dominates](figures/fig-interaction-dominance.svg)

*Figure 3.6 — Photoelectric rules at low energy/high Z, pair production at very high energy/high Z, and Compton owns the broad middle band — which is exactly where megavoltage therapy lives.*

> **Key Point:** In the **megavoltage** beams you treat with every day, **Compton scatter dominates**. That single fact explains poor bone contrast on MV images, the need for scatter shielding, and the uniform way MV dose is deposited.

### Build-up and skin-sparing

Here is a payoff of all that interaction physics. When an MV photon interacts, it sets fast electrons moving *forward*. Those electrons travel a short distance before they deposit their dose, so the maximum dose lands a little **below** the skin, not on it. The result is the **build-up region** and the skin-sparing that makes high-energy x-rays so useful.

![Megavoltage depth dose](figures/fig-depth-dose.svg)

*Figure 3.7 — A megavoltage beam enters with a low surface (skin) dose, builds up to its maximum at d_max, then falls off with depth. Higher energy pushes d_max deeper and spares the skin more.*

The depth of maximum dose, **d_max**, gets deeper as energy rises (for example, roughly 1.5 cm for a 6 MV beam and around 3 cm for an 18 MV beam). This is why higher energies are chosen for deeper tumors — they put their peak dose where the target is, while keeping the skin dose comfortable.

## Part 4 · Measuring radiation: the units

Three units cover almost everything on the exam.

| Quantity | SI unit | Plain-English meaning | Older unit |
|---|---|---|---|
| **Absorbed dose** | **Gray (Gy)** | Energy actually deposited: 1 Gy = 1 joule per kilogram | rad (1 Gy = 100 rad) |
| **Equivalent dose** | **Sievert (Sv)** | Absorbed dose adjusted for how harmful the radiation type is | rem (1 Sv = 100 rem) |
| **Activity** | **Becquerel (Bq)** | How many atoms decay per second | curie (1 Ci = 3.7 × 10¹⁰ Bq) |

A couple of anchors worth memorizing: **1 Gy = 100 rad** and **1 Sv = 100 rem**. For the x-rays, gammas, and electrons used in radiation therapy, the "harm factor" (radiation weighting factor) is 1, so **1 Gy of our beam equals 1 Sv**. The gray and sievert only diverge for high-LET radiations like alpha particles and neutrons.

> **Common mix-up:** **Gray** measures energy *deposited in tissue* — it is what the prescription is written in. **Sievert** measures *biological risk* and is the unit of dose limits and badge readings (Chapter 4). Same size for our beams, different jobs.

A quick word on calibration: physicists make sure "what the machine says" equals "what the patient gets" using the **AAPM TG-51** protocol, which calibrates photon beams at a reference depth of **10 cm in water** and specifies an electron beam's quality by **R₅₀** (the depth where dose falls to 50%). You do not perform this, but you should recognize the names.

## Part 5 · Radiobiology: what radiation does to cells

### Direct and indirect action

Radiation kills cells mainly by damaging **DNA**. It can do this two ways: **directly**, by breaking the DNA strand itself, or **indirectly**, by ionizing nearby water to create reactive **free radicals** that then attack the DNA. For the low-LET radiation we use most, the **indirect** path through water and free radicals causes the majority of the damage — which is also why **oxygen matters** so much (coming up).

### The cell survival curve and the linear-quadratic model

If you irradiate a population of cells with rising doses and plot the fraction that survive on a log scale, you get the famous **cell survival curve**.

![Cell survival curve](figures/fig-cell-survival.svg)

*Figure 3.8 — For low-LET x-rays the curve has a "shoulder" at low dose (cells repairing sublethal damage) before bending steeply downward. High-LET radiation gives a straighter, steeper line — more lethal per gray, with little repair.*

We describe the curve with the **linear-quadratic (LQ) model**:

> **Key Point:** **S = e^(−αD − βD²)** — survival falls off with a single-hit term (**α**, linear in dose) and a two-hit term (**β**, dose-squared).

The ratio **α/β** captures how a tissue responds to the *size* of each dose:

- **High α/β (≈ 10 Gy)** — tumors and early-responding tissues (skin, mucosa, gut). These care more about *total* dose.
- **Low α/β (≈ 3 Gy)** — late-responding tissues (spinal cord, lung, kidney). These are very sensitive to *large* doses per fraction.

This difference is the whole reason we usually give many **small** fractions: small daily doses spare the low-α/β late-responding normal tissues while still controlling the tumor.

### LET and RBE

- **LET (Linear Energy Transfer)** is how densely a radiation deposits energy along its track. X-rays and electrons are **low-LET** (sparse ionizations); alpha particles, neutrons, and carbon ions are **high-LET** (dense ionizations that overwhelm repair).
- **RBE (Relative Biological Effectiveness)** compares how much of a reference radiation it takes to get the same effect as a test radiation. High-LET radiation has **RBE > 1** — it does more biological damage per gray.

> **Common mix-up:** LET describes the *radiation's* track structure; RBE describes the *biological result*. As LET rises, RBE generally rises with it — up to a point.

### The oxygen effect

Because so much damage is done indirectly through free radicals, **oxygen** dramatically increases radiation's killing power: it "fixes" (makes permanent) the chemical damage. Well-oxygenated cells are far more radiosensitive than hypoxic (oxygen-starved) ones.

![The oxygen effect](figures/fig-oxygen-effect.svg)

*Figure 3.9 — Oxygenated cells (left curve) die at lower doses than hypoxic cells (right curve). The ratio of doses needed for the same effect is the Oxygen Enhancement Ratio, about 2.5–3 for low-LET radiation.*

We quantify this with the **Oxygen Enhancement Ratio (OER) ≈ 2.5–3** for x-rays. Tumors often contain hypoxic, resistant pockets — and this is one more reason fractionation helps: between fractions, tumors **reoxygenate**, turning resistant cells into sensitive ones.

### The Four R's of radiobiology

These four processes explain *why fractionation works*:

1. **Repair** — between fractions, normal cells repair sublethal damage (the "shoulder" returns each day). Late-responding normal tissue benefits most.
2. **Repopulation** — surviving cells divide during a long course; this is why dragging treatment out too long can let a tumor regrow.
3. **Reoxygenation** — hypoxic tumor regions regain oxygen between fractions and become easier to kill.
4. **Reassortment (redistribution)** — cells get caught in radiosensitive phases of their cycle over repeated fractions.

> **Key Point:** Repair and Repopulation tend to **protect** tissues; Reoxygenation and Reassortment tend to **sensitize** the tumor. Fractionation is the art of tilting that balance in the patient's favor.

### Fractionation math: BED and EQD2

To compare different fraction schemes fairly, we use **Biologically Effective Dose (BED)** and the **Equivalent Dose in 2-Gy fractions (EQD2)**:

```
BED  = n · d · (1 + d / (α/β))
EQD2 = BED / (1 + 2 / (α/β))
   n = number of fractions
   d = dose per fraction
```

**Worked example 1 — a standard course, two tissues.** 60 Gy in 30 fractions (so n = 30, d = 2 Gy).

```
Tumor (α/β = 10):       BED = 60 × (1 + 2/10) = 60 × 1.2   = 72 Gy
Late tissue (α/β = 3):  BED = 60 × (1 + 2/3)  = 60 × 1.667 ≈ 100 Gy
```

The same physical 60 Gy is biologically "heavier" for the late-responding tissue — which is precisely why we respect its dose limits.

**Worked example 2 — converting an SBRT course to EQD2.** A lung tumor gets 50 Gy in 5 fractions (n = 5, d = 10 Gy, α/β = 10).

```
BED  = 5 × 10 × (1 + 10/10) = 50 × 2 = 100 Gy
EQD2 = 100 / (1 + 2/10)     = 100 / 1.2 ≈ 83 Gy
```

So that short, punchy SBRT course is biologically like ~83 Gy given in gentle 2-Gy fractions — far more than its 50 Gy "sticker price." This is why high-dose-per-fraction treatments are so potent (and why their normal-tissue limits are handled carefully).

## Part 6 · Effects on tissue and people

### Deterministic versus stochastic effects

Radiation's harmful effects come in two flavors, and the exam loves to test the distinction.

![Deterministic versus stochastic effects](figures/fig-deterministic-stochastic.svg)

*Figure 3.10 — Deterministic effects have a threshold: below it, nothing; above it, severity grows with dose. Stochastic effects have no threshold: the probability rises with dose, but severity does not.*

- **Deterministic (tissue reactions)** — there is a **threshold dose**, and above it the **severity** climbs with dose. Examples: skin erythema, cataracts, sterility, fibrosis. These are predictable and dose-dependent.
- **Stochastic (chance) effects** — **no threshold**; the **probability** of the effect rises with dose, but the severity does not depend on dose. Examples: radiation-induced cancer and heritable effects. This is the basis of the "no safe dose" precaution behind ALARA.

> **Common mix-up:** Deterministic = *severity* rises with dose, above a threshold. Stochastic = *probability* rises with dose, no threshold. A cataract is deterministic; a radiation-induced cancer is stochastic.

### Normal-tissue tolerance

Every organ has a dose it can tolerate before complications become likely. A common shorthand is **TD₅/₅** — the dose expected to cause a 5% complication rate within 5 years. A few values worth recognizing (conventional fractionation):

- **Spinal cord:** about **45–50 Gy** (we keep cord dose well under this to avoid myelopathy).
- **Lung:** mean dose roughly **≤ 20 Gy**, or keep the volume getting ≥ 20 Gy (V20) under about 35%, to limit pneumonitis.
- **Eye lens:** a threshold around **0.5 Gy** for cataract formation.

These numbers are why the prescription and plan obey **organ-at-risk constraints**, and why the dose-volume histogram (Chapter 6) is checked so carefully.

## Check yourself

**1. Cobalt-60 emits gamma rays of what energies, and what is its half-life?**
*1.17 and 1.33 MeV (average ≈ 1.25 MeV), with a half-life of 5.27 years.*

**2. Which photon interaction dominates at megavoltage therapy energies, and name one practical consequence.**
*Compton scatter. Consequences include poor bone contrast on MV images and the need for secondary (scatter) shielding.*

**3. A source gives 200 cGy at 100 cm. Using the inverse-square law, what is the dose rate at 140 cm?**
*D₂ = 200 × (100/140)² = 200 × 0.510 ≈ 102 cGy.*

**4. A beam is 100%. After passing through 2 half-value layers, how much remains?**
*25% (100% → 50% → 25%). Attenuation is exponential — each HVL halves what is left.*

**5. What is the difference between the gray and the sievert?**
*The gray measures absorbed dose (energy deposited, used for prescriptions); the sievert measures equivalent dose (biological risk, used for dose limits). For therapy x-rays they are numerically equal.*

**6. Convert 50 Gy in 5 fractions (α/β = 10) to BED.**
*BED = 5 × 10 × (1 + 10/10) = 100 Gy.*

**7. A cataract from radiation is which type of effect — deterministic or stochastic — and why?**
*Deterministic: it has a threshold dose, and severity increases with dose above that threshold.*

**8. Why does fractionation help spare late-responding normal tissue?**
*Late-responding tissue has a low α/β (~3 Gy), making it very sensitive to large doses per fraction; small daily fractions plus overnight Repair keep its biological dose low while the tumor is still controlled.*

## Chapter references

**Free, full-text sources**

1. IAEA — *Radiation Oncology Physics: A Handbook for Teachers and Students* (free PDF; beam production, interactions, attenuation, depth dose, units, radiobiology): <https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1196_web.pdf>.
2. AAPM Reports — TG-51 reference dosimetry (R₅₀ for electron beam quality), free: <https://www.aapm.org/pubs/reports/>.
3. U.S. NRC — 10 CFR Part 20, Standards for Protection Against Radiation (quantities, units): <https://www.nrc.gov/reading-rm/doc-collections/cfr/part020/>.
4. CDC — Radiation and your health (deterministic vs stochastic effects, ALARA): <https://www.cdc.gov/radiation-health/>.

**For deeper reading (library / textbook)**

5. Khan FM, Gibbons JP. *The Physics of Radiation Therapy.* Wolters Kluwer.
6. Hall EJ, Giaccia AJ. *Radiobiology for the Radiologist.* Wolters Kluwer.

*This chapter offers original educational explanations. It is not affiliated with or endorsed by the ARRT and does not reproduce actual exam questions.*
