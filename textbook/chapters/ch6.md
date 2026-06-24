# Chapter 6 — Treatment Volume Localization

## What you'll learn

- How CT simulation captures the patient in the exact position they will be treated in, and why slice thickness, scan range, and contrast matter.
- The difference between a 3D snapshot and a 4D-CT that "watches" the patient breathe.
- How immobilization devices, reference marks, tattoos, and the isocenter turn a plan into a repeatable daily setup.
- The ICRU target volumes — GTV, CTV, ITV, PTV — and exactly what each one adds.
- The main image-guided radiation therapy (IGRT) methods, and how to read an image "match" the way a therapist does at the machine every day.
- What a 6-degrees-of-freedom couch correction means, and when a patient needs to be re-simulated (adaptive radiotherapy).

## Why this matters

Radiation only helps if it lands on the tumor and spares the healthy tissue around it. Everything in this chapter — the simulation scan, the foam cradle, the tiny ink tattoo, the daily image match — exists to put the beam in the same correct place every single day. As a therapist, image matching will be one of your most repeated and most consequential tasks, so we will spend extra time making it clear.

## 1. CT Simulation: Building the Patient's Blueprint

**Simulation** is the planning appointment where we record the patient's anatomy and define the treatment position. Think of it as the architectural survey before a house is built. Nothing about the rest of the treatment course is repeatable unless this first scan is done carefully.

In modern departments, simulation is done on a **CT simulator** — a CT (computed tomography) scanner with a flat couch top that matches the treatment couch, plus a set of **lasers** mounted on the room walls and ceiling. The single most important rule: **scan the patient in the treatment position.** If they will be treated lying on their back with arms over their head, that is exactly how they are scanned. The CT images become the 3D model the dosimetrist plans on, so the model must match reality.

### Slice thickness and scan range

The CT image is built from many thin cross-sectional slices, like a loaf of sliced bread. **Slice thickness** is how thick each slice is.

| Setting | Typical slice thickness | Why |
|---|---|---|
| Stereotactic (SRS/SBRT, very precise small targets) | 1–3 mm | Thinner slices = finer detail and smoother digitally reconstructed images |
| Conventional treatment | 3–5 mm | Good detail with manageable data size |

Thinner slices give more detail but make larger image sets. The **scan range** is how much of the body is imaged — always generous enough to include the target, all the organs at risk nearby, and enough length above and below for the planned beams to enter and exit.

### Contrast and artifacts

**Contrast agents** make certain tissues stand out.

- **IV (intravenous) contrast** brightens blood vessels and many tumors, helping define the target. Note: contrast changes the apparent tissue density the planning system reads, so departments have protocols for handling this.
- **Oral contrast** outlines the stomach and bowel so the bowel can be avoided.

Watch for **artifacts** — errors in the image. **Metal** (hip prostheses, dental fillings) causes **beam-hardening artifacts**: bright and dark streaks that distort the picture and the dose calculation. We plan around these, sometimes with special metal-artifact-reduction settings.

> **Key Point:** The CT simulation scan is the reference everything else is measured against. If the patient is positioned poorly at sim, every treatment day inherits that error.

## 2. 3D vs. 4D-CT: Capturing Motion

A standard CT scan is a **3D** image — a single frozen snapshot. That is fine for anatomy that holds still. But the lungs, liver, and pancreas move as the patient breathes. A snapshot of a moving target is like a photo of a runner: it shows where they were in one instant, not the full path they travel.

**4D-CT** solves this. It adds time as the fourth dimension. The scanner records the breathing pattern (with a belt or an external marker) while it images, then **sorts** the slices by **breathing phase** — full inhale, mid-breath, full exhale, and stages in between. The result is a movie of the anatomy across the breathing cycle.

Why we care: 4D-CT shows the full range a tumor travels during breathing. That range is exactly what we need to build the **internal margin** (the ITV, below) and to design **motion management** strategies like breath-hold or gating.

> **Common mix-up:** 3D-CT is not "lower quality" than 4D-CT — it is simply a still image. 4D-CT is specifically for moving targets and produces much more data, so it is reserved for sites where breathing motion matters.

## 3. Immobilization: Holding the Position

A great simulation is useless if the patient lies differently tomorrow. **Immobilization devices** lock the patient into a reproducible position. They are matched to the body region:

- **Thermoplastic mask** — a mesh sheet softened in warm water, molded to the face/head/neck, then hardened. It clips to the couch and holds the head still. Good masks reproduce position to within roughly **3 mm**.
- **Breast board** — an inclined board with arm and hand grips that raises the arms out of the field and sets a consistent torso angle.
- **Vacuum bag (vac-lok / cradle)** — a bag of foam beads molded around the patient; air is pumped out so it stiffens into a custom cradle. Common for body SBRT and pelvis.
- **Headframe / stereotactic frame** — the most rigid option, historically bolted on for cranial SRS; very small setup error.

There is a direct trade: **the tighter and more reproducible the immobilization, the smaller the setup margin we have to add** around the target. Less wobble means we can safely treat a smaller volume, sparing more healthy tissue. This is why a rigid SRS frame allows millimeter margins while a loose setup forces a bigger, more generous margin.

## 4. Reference Marks, Tattoos, and the Isocenter

Once the patient is positioned and scanned, we mark them so the position can be found again.

- **Reference marks / tattoos** — tiny permanent **India-ink dots** placed at reference points on the skin (often three: one anterior, two lateral). They are aligned to the room lasers and give the therapist a starting point each day. They are deliberately small and permanent so they don't fade and don't bother the patient long-term.

- **The isocenter** is the heart of the whole geometry. It is the single point in space where the rotation axes of the **gantry** (the rotating beam head), the **collimator** (the beam-shaping head), and the **couch** all intersect. Imagine three spinning hoops all threaded through one bead — that bead is the isocenter. The beam can rotate all the way around the patient and always passes through this one point.

We place the isocenter inside or near the target at planning, then mark its location so it can be reproduced. Two things make that possible:

1. The room's **three-plane lasers** (sagittal, coronal, axial) project lines that cross at a fixed point in the room.
2. We **record the isocenter's CT coordinates** relative to the reference tattoos — the measured shift (in cm) from the tattoo point to the true isocenter.

Each treatment day, the therapist lines the tattoos up to the lasers, then applies the recorded shift to drive the couch to the isocenter. After that, imaging fine-tunes it.

> **Key Point:** The isocenter is a point, not a region — the intersection of the gantry, collimator, and couch rotation axes. Lasers reproduce it in the room; recorded CT coordinates tell us where it sits relative to the patient's marks.

## 5. ICRU Target Volumes (Reports 50, 62, and 83)

The **ICRU** (International Commission on Radiation Units and Measurements) defined a standard set of nested volumes so that everyone — physician, dosimetrist, therapist — means the same thing by the same words [1][2][3]. Picture a set of Russian nesting dolls: each volume contains the one before it and adds one specific kind of uncertainty.

| Volume | Stands for | What it adds | Plain-language meaning |
|---|---|---|---|
| **GTV** | Gross Tumor Volume | Nothing — it is the starting point | The tumor we can actually **see or feel** (on imaging or exam). **No margin.** |
| **CTV** | Clinical Target Volume | Margin for **microscopic spread** + elective nodes | GTV plus a rim where disease likely exists but is invisible, plus nearby lymph node regions we treat electively. |
| **ITV** | Internal Target Volume | Margin for **internal motion** | CTV plus the range the target moves with breathing/filling — built from **4D-CT**. |
| **PTV** | Planning Target Volume | Margin for **setup uncertainty** | CTV/ITV plus a buffer for day-to-day positioning error. The volume we actually aim the dose at. |
| **OAR** | Organ At Risk | — | A healthy structure we must protect (cord, lung, rectum). |
| **PRV** | Planning organ at Risk Volume | A safety margin **around the OAR** | The OAR plus a margin, so motion/setup error doesn't accidentally overdose it. |

A few accuracy rules worth memorizing:

- **GTV has no margin.** It is purely what is visible or palpable.
- **If the tumor was surgically removed (resected), the GTV = 0** — there is nothing gross left to see. We still treat a CTV (the tumor bed and at-risk tissue).
- **CTV adds microscopic disease** (the invisible spread) and elective nodes.
- **ITV adds internal motion** only.
- **PTV adds setup uncertainty** only.

### The van Herk margin recipe

How big should the PTV margin be? A common, evidence-based answer is the **van Herk margin recipe** [4], often written:

> margin ≈ 2.5 Σ + 0.7 σ

where **Σ (sigma)** represents **systematic** errors (the same error every day, like a consistent sim or planning offset) and **σ** represents **random** errors (day-to-day variation). Systematic errors are weighted more heavily because they shift every fraction in the same direction. You don't need to compute it by hand for the registry, but understand the idea: **the margin is a calculated cushion, and better immobilization plus daily imaging shrinks it.**

> **Common mix-up:** Students often swap ITV and PTV. Remember the order of the uncertainties: **ITV = motion inside the body; PTV = error in setting the body up.** ITV is about the tumor moving; PTV is about the patient being positioned slightly differently each day.

## 6. Image-Guided Radiation Therapy (IGRT)

Tattoos and lasers get the patient close. **IGRT** — taking an image at the machine and comparing it to the plan — gets them exactly right. This section is the heart of the chapter, so we will go slowly.

### The big idea: matching a moving image to a reference image

Every form of IGRT does the same fundamental thing:

- The **reference image** is from the planning CT — where the anatomy is *supposed* to be. (In our trainer's color scheme, the reference is shown in **orange**.)
- The **moving image** is taken today at the machine — where the anatomy *actually is* right now. (Shown in **blue**.)

The therapist's job is to **slide and rotate the today image until it lines up with the plan image.** When you nudge the images on screen, you are really telling the system how far off the patient is. The system then converts that into a **couch correction** — physically moving the treatment couch so the patient's anatomy sits exactly where the plan expects. Match on screen, then the couch moves the patient to agree with the plan.

Think of it like aligning two printed transparencies on an overhead projector: you shift and twist the top sheet until its lines fall exactly on the bottom sheet's lines. The amount you shifted is your correction.

### What a 6DOF couch correction means

A couch can correct position in up to **six degrees of freedom (6DOF)** — six independent ways to move:

**Three translations (sliding):**

| Axis | Direction | Memory aid |
|---|---|---|
| **Lat** (lateral) | left ↔ right | side to side |
| **Long** (longitudinal) | head ↔ feet | up and down the table |
| **Vert** (vertical) | up ↔ down | raising/lowering the couch |

**Three rotations (tilting/twisting):**

| Rotation | Motion | Everyday image |
|---|---|---|
| **Pitch** | nodding | like nodding "yes" |
| **Roll** | side tilt | like tipping your head toward a shoulder |
| **Yaw** | turning | like shaking "no" |

A couch that only does the three translations is a **3DOF** (or 4DOF, adding yaw) couch. A full **6DOF couch** can also correct the three rotations, which matters most for high-precision cases like cranial SRS and spine SBRT, where a tiny tilt throws the target off.

> **Key Point:** A couch shift is just the real-world result of your on-screen match. You align the today image to the plan image; the couch then moves the patient by exactly that amount so the beam hits the planned spot.

Now the specific modalities.

### 6.1 2D/2D Planar kV Imaging

The machine takes two **planar** (flat, X-ray-style) **kV** (kilovoltage — diagnostic-energy) images at right angles to each other: typically an **AP** (anterior–posterior, front-to-back) view and a **lateral** (side) view. This pair is called an **orthogonal** pair because the two views are 90° apart, like a front photo and a side photo of a building.

Each live image is matched to a **DRR (digitally reconstructed radiograph)** — a synthetic X-ray the planning system creates by ray-tracing through the planning CT. So you are comparing today's real X-ray to a "predicted" X-ray from the plan. You align by either:

- **Bone match** — line up the skeleton (vertebrae, pelvic bones), used when the target tracks with bone.
- **Fiducial match** — line up implanted **fiducial markers** (small gold seeds placed in or near the tumor), used when the target moves relative to bone (e.g., prostate).

The weakness: planar kV images have **poor soft-tissue contrast.** You can see bone and metal seeds well, but the tumor and soft organs are faint or invisible — which is exactly why fiducials are implanted for sites like the prostate.

### 6.2 MV Portal Imaging / EPID

**MV (megavoltage) portal imaging** uses the **treatment beam itself** to make the image, captured by an **EPID (electronic portal imaging device)** — a flat panel behind the patient. Because the treatment beam is so high-energy, the images have **low contrast** (everything looks washed out and gray) and it delivers a little extra dose. It is the **older** method, largely replaced by kV imaging and CBCT, but you should recognize the term: portal imaging = using the MV treatment beam to verify the field.

### 6.3 kV Cone-Beam CT (CBCT)

**CBCT (cone-beam CT)** is the big upgrade. Instead of two flat images, the kV source and detector rotate around the patient to acquire a **full 3D volumetric image** right on the treatment machine [6]. This unlocks two major advantages:

- **Soft-tissue matching** — because it is a true 3D image, you can match on the actual soft-tissue target and nearby organs (prostate, bladder, rectum), not just bone.
- **Full 6DOF correction** — you view the patient in three planes (**axial, coronal, sagittal**) and can correct all three translations and all three rotations.

In a CBCT match you scroll through slices and fuse the planning CT (orange) with today's CBCT (blue), shifting and rotating until soft-tissue landmarks overlap. This is the modern workhorse of IGRT.

> **Common mix-up:** "kV" vs "MV" describes the **energy** of the imaging beam (diagnostic vs treatment). "2D vs CBCT" describes the **dimension** of the image (flat pair vs full volume). A kV beam can make either a 2D planar image or a 3D cone-beam CT.

### 6.4 Implanted Fiducial Markers and Transponders

When the target is invisible on imaging or moves relative to bone, we implant markers:

- **Gold seeds** — small inert gold fiducials placed in the **prostate, pancreas, lung, or liver.** They show up crisply on kV images, giving a reliable target to match even when the surrounding tissue is faint.
- **Electromagnetic transponders (Calypso)** — tiny implanted "beacons" that broadcast their position continuously to an antenna array. This allows **real-time tracking** of the target during treatment with no imaging dose, often described as "GPS for the body."

### 6.5 Surface-Guided RT (SGRT)

**SGRT (surface-guided radiation therapy)** uses **optical cameras** to map the **skin surface** in 3D, comparing it to a reference surface from the plan. Because it uses light, not X-rays, it adds **no extra radiation dose** and can run continuously. Its three main jobs:

1. **Setup** — position the patient by matching the skin surface, often reducing reliance on tattoos.
2. **Intrafraction monitoring** — watch the surface *during* the beam and pause if the patient drifts.
3. **DIBH (deep-inspiration breath-hold)** — coach the patient to hold a deep breath. In left-breast treatment, a deep breath pushes the heart away from the chest wall, sparing it. SGRT shows whether the patient is holding within the correct **gating window**, and the beam only turns on while they are in that window.

## 7. Adaptive Radiotherapy and Re-Simulation

A treatment course runs over many weeks, and the patient's anatomy can change. When it changes enough that the original plan no longer fits, we adapt.

Common triggers:

- **Weight loss** — the mask or immobilization no longer fits snugly; the external contour has shifted.
- **Tumor shrinkage** — a head-and-neck or lung tumor that responds well can shrink away from the planned volume, meaning the plan now treats too much normal tissue (or the OARs have moved into the dose).
- **Organ filling changes** — a fuller or emptier **bladder or rectum** shifts the prostate and changes the dose to nearby organs.

**Adaptive radiotherapy (ART)** means modifying the plan to match the patient's current anatomy. This may be a quick **online adaptation** (re-planning at the machine using today's CBCT) or a full **re-simulation** — bringing the patient back for a new CT sim and a brand-new plan. The principle is simple: the plan should always match the patient in front of you, not the patient from week one.

> **Key Point:** Daily imaging fixes *where the patient is today*. Adaptive radiotherapy fixes the situation where *the patient's anatomy itself has changed* and the original plan no longer fits.

## Check yourself

1. **A patient's lung tumor moves with breathing. Which volume captures that motion, and what imaging is used to build it?**
   *The ITV (Internal Target Volume) captures breathing motion, and it is built from a 4D-CT, which sorts images by breathing phase to show the full range of motion.*

2. **A tumor was completely surgically removed before radiation. What is the GTV, and why?**
   *The GTV is 0 (zero). GTV is only the visible or palpable gross tumor; if it has been resected, there is nothing gross left to outline. A CTV is still treated to cover the tumor bed and microscopic disease.*

3. **Put these in order from innermost to outermost and state what each adds: PTV, GTV, CTV, ITV.**
   *GTV (visible tumor, no margin) → CTV (adds microscopic spread and elective nodes) → ITV (adds internal motion) → PTV (adds setup uncertainty).*

4. **Why are gold fiducial markers implanted in the prostate for 2D/2D kV imaging?**
   *Because planar kV images have poor soft-tissue contrast, the prostate itself is hard to see. The gold seeds are clearly visible, giving a reliable target to match — and they track the prostate's motion, which moves relative to bone.*

5. **In plain terms, what does "matching the moving image to the reference image" produce, and what physically happens next?**
   *The therapist aligns today's at-machine image (moving) to the planning-CT image (reference). The misalignment is converted into a couch correction (shift), and the treatment couch physically moves the patient so their anatomy matches the plan.*

6. **What does a 6DOF couch correct that a 3DOF couch cannot, and when does it matter most?**
   *A 6DOF couch corrects the three rotations — pitch, roll, and yaw — in addition to the three translations (Lat, Long, Vert). It matters most for high-precision cases like cranial SRS and spine SBRT, where a small tilt would miss the target.*

## Chapter references

**Free, full-text sources**

1. IAEA — *Radiation Oncology Physics: A Handbook for Teachers and Students* (free PDF; simulation, treatment planning, target-volume and image-guidance chapters): <https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1196_web.pdf>.
2. AAPM Reports — respiratory motion (TG-76), CBCT/IGRT QA (TG-179), IGRT (TG-104/TG-147), all free: <https://www.aapm.org/pubs/reports/>.

**For deeper reading (library / standards)**

3. ICRU Reports 50, 62, and 83 — the defining documents for GTV/CTV/ITV/PTV/PRV and margins (ICRU; purchase).
4. Washington CM, Leaver DT. *Principles and Practice of Radiation Therapy.* Elsevier — simulation and IGRT chapters.

*This chapter offers original educational explanations. It is not affiliated with or endorsed by the ARRT and does not reproduce actual exam questions.*
