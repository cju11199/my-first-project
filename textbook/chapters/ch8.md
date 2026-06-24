# Chapter 8 — Treatments

## What you'll learn

- The main external-beam techniques (3D-CRT, IMRT, VMAT, SBRT/SRS, TBI, electrons) and when each is used.
- How proton therapy uses the Bragg peak to spare tissue beyond the target.
- The three brachytherapy delivery types, their isotopes, applicators, and dose-specification points.
- How image guidance and record-and-verify systems confirm you are treating the right place, the right way, every day.
- The basics of how a linear accelerator makes its beam and how a daily treatment unfolds.
- Common acute toxicities, how imaging frequency trades off against margin, and how toxicity is graded with CTCAE version 5.

**Why this matters.** Treatment delivery is where the plan meets the patient. As a therapist, you are the last safety check before the beam turns on, and you manage patients through weeks of side effects. Knowing the *why* behind each technique helps you set up accurately, recognize when something is off, and explain care to anxious patients.

## External-beam techniques

External-beam radiation therapy (EBRT) aims radiation at the patient from a machine outside the body, usually a **linear accelerator (linac)**. Over the decades the field has moved from simple boxes of radiation toward beams that wrap tightly around the tumor. Think of it as the difference between spray-painting a wall and using a fine airbrush.

### 3D conformal radiotherapy (3D-CRT)

**3D-CRT** uses a CT scan to build a three-dimensional picture of the tumor and nearby organs, then shapes each beam to match the tumor's outline from that beam's point of view (the "beam's-eye view"). The shaping is done with a **multileaf collimator (MLC)** — a bank of thin metal "leaves" that slide in and out to form a custom aperture, like a stencil made of movable tongue depressors.

In 3D-CRT each beam is uniform in intensity. It conforms the *shape* of the dose but cannot carve out concave notches around critical organs.

### Intensity-modulated radiotherapy (IMRT)

**IMRT** goes one step further: it varies the *intensity* across each beam, not just the outline. By making some parts of a beam stronger and others weaker, IMRT can paint a dose that curves around sensitive structures — for example, wrapping around the spinal cord while still covering a tumor that hugs it.

IMRT is delivered two ways:

- **Step-and-shoot (segmental):** the MLC forms one shape, the beam turns on, then off; the leaves move to the next shape and the beam fires again. The dose is built from a stack of static "snapshots."
- **Sliding-window (dynamic):** the leaves move continuously *while* the beam stays on, sweeping across the field like a window shade. This is usually faster but demands tighter machine quality assurance.

> **Common mix-up:** IMRT vs VMAT. Both modulate intensity. The difference is delivery: traditional IMRT uses a set of fixed gantry angles (the gantry stops at each angle to treat), while VMAT delivers the dose as the gantry rotates continuously around the patient.

### Volumetric-modulated arc therapy (VMAT)

**VMAT** is a form of IMRT delivered during one or more continuous gantry arcs. As the machine sweeps around the patient, three things change at once: the MLC leaves move, the gantry rotation speed varies, and the dose rate (how fast radiation comes out) varies. Because everything happens in a single rotation, VMAT is often much faster than fixed-angle IMRT — a treatment that took 10–15 minutes might finish in 2–3. Less time on the table means less chance for the patient to move.

### Stereotactic radiosurgery and SBRT

**Stereotactic** means using precise coordinates to pinpoint a target. **Stereotactic radiosurgery (SRS)** treats targets in the brain; **stereotactic body radiation therapy (SBRT)**, also called SABR, treats targets in the body (lung, liver, spine).

These techniques share a recipe: a **few fractions** (often 1–5 treatments) delivering a **high dose per fraction**, aimed with **rigid immobilization** and image guidance for roughly **1–2 mm precision** [1]. Because the dose per session is so large, there is little room for error — the margins are tight and the falloff outside the target must be steep. AAPM Task Group 101 lays out the technical and safety requirements for SBRT [1].

> **Key Point:** A *fraction* is a single treatment session. Conventional courses use many small fractions (about 1.8–2 Gy each, sometimes 30–40 of them). SBRT/SRS flips this: very few fractions, each one large. More dose per visit means immobilization and imaging must be near-perfect.

### Total body irradiation (TBI)

**TBI** irradiates the whole body, most often as part of **conditioning** before a bone-marrow or stem-cell transplant. The goal is to wipe out diseased marrow and suppress the immune system so the donor cells can engraft. A **commonly used** scheme is about **12 Gy in roughly 6 fractions** (for example, 2 Gy twice daily over three days), though protocols vary widely.

Because the lungs are sensitive to radiation, **lung shielding** (blocks that reduce dose to the lungs) is a standard part of many TBI techniques to lower the risk of radiation pneumonitis. The ILROG (International Lymphoma Radiation Oncology Group) guidelines describe contemporary TBI practice [6].

### Electron beams

So far we have discussed **photon** (x-ray) beams, which penetrate deeply. **Electron beams** are different: electrons deposit their energy quickly and then stop, making them ideal for **superficial targets** — skin lesions, scars, or the chest wall after mastectomy.

A defining feature of electrons is that the dose is **normalized at d-max**, the depth of maximum dose. Beyond d-max the dose falls off rapidly, which protects deeper tissue. You choose the electron energy (in MeV) based on how deep the target sits: higher energy reaches deeper. A rough clinical rule of thumb is that the practical range in centimeters is about the energy in MeV divided by three.

| Technique | Beam type | Intensity modulated? | Gantry motion | Typical fractionation | Best suited for |
|---|---|---|---|---|---|
| 3D-CRT | Photon | No (shaped only) | Fixed angles | Conventional (many fractions) | Larger or simpler targets |
| IMRT | Photon | Yes | Fixed angles (step-and-shoot or sliding-window) | Conventional | Targets near critical organs |
| VMAT | Photon | Yes | Continuous arc(s) | Conventional | Same as IMRT, but faster delivery |
| SBRT / SRS | Photon | Yes (often) | Arcs or many beams | Few fractions, high dose each | Small, well-defined targets with rigid setup |

*Electrons and TBI are specialized techniques rather than direct alternatives to the photon methods above, so they sit outside this comparison.*

## Particle therapy: protons

**Proton therapy** uses charged particles instead of x-rays, and its key advantage is a physics phenomenon called the **Bragg peak**.

When a proton beam enters tissue, it deposits relatively little dose along the way. Then, at a depth determined by its energy, it dumps most of its energy in a sharp spike — the Bragg peak — and stops. Almost no dose continues past that point. Picture a car that coasts gently down a street and then slams on the brakes at one exact house, with nothing happening beyond it.

A single Bragg peak is very narrow, so to cover a whole tumor the team stacks many peaks of different energies side by side. The result is a **spread-out Bragg peak (SOBP)** — a plateau of uniform dose across the target depth, with **minimal exit dose** beyond it. This sparing of tissue *behind* the tumor is why protons are attractive for children and for tumors near critical structures.

> **Key Point:** The headline benefit of protons is not a higher tumor dose — it is the near-absence of exit dose past the target, thanks to the Bragg peak.

## Brachytherapy

**Brachytherapy** (from the Greek *brachy*, "short") places the radioactive source very close to — or inside — the tumor. Because dose falls off steeply with distance, brachytherapy delivers a high dose to the target while sparing nearby tissue.

Sources are classed by how fast they deliver dose: **dose rate**.

| Type | Dose rate | Isotope | Typical use |
|---|---|---|---|
| HDR | High-dose-rate | **Iridium-192** | Stepping-source treatments (gynecologic, breast, etc.) |
| LDR intracavitary | Low-dose-rate | **Cesium-137** | Classic GYN intracavitary inserts |
| Permanent seeds | Low (permanent) | **Iodine-125** | Prostate seed implants left in place |

> **Common mix-up:** HDR vs LDR — and the isotopes. **HDR uses Iridium-192**, a single tiny source on a wire that *steps* through the applicator under computer control, pausing at programmed positions (dwell points) for set times. **LDR intracavitary uses Cesium-137** and delivers dose slowly over hours to days. **Permanent prostate seed implants use Iodine-125**, left in the gland permanently to decay away. Keep these three straight — swapping the isotopes is a classic exam trap.

### Applicators

The source is delivered through an **applicator** matched to the anatomy:

- **Tandem and ovoids (Fletcher-Suit):** a central tube (tandem) placed through the cervical canal into the uterus, plus two side capsules (ovoids) in the vaginal fornices. This is the workhorse for **gynecologic intracavitary** treatment of cervical cancer.
- **Interstitial needles/catheters:** thin needles or catheters placed directly *through* the tissue/tumor (for example, in the breast or prostate) so the source can pass through them.
- **Intraluminal catheters:** a catheter placed inside a body **lumen** (a hollow passage such as the esophagus or a bronchus) so the source can treat the lining from within.

### Dose specification points

Gynecologic brachytherapy historically reports dose at two anatomic landmarks:

- **Point A:** roughly 2 cm up from the cervical os and 2 cm lateral to the tandem — near where the uterine artery crosses the ureter. It approximates the dose to the **target/paracervical tissue**.
- **Point B:** 3 cm lateral to Point A (5 cm from midline). It approximates dose at the **pelvic sidewall**, near the lymph nodes.

**ICRU Report 38** standardized this older point-and-volume reporting for intracavitary GYN brachytherapy, and **ICRU Report 89** updated it for modern image-based (CT/MRI) planning that reports dose to target volumes and organs at risk rather than relying on points alone [4][5].

## Image guidance and verification at delivery

Planning a beautiful dose distribution is useless if the patient is not in the right position. **Image-guided radiation therapy (IGRT)** confirms the target's location *at the machine, on the day*, before the beam goes on.

- **Portal imaging:** an x-ray taken with the treatment beam (or a low-dose kV beam) to check bony anatomy against the plan. Modern systems use an **electronic portal imaging device (EPID)**, a flat-panel detector.
- **Cone-beam CT (CBCT):** the gantry rotates while a kV x-ray source and detector acquire a 3D volume, letting you align soft tissue and bone in three planes — not just a flat shadow.
- **Fiducial or soft-tissue matching:** **fiducials** are small markers (often gold seeds) implanted in or near the tumor; they show up clearly on imaging so you can align to the tumor itself. When good soft-tissue contrast exists (as on CBCT), you may match directly to the organ.

After imaging, the therapist (or therapist and physician, per policy) reviews the match and applies couch shifts to correct any offset before treating.

### Record-and-verify systems

A **record-and-verify (R&V)** system is the safety brain of the treatment room. It holds the approved plan parameters — energy, MLC shapes, gantry and collimator angles, monitor units, couch position — and **compares planned versus delivered** values in real time. If anything falls **outside tolerance**, the system **interlocks** (stops the beam) rather than treating the wrong way. It also records every fraction, building the treatment history.

> **Key Point:** IGRT answers "is the patient in the right place?" R&V answers "is the machine doing exactly what the plan said?" You need both.

## Machine operation basics

### How the linac makes the beam

A linear accelerator builds its beam in stages:

1. An **electron gun** injects electrons into an **accelerating waveguide**.
2. Microwaves (from a magnetron or klystron) accelerate the electrons to nearly the speed of light down the waveguide.
3. For **electron** treatments, that pencil of electrons is spread out (by scattering foils or scanning) and used directly.
4. For **photon (x-ray)** treatments, the electrons slam into a high-density **target**, producing x-rays by *bremsstrahlung* ("braking radiation").
5. A **flattening filter** (in conventional modes) evens out the beam; the **primary and secondary collimators** plus the **MLC** shape it; and **monitor chambers** measure the output in **monitor units (MU)**.

### Beam modifiers

Several devices tailor the beam:

- **Wedges** tilt the dose gradient across the field (physical metal wedges or "virtual" wedges made with moving jaws).
- **Bolus** is tissue-equivalent material laid on the skin to pull dose up to the surface (useful for skin or scar treatments).
- **Blocks/MLC** shape the field and shield normal tissue.
- **Compensators** correct for sloping or irregular body surfaces.

### Daily setup workflow

A typical fraction follows a predictable rhythm:

1. **Identify the patient** with at least two identifiers — this is non-negotiable.
2. **Position and immobilize** using the same devices used at simulation (masks, vac-bags, breast boards).
3. **Align** to skin marks/tattoos and room lasers to the planned isocenter.
4. **Image** (portal, CBCT, or fiducial match) and apply any couch shifts.
5. **Treat**, monitoring the patient by camera and audio, watching the R&V console for interlocks.
6. **Document** the fraction, image approvals, and any patient-reported issues.

## On-treatment management

You will see patients several days a week for weeks, so you are often the first to notice side effects. **Acute toxicities** appear during or shortly after treatment (versus *late* effects that show up months to years later).

Common acute toxicities depend on what is in the beam:

- **Mucositis:** painful inflammation of the mouth/throat lining (head-and-neck treatment).
- **Esophagitis:** painful swallowing from an inflamed esophagus (chest treatment).
- **Dermatitis:** skin reaction ranging from redness to moist peeling, especially in skin folds and high-dose surface areas.
- **Myelosuppression:** drop in blood counts when large volumes of bone marrow are irradiated (broad pelvic/spine fields, TBI). Watch for low white cells (infection risk), low platelets (bleeding), and anemia (fatigue).

### The imaging-versus-margin trade-off

Every plan includes a **PTV (planning target volume) margin** — extra room around the tumor to account for setup uncertainty and motion. There is a trade-off:

- **Image more often** (e.g., daily CBCT) → you catch and correct day-to-day shifts → you can use a **smaller margin** → less normal tissue irradiated, but more imaging dose and time.
- **Image less often** → you must use a **larger margin** to stay safe → more normal tissue in the high-dose region.

> **Key Point:** Frequent image guidance "buys back" margin. Tighter, more accurate setup lets the planner shrink the PTV and spare healthy tissue — one big reason IGRT became standard.

### Supportive care

Good supportive care keeps patients on schedule:

- **Skin:** gentle washing, prescribed moisturizers, avoid friction and sun; topical or dressing care for moist desquamation.
- **Mucositis/esophagitis:** topical/systemic analgesics, "magic mouthwash"-type rinses, soft diet, nutrition support, hydration.
- **Nutrition and weight:** monitor closely in head-and-neck and GI patients; dietitian referral.
- **Monitoring counts:** regular CBCs during marrow-heavy treatment.

### Grading toxicity with CTCAE v5

Clinicians grade side effects with the **Common Terminology Criteria for Adverse Events, version 5 (CTCAE v5)** [7]. It assigns each toxicity a severity grade so the whole team speaks the same language:

| Grade | General meaning |
|---|---|
| 1 | Mild; usually no intervention needed |
| 2 | Moderate; minimal/local intervention; affects some daily activities |
| 3 | Severe but not immediately life-threatening; may need hospitalization |
| 4 | Life-threatening; urgent intervention |
| 5 | Death related to the toxicity |

> **Common mix-up:** CTCAE *grade* describes **severity**, not how soon a toxicity appears. A Grade 3 acute dermatitis and a Grade 3 late fibrosis are both "severe," but one is early and one is late — timing (acute vs late) is a separate idea from grade.

## Check yourself

1. **A patient is scheduled for a single high-dose treatment to a small brain metastasis with a rigid frame. What technique is this, and roughly what precision is expected?**
   *Stereotactic radiosurgery (SRS): one (or very few) high-dose fractions with rigid immobilization and roughly 1–2 mm precision [1].*

2. **What is the practical difference between IMRT and VMAT?**
   *Both modulate beam intensity. Traditional IMRT treats from fixed gantry angles; VMAT delivers the dose during one or more continuous gantry arcs, usually faster.*

3. **Match each brachytherapy type to its isotope: HDR, LDR intracavitary, permanent prostate seeds.**
   *HDR uses Iridium-192; LDR intracavitary uses Cesium-137; permanent prostate seeds use Iodine-125.*

4. **Why do proton beams spare tissue beyond the tumor better than x-rays?**
   *Protons deposit most of their energy at the Bragg peak and then stop, leaving minimal exit dose; stacking peaks of different energies makes a spread-out Bragg peak (SOBP) covering the target.*

5. **A department switches from weekly portal imaging to daily CBCT. How might this affect the PTV margin, and why?**
   *Daily imaging catches and corrects setup variation, so the planner can use a smaller PTV margin, sparing more normal tissue (at the cost of more imaging time and dose).*

6. **What does a record-and-verify system do when a delivered parameter falls outside tolerance?**
   *It interlocks and stops the beam, preventing delivery that does not match the approved plan, and it logs the event.*

## Chapter references

**Free, full-text sources**

1. IAEA — *Radiation Oncology Physics: A Handbook for Teachers and Students* (free PDF; external-beam techniques, brachytherapy, electrons): <https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1196_web.pdf>.
2. AAPM Reports — stereotactic body radiotherapy (TG-101) and related delivery/QA, free: <https://www.aapm.org/pubs/reports/>.
3. NCI — CTCAE v5.0 (Common Terminology Criteria for Adverse Events), free: <https://ctep.cancer.gov/protocoldevelopment/electronic_applications/ctc.htm>.
4. NCI — PDQ treatment summaries (modality selection by site): <https://www.cancer.gov/types>.

**For deeper reading (library / standards)**

5. ICRU Reports 38 and 89 — brachytherapy dose and reporting (ICRU; purchase).
6. Khan FM, Gibbons JP. *The Physics of Radiation Therapy.* Wolters Kluwer; Gunderson & Tepper, *Clinical Radiation Oncology.*

*This chapter offers original educational explanations. It is not affiliated with or endorsed by the ARRT and does not reproduce actual exam questions.*
