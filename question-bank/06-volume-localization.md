# Procedures — Treatment Volume Localization

_Original practice questions for ARRT Radiation Therapy registry review. Not actual exam items; not affiliated with the ARRT._

## CT Simulation & Imaging

### TVL-01 · _recall_
What is the single most important requirement when positioning a patient for CT simulation?

- **A.** The scan is acquired with the thinnest possible slice thickness
- **B.** Oral contrast is administered for every anatomic site
- **C.** The patient is scanned in the exact position to be reproduced at each treatment
- **D.** The arms are always raised above the head

**Answer:** C
**Explanation:** CT simulation must capture the patient in the actual treatment position so that the plan and daily setup are reproducible; immobilization, slice thickness, and contrast are secondary to this principle.
**Source:** Washington & Leaver

### TVL-02 · _recall_
Which slice thickness range is most appropriate for a conventional (non-stereotactic) CT simulation?

- **A.** 3–5 mm
- **B.** 1–3 mm
- **C.** 8–10 mm
- **D.** 10–15 mm

**Answer:** A
**Explanation:** Conventional simulations typically use 3–5 mm slices, while stereotactic/SRS planning uses finer 1–3 mm slices to resolve small targets and improve reconstruction accuracy.
**Source:** Washington & Leaver

### TVL-03 · _application_
A patient is being simulated for intracranial stereotactic radiosurgery of a small lesion. Which scan parameter should the therapist select?

- **A.** 5 mm slices to reduce scan time
- **B.** 1 mm slices to resolve the small target and improve spatial accuracy
- **C.** 10 mm slices because the brain is a stable site
- **D.** Variable slice thickness across the scan range

**Answer:** B
**Explanation:** SRS demands sub-millimeter to ~1 mm slices because the targets are small and high spatial accuracy is required for the steep dose gradients.
**Source:** AAPM TG-179

### TVL-04 · _recall_
Why is IV contrast frequently administered during CT simulation for certain sites?

- **A.** It lowers the imaging dose to the patient
- **B.** It eliminates the need for immobilization
- **C.** It corrects for breathing motion
- **D.** It enhances vascular structures and improves tumor/normal-tissue delineation

**Answer:** D
**Explanation:** IV contrast opacifies vessels and enhances many tumors and nodal regions, improving the visibility used for contouring; it does not affect dose or motion.
**Source:** Washington & Leaver

### TVL-05 · _application_
A simulation CT of a patient with bilateral hip prostheses shows dark and bright streaks radiating across the pelvis, obscuring the prostate. What is the cause, and a reasonable mitigation?

- **A.** Patient motion; sedate the patient
- **B.** Beam-hardening/metal artifact; use metal-artifact reduction and avoid beam entry through the implants
- **C.** Contrast extravasation; stop the IV
- **D.** Incorrect window/level; widen the display window

**Answer:** B
**Explanation:** High-density metal causes beam-hardening and streak artifacts that degrade soft-tissue visualization; MAR reconstruction and choosing beam angles that avoid the prostheses help.
**Source:** Washington & Leaver

### TVL-06 · _application_
When defining the CT scan range for simulation, the therapist should ensure the range:

- **A.** Covers only the GTV to minimize dose
- **B.** Matches the diagnostic CT slice count exactly
- **C.** Extends adequately beyond the target to support oblique/non-coplanar beams and DRR generation
- **D.** Stops at the skin surface of the treated region

**Answer:** C
**Explanation:** The scan range must extend well superior and inferior to the target so beams entering from any angle and DRRs are fully reconstructed; too short a range clips beam paths.
**Source:** Washington & Leaver

## 3D vs 4D-CT & Motion Management

### TVL-07 · _recall_
What does a 4D-CT acquisition add compared with a standard 3D simulation CT?

- **A.** Higher spatial resolution in a single static image
- **B.** Sorting of image data by respiratory phase to capture target motion
- **C.** Automatic contouring of all organs at risk
- **D.** Elimination of the need for a PTV margin

**Answer:** B
**Explanation:** 4D-CT correlates image acquisition with the breathing cycle and sorts data into phase bins, revealing how the target moves so motion can be incorporated into the plan.
**Source:** AAPM TG-76

### TVL-08 · _application_
A lower-lobe lung tumor moves significantly with respiration. Which simulation approach best characterizes this motion for treatment planning?

- **A.** A single fast 3D helical scan
- **B.** A non-contrast 3D scan with thicker slices
- **C.** A planar kV radiograph at end-inspiration
- **D.** A 4D-CT to define the motion envelope across breathing phases

**Answer:** D
**Explanation:** 4D-CT samples the tumor across the respiratory cycle so the full range of motion can be encompassed (e.g., to build an ITV), which a single static scan cannot show.
**Source:** AAPM TG-76

### TVL-09 · _application_
From a 4D-CT dataset, a planner combines the GTV positions across all breathing phases. Which volume is being constructed directly from this motion data?

- **A.** PTV
- **B.** PRV
- **C.** ITV
- **D.** CTV

**Answer:** C
**Explanation:** The internal target volume (ITV) is the CTV plus an internal margin for physiologic motion, and 4D-CT phase data is the standard way to derive it.
**Source:** ICRU Report 62

## Immobilization & Reproducibility

### TVL-10 · _recall_
A thermoplastic mask for head-and-neck immobilization provides setup reproducibility on the order of:

- **A.** ~1 cm
- **B.** ~2 cm
- **C.** ~5 cm
- **D.** ~3 mm

**Answer:** D
**Explanation:** Custom thermoplastic masks typically achieve roughly 3 mm reproducibility, which is why they are standard for head-and-neck and brain treatments.
**Source:** Washington & Leaver

### TVL-11 · _recall_
Which immobilization device is most appropriate for reproducibly positioning a patient receiving left-breast tangential fields with the arm abducted?

- **A.** Breast board with arm support
- **B.** Vacuum-formed body bag
- **C.** Stereotactic headframe
- **D.** Thermoplastic mask

**Answer:** A
**Explanation:** A breast board indexes the torso and supports the raised arm, reproducing the breast/chest-wall position for tangential treatment.
**Source:** Washington & Leaver

### TVL-12 · _application_
A clinic adopts a more rigid immobilization system and adds daily imaging for a treatment site. What is the expected effect on the PTV margin?

- **A.** The margin must increase to be safe
- **B.** The margin is unaffected by immobilization
- **C.** The margin can be reduced because setup uncertainty is smaller
- **D.** The margin is replaced by the GTV

**Answer:** C
**Explanation:** Tighter immobilization and image guidance reduce setup uncertainty, allowing a smaller PTV margin and sparing more normal tissue (the van Herk concept).
**Source:** ICRU Report 83

### TVL-13 · _recall_
Which device is most associated with frame-based intracranial stereotactic radiosurgery?

- **A.** Vacuum bag
- **B.** Invasive/relocatable stereotactic headframe
- **C.** Breast board
- **D.** Knee/ankle sponge

**Answer:** B
**Explanation:** Frame-based SRS uses a rigid stereotactic headframe to provide the high positional accuracy required for single-fraction cranial radiosurgery.
**Source:** AAPM TG-179

### TVL-14 · _application_
A vacuum-locked body cushion ("vac-bag") used for an abdominal SBRT patient has lost firmness and no longer conforms to the patient. The most appropriate action is to:

- **A.** Proceed; the bag shape is not important
- **B.** Switch to a thermoplastic mask
- **C.** Re-evacuate/replace the bag to restore conformance and reproducibility before treatment
- **D.** Remove immobilization entirely to speed setup

**Answer:** C
**Explanation:** A vacuum bag only immobilizes while it holds its molded shape; if it loses vacuum it must be re-formed or replaced to preserve reproducible positioning.
**Source:** Washington & Leaver

## Reference Marks, Lasers & Isocenter

### TVL-15 · _recall_
The treatment isocenter is best defined as the:

- **A.** Geometric center of the GTV
- **B.** Intersection of the gantry, collimator, and couch rotation axes
- **C.** Point where the lasers cross the patient's skin
- **D.** Center of the imaging panel

**Answer:** B
**Explanation:** The machine isocenter is the fixed point where the gantry, collimator, and couch rotational axes intersect; the plan's isocenter is aligned to it at setup.
**Source:** Washington & Leaver

### TVL-16 · _recall_
What is the primary purpose of skin tattoos/reference marks placed at simulation?

- **A.** To define the GTV boundary
- **B.** To provide reproducible external reference points for daily setup alignment to lasers
- **C.** To measure the patient's separation
- **D.** To replace the need for imaging

**Answer:** B
**Explanation:** Tattoos/marks give stable external landmarks that the room lasers are aligned to each day, reproducing the simulation position before any image guidance.
**Source:** Washington & Leaver

### TVL-17 · _application_
At simulation, the localization point marked on the patient is not the planned isocenter. How is the actual treatment isocenter most commonly established at the first setup?

- **A.** Couch shifts (recorded CT coordinates) are applied from the reference marks to the planned isocenter
- **B.** The patient is re-simulated each day
- **C.** The tattoos are moved to the isocenter
- **D.** The gantry is rotated to the target

**Answer:** A
**Explanation:** The plan records the shift from the marked reference point to the isocenter; the therapist applies these Lat/Long/Vert couch shifts to move from the tattoos to the treatment isocenter.
**Source:** Washington & Leaver

### TVL-18 · _recall_
The three room lasers used in CT simulation and at the linac define which planes?

- **A.** Coronal only
- **B.** Oblique planes only
- **C.** Sagittal, coronal, and axial (transverse) reference planes
- **D.** The collimator plane only

**Answer:** C
**Explanation:** A laser system projects sagittal, coronal, and axial reference lines that intersect at a known point, allowing three-plane alignment of the patient.
**Source:** Washington & Leaver

## ICRU Target & Organ Volumes

### TVL-19 · _recall_
According to ICRU definitions, the gross tumor volume (GTV):

- **A.** Includes a margin for microscopic spread
- **B.** Includes setup uncertainty
- **C.** Is the demonstrable/visible/palpable extent of tumor with no added margin
- **D.** Always includes elective nodes

**Answer:** C
**Explanation:** The GTV is the gross, demonstrable disease (imaging/clinical) with no margin; margins for microscopic disease and motion/setup are added at later volumes.
**Source:** ICRU Report 50

### TVL-20 · _application_
A patient has a complete gross-total surgical resection of a tumor and is referred for postoperative radiotherapy. What is the GTV?

- **A.** The pre-operative tumor size
- **B.** The same as the PTV
- **C.** Zero — there is no demonstrable gross disease
- **D.** The surgical scar plus 2 cm

**Answer:** C
**Explanation:** When the gross tumor has been resected there is no visible disease, so GTV = 0; treatment is then directed at the CTV (the tumor bed and at-risk microscopic regions).
**Source:** ICRU Report 50

### TVL-21 · _recall_
The clinical target volume (CTV) is the GTV plus:

- **A.** Subclinical microscopic disease and, when indicated, elective nodal regions
- **B.** Setup uncertainty
- **C.** Internal respiratory motion
- **D.** Organ-at-risk margins

**Answer:** A
**Explanation:** The CTV adds a margin for microscopic spread (and elective nodes) that cannot be imaged; motion and setup are added in later volumes.
**Source:** ICRU Report 50

### TVL-22 · _recall_
Which volume specifically accounts for variations in the size, shape, and position of the CTV due to internal physiologic motion?

- **A.** PTV
- **B.** GTV
- **C.** PRV
- **D.** ITV

**Answer:** D
**Explanation:** The internal target volume (ITV) is the CTV plus an internal margin for physiologic motion such as respiration; it is commonly derived from 4D-CT.
**Source:** ICRU Report 62

### TVL-23 · _recall_
The planning target volume (PTV) adds a margin primarily to account for:

- **A.** Microscopic tumor spread
- **B.** The gross visible tumor
- **C.** Setup uncertainties and geometric variations of beam-to-patient alignment
- **D.** Organ-at-risk tolerance

**Answer:** C
**Explanation:** The PTV is a geometric concept that adds a setup/positioning margin around the CTV (or ITV) to ensure the prescribed dose is actually delivered to the CTV.
**Source:** ICRU Report 50

### TVL-24 · _application_
A planner needs to build, in order, the volumes for a moving thoracic target. Which sequence correctly reflects the added uncertainties?

- **A.** GTV → CTV (microscopic) → ITV (internal motion) → PTV (setup)
- **B.** GTV → PTV → CTV → ITV
- **C.** CTV → GTV → PTV → ITV
- **D.** PTV → ITV → CTV → GTV

**Answer:** A
**Explanation:** Margins are added stepwise: GTV (gross), CTV (microscopic spread), ITV (internal motion), then PTV (setup uncertainty).
**Source:** ICRU Report 62

### TVL-25 · _application_
A student mistakenly adds the respiratory-motion margin to the PTV and the setup margin to the ITV. Which statement corrects this?

- **A.** Both margins belong to the GTV
- **B.** The PTV contains microscopic disease; the ITV contains setup error
- **C.** The CTV contains both motion and setup margins
- **D.** Internal motion defines the ITV; setup uncertainty defines the PTV

**Answer:** D
**Explanation:** Internal physiologic motion expands the CTV into the ITV, while setup/positioning uncertainty expands into the PTV; swapping them is a classic ITV-vs-PTV confusion.
**Source:** ICRU Report 62

### TVL-26 · _recall_
The planning organ-at-risk volume (PRV) is best described as:

- **A.** The gross tumor with no margin
- **B.** The CTV plus elective nodes
- **C.** The OAR with a margin for its motion and setup uncertainty
- **D.** The intersection of machine axes

**Answer:** C
**Explanation:** Just as the PTV protects the CTV geometrically, the PRV expands the organ at risk by a margin so that dose limits remain valid despite motion/setup variation.
**Source:** ICRU Report 62

## IGRT Modalities & 6DOF Correction

### TVL-27 · _recall_
Megavoltage (MV) portal imaging with an EPID is characterized by:

- **A.** Excellent soft-tissue contrast comparable to diagnostic CT
- **B.** Low subject contrast because it uses the high-energy treatment beam
- **C.** Three-dimensional volumetric imaging
- **D.** No radiation dose to the patient

**Answer:** B
**Explanation:** MV portal imaging uses the treatment-energy beam, where photoelectric differences are small, giving poor (low) contrast best suited to bony/field-edge verification.
**Source:** Washington & Leaver

### TVL-28 · _application_
A therapist needs soft-tissue visualization of the prostate (relative to bone) before each fraction. Which IGRT modality is most appropriate?

- **A.** kV cone-beam CT (CBCT)
- **B.** MV portal image
- **C.** Single planar kV radiograph
- **D.** Room lasers only

**Answer:** A
**Explanation:** kV cone-beam CT provides volumetric, soft-tissue imaging so the prostate can be matched directly rather than relying on surrogate bony anatomy.
**Source:** AAPM TG-179

### TVL-29 · _application_
On a daily 2D/2D kV pair, the bony pelvis matches the DRRs but implanted prostate fiducials sit several millimeters off. The therapist should:

- **A.** Accept the bony match and treat
- **B.** Ignore the fiducials as artifact
- **C.** Re-simulate the patient immediately
- **D.** Shift to align the fiducials, since they better represent the prostate target position

**Answer:** D
**Explanation:** The prostate can move relative to bone with bladder/rectal filling, so when fiducials are present the match is made to the seeds (the target surrogate), not to bone.
**Source:** AAPM TG-179

### TVL-30 · _recall_
A "2D vs CBCT" distinction in IGRT refers primarily to differences in:

- **A.** The energy of the imaging beam (kV vs MV)
- **B.** The dimensionality of the image (planar vs volumetric)
- **C.** Whether contrast is used
- **D.** The immobilization device

**Answer:** B
**Explanation:** 2D vs CBCT describes image dimensionality (planar projection vs 3D volume); kV vs MV is the separate axis describing imaging-beam energy.
**Source:** AAPM TG-179

### TVL-31 · _application_
After a daily CBCT, the registration software reports the patient is rotated about the longitudinal (superior–inferior) axis. Which 6DOF couch correction addresses this?

- **A.** Lateral translation
- **B.** Roll
- **C.** Vertical translation
- **D.** Pitch

**Answer:** B
**Explanation:** Roll is the rotation about the longitudinal/superior–inferior axis; a 6DOF couch corrects three translations (Lat/Long/Vert) plus pitch, roll, and yaw.
**Source:** AAPM TG-179

### TVL-32 · _recall_
Which technology enables real-time, continuous tracking of an implanted target during treatment without additional imaging dose?

- **A.** MV portal imaging
- **B.** Electromagnetic transponders (e.g., Calypso beacons)
- **C.** Weekly port films
- **D.** Skin tattoos

**Answer:** B
**Explanation:** Implanted electromagnetic transponders are localized by a non-ionizing field array, allowing continuous real-time target tracking with no added radiation dose.
**Source:** AAPM TG-179

### TVL-33 · _application_
A left-breast patient is treated with deep-inspiration breath-hold to spare the heart, and the team wants markerless, no-dose intrafraction monitoring of the chest position. Which technology fits best?

- **A.** Surface-guided RT (optical surface tracking)
- **B.** kV cone-beam CT every few seconds
- **C.** MV portal imaging
- **D.** Implanted gold fiducials

**Answer:** A
**Explanation:** SGRT uses optical cameras to monitor the body surface in real time without ionizing radiation, making it well suited to DIBH gating and intrafraction motion monitoring.
**Source:** AAPM TG-179

### TVL-34 · _application_
On a 2D/2D kV match for a spine SBRT patient, the vertebral body is the alignment reference. Compared with an MV portal image, the kV pair offers:

- **A.** Worse bony contrast and more dose
- **B.** Volumetric soft-tissue information
- **C.** Better bony/edge contrast at lower imaging dose
- **D.** No need for DRRs

**Answer:** C
**Explanation:** kV imaging exploits the photoelectric effect for higher bony contrast at lower dose than MV portal imaging, which is advantageous for bone-based 2D matching.
**Source:** AAPM TG-179

## Adaptive RT & Re-simulation

### TVL-35 · _application_
During a 7-week head-and-neck course, a patient loses substantial weight and the thermoplastic mask now fits loosely. What is the most appropriate response?

- **A.** Continue with the original plan unchanged
- **B.** Trigger re-evaluation/re-simulation and consider adaptive replanning
- **C.** Tighten the couch restraints only
- **D.** Reduce the prescribed dose

**Answer:** B
**Explanation:** Weight loss and tumor shrinkage change the external contour and internal anatomy, so a loose mask is a classic trigger to re-simulate and adapt the plan to preserve target coverage and OAR sparing.
**Source:** Washington & Leaver

_Educational use only; original practice questions, not affiliated with or endorsed by the ARRT._
