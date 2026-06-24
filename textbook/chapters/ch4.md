# Chapter 4 — Radiation Protection, Equipment Operation & Quality Assurance

## What you'll learn

- How the **ALARA** principle works and how its three tools — **time, distance, and shielding** — actually lower dose, including why distance is so powerful (the inverse-square law).
- The U.S. **NRC dose limits** for occupational workers, the public, the declared-pregnant worker, and specific tissues — straight from 10 CFR 20.
- How treatment rooms are shielded: **primary vs. secondary barriers** and the design factors **W**, **U**, and **T**.
- How **personnel dosimeters** (TLD, film badge, OSL) work, where you wear them, and how often they're read.
- The major **linear accelerator components** and the **safety interlocks** that protect patients and staff.
- The backbone of a **quality assurance (QA)** program — linac checks (TG-142), imaging/IGRT checks (TG-179), and CT-simulator checks (TG-66).

## Why this matters

Radiation therapy delivers enormous, deliberate doses to patients while keeping the people around the beam safe. That balance only works because of layered protection: smart habits, well-designed rooms, monitored dosimeters, and machines that are checked constantly. As a therapist, you are the daily guardian of all four — and the ARRT registry will expect you to know the numbers and the reasons behind them cold.

---

## The ALARA Principle

**ALARA** stands for **As Low As Reasonably Achievable**. It is the guiding philosophy of all radiation protection. The idea is simple: even when a dose is legally allowed, you still try to keep it as low as you reasonably can, factoring in technology, cost, and the benefit of the procedure.

Think of ALARA like driving under the speed limit. The limit is the maximum, not a target. A careful driver routinely goes slower than allowed when conditions call for it. ALARA asks you to treat every dose limit the same way — as a ceiling you stay well beneath.

ALARA rests on three practical tools you can adjust at the bedside or in the control area: **time, distance, and shielding**.

> **Key Point:** ALARA is not a dose *limit* — it is a *mindset*. Limits are legal ceilings; ALARA pushes you to stay far below them whenever practical.

### Tool 1 — Time

The less time you spend near a radiation source, the less dose you receive. Dose accumulates in direct proportion to exposure time: double your time in the field, and you roughly double your dose.

In practice this means working efficiently and confidently around active sources — for example, during **brachytherapy** (treatment using radioactive sources placed in or near the tumor) — and never lingering. Rehearsing a procedure so you move quickly and deliberately is itself a radiation-protection strategy.

### Tool 2 — Distance and the Inverse-Square Law

Distance is the single most powerful protection tool, and the reason is the **inverse-square law**. This law states that the intensity of radiation from a point source falls off with the *square* of the distance from that source.

In formula form:

**I₁ / I₂ = (d₂)² / (d₁)²**

where I is intensity and d is distance. The practical takeaway: if you **double** your distance from a source, the intensity drops to **one-quarter** (because 2² = 4). Triple the distance, and intensity drops to one-ninth (3² = 9).

Picture radiation spreading out from a source like paint sprayed from a nozzle. Up close, the paint is dense on a small patch. As the spray fans out, the same amount of paint covers a much larger area, so any one spot gets far less. Stepping back a single extra step buys you outsized protection.

> **Common mix-up:** Students often think doubling distance *halves* dose. It does not — it cuts dose to a **quarter**. The relationship is squared, not linear.

### Tool 3 — Shielding

Shielding places absorbing material between you and the source. **High-density, high-atomic-number materials** like **lead** stop photons most efficiently per unit thickness, while **concrete** is used in bulk for walls because it is cheap and structural.

The amount of shielding is often described in **half-value layers (HVL)** — the thickness of material needed to cut the beam intensity in half. Stack enough half-value layers and the beam is reduced by a large, predictable factor.

In therapy, shielding shows up as the lead in the linac head, the thick concrete-and-lead vault walls, and the lead-lined door — not as a lead apron. (Lead aprons help in low-energy diagnostic imaging but are useless against the high-energy beams of a linac, which would pass right through them.)

---

## Occupational and Public Dose Limits (U.S. NRC, 10 CFR 20)

The U.S. Nuclear Regulatory Commission (**NRC**) sets enforceable dose limits in federal regulation **10 CFR Part 20** [1]. These are the numbers used in the United States and the ones the registry expects.

A quick unit note: the **sievert (Sv)** and **millisievert (mSv)** are SI units of *effective dose* (dose adjusted for biological harm). The older U.S. unit is the **rem**, where **1 rem = 10 mSv** (so 1 Sv = 100 rem).

| Category | Limit (SI) | Limit (conventional) |
|---|---|---|
| Occupational whole-body (annual) | **50 mSv/year** | 5 rem/year |
| Occupational **cumulative** lifetime | **10 mSv × age in years** | 1 rem × age |
| Lens of the eye (annual) | **150 mSv/year** | 15 rem/year |
| Skin / extremities (annual) | **500 mSv/year** | 50 rem/year |
| **Public** (annual) | **1 mSv/year** | 100 mrem/year |
| Declared-pregnant worker — embryo/fetus (entire pregnancy) | **5 mSv total** (~0.5 mSv/month) | 0.5 rem |

A few clarifications:

- The **whole-body** occupational limit is **50 mSv (5 rem) per year**. The NRC also applies a **cumulative** limit of **10 mSv multiplied by your age in years** — so a 40-year-old worker's lifetime total should not exceed 400 mSv.
- The **public** limit is **1 mSv (100 mrem) per year** — fifty times stricter than the occupational limit, because the public hasn't accepted the risk as part of a job and isn't monitored.
- A worker who voluntarily informs her employer in writing that she is pregnant becomes a **declared-pregnant worker**. The dose limit to the **embryo/fetus** is **5 mSv (0.5 rem) over the entire gestation**, and the NRC asks employers to avoid large monthly spikes — roughly **0.5 mSv per month**.
- The **lens of the eye** limit is **150 mSv/year**, and **skin and extremities** are limited to **500 mSv/year**. These tissues tolerate more local dose than the whole body.

> **Key Point:** Memorize the headline set: **occupational 50 mSv/yr, public 1 mSv/yr, fetus 5 mSv total, cumulative 10 mSv × age.** These four are registry favorites.

> **Common mix-up:** Some review sources quote the international **ICRP** occupational figure of 20 mSv/year or a 0.1 mSv public figure. For the U.S. registry, use the **NRC 10 CFR 20** values above — **50 mSv** occupational and **1 mSv** public.

---

## Facility Shielding (NCRP Report 151)

Treatment rooms are housed in heavily shielded vaults. The design rules come from **NCRP Report 151** [2]. Shielding barriers fall into two types based on what radiation they intercept.

### Primary vs. Secondary Barriers

- A **primary barrier** is the wall (or floor/ceiling) that the **direct, useful beam** can point at. Because it faces the full-strength beam, it is the thickest part of the vault.
- A **secondary barrier** handles only **leakage** (radiation that escapes the linac head despite its shielding) and **scatter** (radiation that bounces off the patient and room surfaces). These are weaker, so secondary barriers can be thinner.

Picture the primary barrier as the backstop directly behind home plate at a batting cage — it takes the hardest hits. Secondary barriers are the side netting that only catches deflections.

### The Design Factors: W, U, and T

NCRP-151 calculates required barrier thickness using three factors:

| Factor | Name | What it means |
|---|---|---|
| **W** | Workload | How much the machine is used — total dose delivered at 1 meter per week (e.g., Gy/week). Busier rooms need more shielding. |
| **U** | Use factor | The fraction of the workload the beam is aimed at a *particular* barrier. A floor might have U near 1; a given wall might be ¼. |
| **T** | Occupancy factor | How occupied the space *on the other side* of the barrier is. A full-time office (T = 1) demands more shielding than a rarely used storage closet or parking lot (T as low as 1/40). |

These combine so that a barrier protecting a busy office, frequently in the beam's path, in a high-workload room, must be thickest. Vault walls are typically built of **concrete** in bulk, with **lead** added where space is tight (lead gives more attenuation per inch).

### Controlled vs. Uncontrolled Areas

- A **controlled area** is occupied mainly by trained, monitored radiation workers (the control console area). It is held to the occupational framework.
- An **uncontrolled area** is anywhere the general public may be — waiting rooms, hallways, the floor above. These must meet the **public** limit of **1 mSv/year**, which is why shielding toward them is so demanding.

---

## Personnel Dosimetry

A **dosimeter** is a small device a worker wears to measure accumulated occupational dose. It does not protect you — it *records* what you received, much like a car's odometer logs distance after the fact.

| Type | How it works | Key traits |
|---|---|---|
| **TLD** (thermoluminescent dosimeter) | Crystals (commonly **lithium fluoride**) trap energy from radiation; heating them later releases light proportional to dose | **Reusable**; accurate; no instant readout |
| **Film badge** | Radiation darkens photographic film inside the badge | Provides a **permanent physical record**; **single-use** (not reusable); sensitive to heat/humidity |
| **OSL** (optically stimulated luminescence) | Aluminum-oxide crystals trap energy; **laser light** (not heat) releases it for reading | Reusable; can be re-read; very sensitive |

Dosimeters are typically **read monthly** by an outside service that reports each worker's dose.

**Placement** matters:

- Worn at the **collar** (outside any apron) for staff in diagnostic settings, estimating dose to the head, neck, and lens.
- Worn at the **waist** for whole-body monitoring.
- A pregnant worker often wears a **second** dosimeter at the **waist/abdomen** to track fetal dose specifically.

> **Key Point:** TLD and OSL are **reusable**; the **film badge is single-use** but leaves a **permanent record**. That trade-off — reusability vs. a permanent archive — is the classic exam distinction.

---

## Linear Accelerator Components

A medical **linear accelerator (linac)** speeds up electrons to high energy and either uses them directly or converts them into a photon (x-ray) beam. Knowing the path the beam takes through the head helps you understand both treatment and QA.

Following the beam from start to patient:

1. **Electron gun** — injects electrons into the accelerating structure, where microwaves boost them to high energy.
2. **Tungsten target** — for **photon** treatments, the fast electrons slam into this dense metal target, producing x-rays (bremsstrahlung). For **electron** treatments, the target is moved out of the way.
3. **Primary collimator** — a fixed shielding aperture that defines the largest possible beam and blocks stray radiation.
4. **Flattening filter** — a cone-shaped piece of metal that evens out the beam, which is naturally peaked in the center, into a uniform "flat" profile across the field.
   - **Flattening-filter-free (FFF)** modes remove this filter for very high dose rates, used in SRS/SBRT where the beam is small and speed reduces patient motion. The profile is then peaked but corrected by the planning system.
5. **Dual monitor ionization chambers** — two independent chambers measure the dose being delivered in real time. The redundancy is a safety feature: if one fails or they disagree, the beam shuts off.
6. **Jaws** — movable lead/tungsten blocks that set the rectangular field size.
7. **Multileaf collimator (MLC)** — dozens of thin, independently driven leaves that shape the beam to the tumor's outline and enable intensity-modulated and dynamic treatments.

> **Common mix-up:** The **target** makes photons; remove it and you have an electron beam. The **flattening filter** flattens photon beams; removing *it* gives the high-dose-rate **FFF** mode. Two different parts, two different jobs.

---

## Safety Interlocks

An **interlock** is an automatic safety circuit that stops the beam (or prevents it starting) when a condition is unsafe. Interlocks are deliberately **redundant** — built with backup circuits — so that no single failure can defeat them.

Key interlocks include:

- **Door interlock** — the beam cannot run if the vault door is open, keeping people out of the active field.
- **Beam-off / emergency-off (E-stop)** — large red buttons in the room and at the console that immediately kill the beam and machine motion.
- **Motion-disable / collision interlocks** — stop gantry, couch, or collimator movement if a collision or out-of-range condition is detected.

> **Key Point:** If an interlock trips, the safe response is to **stop, identify the cause, and resolve it** — never to bypass or "force" the machine past a safety circuit.

---

## Linac Quality Assurance (AAPM TG-142)

**Quality assurance (QA)** is the routine testing that confirms the machine performs within tolerance. The standard reference for linac QA is **AAPM Task Group 142 (TG-142)** [3]. Tests are grouped by how often they're done.

### Daily QA (done every treatment day)

- **Output constancy** — the dose delivered matches the expected value, typically within about **±3%**.
- **Beam symmetry and flatness** — the beam is even and centered.
- **Lasers** — the room positioning lasers point at the correct isocenter.
- **Door and audiovisual interlocks** — confirmed working before patients are treated.

### Monthly QA

More detailed checks of output, energy, field-size accuracy, MLC positioning, and mechanical alignment.

### Annual QA

The most thorough review — absolute dose calibration, full mechanical and dosimetric characterization, and imaging-system verification.

> **Key Point:** **Tolerances tighten with technique.** Conventional treatments allow looser margins; **IMRT** (intensity-modulated radiation therapy) and especially **SRS/SBRT** (stereotactic radiosurgery / body radiotherapy) demand much tighter ones, because tiny errors matter more when small, high-dose fields sit next to critical structures.

---

## Imaging-System QA (AAPM TG-179)

Modern treatment relies on **image-guided radiation therapy (IGRT)** — using on-board imaging like **kV** (kilovoltage) planar images or **CBCT** (cone-beam CT) to verify the patient's position right before treatment. **AAPM TG-179** covers QA for these systems [4].

The single most important check: the **imaging isocenter must agree with the treatment isocenter within about 1 mm**. If the picture you align to is even slightly offset from where the beam actually goes, you would shift the patient to the wrong place — a precise image in the wrong spot is worse than no image.

Image-quality metrics are also tracked, including:

- **HU / CT-number linearity** — Hounsfield Units (the CT density scale) read correctly across materials.
- **Spatial resolution / MTF** — the **modulation transfer function** describes how well fine detail is preserved; it tells you the smallest features the system can resolve.

> **Key Point:** Imaging-to-treatment isocenter agreement within **~1 mm (TG-179)** is the headline imaging-QA number. Geometry first; image quality second.

---

## CT-Simulator QA (AAPM TG-66)

The **CT simulator** is the CT scanner used to plan treatment — it captures the patient's anatomy in the treatment position and defines the coordinate system the whole plan is built on. **AAPM TG-66** specifies its QA [5].

Critical CT-sim checks:

- **Laser and geometry accuracy** — the external positioning lasers and the scan geometry must be precise, because they set the patient's reference marks (tattoos) and the planning origin.
- **CT-number (HU) calibration** — the scanner must read **water = 0 HU** and **air = −1000 HU**. These two anchor points keep the density scale honest, which matters because the planning system converts HU into the electron densities used for dose calculation.

If the CT simulator's geometry or HU calibration drifts, **every plan built from it inherits the error** — which is why TG-66 treats the simulator as a foundation that must be verified, not assumed.

---

## Chapter summary

Radiation protection is a system of layers. **ALARA** sets the mindset; **time, distance, and shielding** are the levers, with distance amplified by the **inverse-square law**. The **NRC's 10 CFR 20** limits — 50 mSv/yr occupational, 1 mSv/yr public, 5 mSv to the embryo/fetus, 10 mSv × age cumulative — define the legal ceilings, and **NCRP-151** shielding (primary vs. secondary barriers, sized by **W, U, T**) keeps everyone beneath them. **Dosimeters** record what slips through. Finally, the machines themselves are kept honest by **interlocks** and a tiered QA program — **TG-142** for the linac, **TG-179** for imaging, **TG-66** for the CT simulator. Master these and you can answer most protection-and-equipment questions on sight.

---

## Check yourself

**1. You are standing 1 meter from a small radioactive source. If you step back to 2 meters, how does your dose rate change?**
*It drops to one-quarter. By the inverse-square law, doubling the distance (2²) reduces intensity by a factor of four — not by half.*

**2. What are the NRC annual dose limits for an occupational whole-body worker and for a member of the public?**
*Occupational whole-body is 50 mSv/year (5 rem). The public limit is 1 mSv/year (100 mrem) — fifty times stricter.*

**3. What is the dose limit to the embryo/fetus of a declared-pregnant worker, and over what period?**
*5 mSv (0.5 rem) over the entire gestation, with an effort to keep it roughly uniform at about 0.5 mSv per month.*

**4. A vault wall faces the direct treatment beam. Is it a primary or secondary barrier, and which NCRP-151 factor accounts for how often the beam points at it?**
*It is a primary barrier (it intercepts the useful beam). The use factor U accounts for the fraction of the workload aimed at that specific barrier.*

**5. Which dosimeters are reusable, and which leaves a permanent physical record?**
*TLD and OSL are reusable. The film badge is single-use but provides a permanent physical record.*

**6. Per TG-179, how closely must the imaging isocenter match the treatment isocenter, and why does it matter?**
*Within about 1 mm. If the image you align the patient to is offset from where the beam actually delivers, you would position the patient incorrectly despite a "good" image.*

---

## Chapter references

1. U.S. Nuclear Regulatory Commission. *Standards for Protection Against Radiation.* 10 CFR Part 20. Washington, DC: NRC. [1]
2. National Council on Radiation Protection and Measurements. *Structural Shielding Design and Evaluation for Megavoltage X- and Gamma-Ray Radiotherapy Facilities.* NCRP Report No. 151. Bethesda, MD: NCRP; 2005. [2]
3. Klein EE, Hanley J, Bayouth J, et al. *Task Group 142 Report: Quality Assurance of Medical Accelerators.* Med Phys. 2009;36(9):4197–4212 (AAPM TG-142). [3]
4. Bissonnette JP, Balter PA, Dong L, et al. *Quality Assurance for Image-Guided Radiation Therapy Utilizing CT-Based Technologies.* Med Phys. 2012;39(4):1946–1963 (AAPM TG-179). [4]
5. Mutic S, Palta JR, Butker EK, et al. *Quality Assurance for Computed-Tomography Simulators and the Computed-Tomography-Simulation Process.* Med Phys. 2003;30(10):2762–2792 (AAPM TG-66). [5]
6. Centers for Disease Control and Prevention. *ALARA — As Low As Reasonably Achievable.* Radiation and Your Health. Atlanta, GA: CDC. [6]
7. Khan FM, Gibbons JP. *Khan's The Physics of Radiation Therapy.* Philadelphia, PA: Wolters Kluwer. [7]

*This chapter is an independent educational text with original explanations. It is not affiliated with the ARRT, and its contents are not actual ARRT examination items.*
