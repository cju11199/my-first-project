# Procedures — Prescription & Dose Calculation

_Original practice questions for ARRT Radiation Therapy registry review. Not actual exam items; not affiliated with the ARRT._

## Dose Specification & ICRU Reference Point

### DOS-01 · _recall_
According to ICRU Reports 50/62, where should the dose be specified for a photon plan reported at a single reference point?

- **A.** At the point of maximum dose (dmax) anywhere in the patient
- **B.** At a clinically relevant point near the center of the PTV, ideally at or near the beam intersection (isocenter)
- **C.** At the surface entry point of each beam
- **D.** At the point of minimum dose within the GTV

**Answer:** B
**Explanation:** The ICRU reference point should be clinically representative, typically at the center of the PTV and where dose can be accurately determined — usually the isocenter for an isocentric technique.
**Source:** ICRU 50/62; Khan

### DOS-02 · _recall_
On a single dose-volume histogram (DVH), what does a steep, nearly vertical curve for the PTV indicate?

- **A.** Poor target coverage
- **B.** Excessive dose to an organ at risk
- **C.** A highly homogeneous dose across the target volume
- **D.** A geometric miss of the target

**Answer:** C
**Explanation:** A cumulative DVH that drops sharply over a narrow dose range means nearly all of the volume receives a similar dose — i.e., a homogeneous target distribution.
**Source:** Khan

### DOS-03 · _application_
A PTV plan reports a maximum dose of 105% and a minimum dose of 95% of the prescription. Using the simple homogeneity index HI = D_max/D_min, what is the HI and how should it be interpreted?

- **A.** HI = 1.105; lower is better, so this is poor
- **B.** HI ≈ 1.11; higher is better, so this is excellent
- **C.** HI ≈ 1.11; a value close to 1.0 is ideal, so this plan is acceptably homogeneous
- **D.** HI = 0.90; values below 1.0 indicate cold spots

**Answer:** C
**Explanation:** HI = 1.05/0.95 ≈ 1.11; the index approaches 1.0 for perfect homogeneity, so a value near 1.1 reflects an acceptably uniform target dose.
**Source:** ICRU 83; Khan

### DOS-04 · _application_
A conformity index (CI) is defined as the volume receiving the prescription dose divided by the target volume. A plan has a prescription isodose volume of 120 cc and a PTV of 100 cc. What is the CI, and what does it imply?

- **A.** CI = 0.83; the target is under-covered
- **B.** CI = 1.2; the plan perfectly conforms with no spill
- **C.** CI = 100; conformity cannot be assessed
- **D.** CI = 1.2; some normal tissue outside the PTV receives the prescription dose

**Answer:** D
**Explanation:** CI = 120/100 = 1.2; a value above 1.0 means the prescription isodose extends beyond the target, indicating normal-tissue spill.
**Source:** ICRU 83; Khan

### DOS-05 · _recall_
The "hot spot" reported in a treatment plan should generally be evaluated when it is at least what size to be clinically meaningful?

- **A.** A single voxel of any value
- **B.** A volume of at least about 2 cm³ (≈15 mm diameter)
- **C.** Only when it exceeds 200% of prescription
- **D.** Only inside the GTV

**Answer:** B
**Explanation:** ICRU guidance treats a hot spot as significant only when it occupies a minimum volume on the order of 2 cm³ (≈15 mm), rather than an isolated calculation voxel.
**Source:** ICRU 50/62

## Beam Energy & Depth-Dose Selection

### DOS-06 · _recall_
For a deep-seated pelvic tumor, why is a higher-energy photon beam (e.g., 15–18 MV) often preferred over 6 MV?

- **A.** Higher energy has a shallower dmax and less skin sparing
- **B.** Higher energy has greater percent depth dose at depth and deeper dmax (skin sparing)
- **C.** Higher energy produces more surface dose
- **D.** Higher energy has a steeper falloff before the target

**Answer:** B
**Explanation:** As photon energy increases, dmax moves deeper and PDD at depth rises, delivering more dose to deep targets while sparing skin.
**Source:** Khan

### DOS-07 · _recall_
For electron beams, the dose is normalized (100%) at which depth?

- **A.** The surface
- **B.** R50
- **C.** The practical range Rp
- **D.** The depth of maximum dose (dmax)

**Answer:** D
**Explanation:** Electron PDD curves, like photon curves, are normalized to 100% at dmax; electrons then fall off rapidly beyond the therapeutic range.
**Source:** AAPM TG-71

### DOS-08 · _application_
A clinician wants the 90% isodose to cover a lesion at 4.5 cm depth with an electron beam. Using the rule of thumb R90 ≈ E/3.2 (cm, with E in MeV), which nominal energy is the best choice?

- **A.** 9 MeV
- **B.** 12 MeV
- **C.** 6 MeV
- **D.** 15 MeV

**Answer:** D
**Explanation:** R90 ≈ E/3.2, so to reach 4.5 cm, E ≈ 4.5 × 3.2 ≈ 14.4 MeV; 15 MeV is the closest practical choice that places the 90% line at the required depth.
**Source:** AAPM TG-71; Khan

### DOS-09 · _calculation_
Using Rp ≈ E/2 (cm), what is the approximate practical range of a 12 MeV electron beam in water?

- **A.** 3.75 cm
- **B.** 4 cm
- **C.** 6 cm
- **D.** 12 cm

**Answer:** C
**Explanation:** Rp ≈ E/2 = 12/2 = 6 cm; this is the depth where the extrapolated falloff meets the bremsstrahlung tail.
**Source:** AAPM TG-71

### DOS-10 · _application_
A surface lesion overlies critical structures at 5 cm depth that must be spared. Which electron energy minimizes deep dose while still treating a 1.5 cm thick target to the 90% line?

- **A.** 6 MeV (R90 ≈ 1.9 cm)
- **B.** 16 MeV (R90 ≈ 5 cm)
- **C.** 20 MeV
- **D.** 12 MeV (R90 ≈ 3.75 cm)

**Answer:** A
**Explanation:** R90 ≈ E/3.2; 6 MeV gives R90 ≈ 1.9 cm, covering a 1.5 cm target while sparing the structure at 5 cm, since higher energies push the practical range past the critical depth.
**Source:** AAPM TG-71; Khan

## Field Size & Equivalent Square

### DOS-11 · _calculation_
What is the equivalent square of a 10 × 6 cm rectangular field using the formula 2ab/(a+b)?

- **A.** 8.0 cm
- **B.** 6.0 cm
- **C.** 16 cm
- **D.** 7.5 cm

**Answer:** D
**Explanation:** 2ab/(a+b) = 2(10)(6)/(10+6) = 120/16 = 7.5 cm.
**Source:** Khan

### DOS-12 · _calculation_
Using the area/perimeter relationship (equivalent square = 4 × Area/Perimeter), find the equivalent square of a 20 × 5 cm field.

- **A.** 8.0 cm
- **B.** 10 cm
- **C.** 12.5 cm
- **D.** 4.0 cm

**Answer:** A
**Explanation:** 4 × (20×5)/(2×(20+5)) = 4 × 100/50 = 8.0 cm; equivalently 2(20)(5)/25 = 200/25 = 8.0 cm.
**Source:** Khan

### DOS-13 · _calculation_
What is the equivalent square of a 15 × 15 cm field?

- **A.** 11.25 cm
- **B.** 30 cm
- **C.** 7.5 cm
- **D.** 15 cm

**Answer:** D
**Explanation:** For any square field a×a, 2a²/(2a) = a, so the equivalent square equals 15 cm.
**Source:** Khan

### DOS-14 · _application_
Why is the equivalent square useful when looking up output factors and depth-dose data?

- **A.** It converts SSD setups to SAD setups
- **B.** It accounts for wedge transmission
- **C.** Tabulated dosimetry data are indexed by square field size, so a rectangular field must be reduced to its dosimetric equivalent
- **D.** It corrects for tissue inhomogeneity

**Answer:** C
**Explanation:** PDD, TMR, Sc, and Sp tables are organized by square field size, so a rectangular field is converted to its equivalent square to read the correct scatter and depth-dose values.
**Source:** Khan

### DOS-15 · _calculation_
A 25 × 10 cm field is set. What is its equivalent square?

- **A.** 17.5 cm
- **B.** 14.3 cm
- **C.** 12.5 cm
- **D.** 35 cm

**Answer:** B
**Explanation:** 2ab/(a+b) = 2(25)(10)/35 = 500/35 ≈ 14.3 cm.
**Source:** Khan

## Depth-Dose Functions & Inverse Square

### DOS-16 · _recall_
Which depth-dose quantity is essentially independent of source-to-surface distance and is used for SAD/isocentric calculations?

- **A.** Percent depth dose (PDD)
- **B.** Backscatter factor
- **C.** Tissue-maximum ratio (TMR)
- **D.** Mayneord F factor

**Answer:** C
**Explanation:** TMR (and TPR) are defined at a fixed distance to the point of measurement and are independent of SSD, making them appropriate for isocentric setups.
**Source:** Khan

### DOS-17 · _recall_
Percent depth dose is defined as which ratio (× 100)?

- **A.** Dose at depth ÷ dose at dmax
- **B.** Dose at dmax ÷ dose at depth
- **C.** Dose in air ÷ dose in phantom
- **D.** Dose at isocenter ÷ dose at surface

**Answer:** A
**Explanation:** PDD = (dose at depth ÷ dose at dmax) × 100, both measured along the central axis at a fixed SSD.
**Source:** Khan

### DOS-18 · _calculation_
A point receives 100 cGy at 80 cm from the source. Ignoring attenuation, what dose is delivered at 100 cm using the inverse-square law?

- **A.** 80 cGy
- **B.** 125 cGy
- **C.** 156 cGy
- **D.** 64 cGy

**Answer:** D
**Explanation:** D2 = D1 × (d1/d2)² = 100 × (80/100)² = 100 × 0.64 = 64 cGy.
**Source:** Khan

### DOS-19 · _calculation_
A point dose is 150 cGy at 100 cm. What is the dose at 120 cm by inverse square (attenuation ignored)?

- **A.** 125 cGy
- **B.** 216 cGy
- **C.** 104 cGy
- **D.** 180 cGy

**Answer:** C
**Explanation:** D2 = 150 × (100/120)² = 150 × 0.694 ≈ 104 cGy.
**Source:** Khan

### DOS-20 · _calculation_
Given a PDD of 75% at 10 cm depth for a field, and a dmax dose of 200 cGy, what is the dose delivered at 10 cm?

- **A.** 150 cGy
- **B.** 267 cGy
- **C.** 75 cGy
- **D.** 125 cGy

**Answer:** A
**Explanation:** Dose at depth = dmax dose × PDD/100 = 200 × 0.75 = 150 cGy.
**Source:** Khan

### DOS-21 · _calculation_
A prescription calls for 180 cGy at 8 cm depth where the PDD is 72%. What dose must be delivered at dmax?

- **A.** 130 cGy
- **B.** 250 cGy
- **C.** 200 cGy
- **D.** 252 cGy

**Answer:** B
**Explanation:** Dmax dose = dose at depth ÷ (PDD/100) = 180 ÷ 0.72 = 250 cGy.
**Source:** Khan

### DOS-22 · _recall_
Which quantity is the historical predecessor of TMR, defined as the ratio of dose at depth in phantom to dose at the same point in free space?

- **A.** Scatter-air ratio
- **B.** Tissue-phantom ratio
- **C.** Collimator scatter factor
- **D.** Tissue-air ratio (TAR)

**Answer:** D
**Explanation:** TAR (tissue-air ratio) is the older function relating in-phantom dose to in-air dose; TMR was developed to extend the concept to high-energy beams.
**Source:** Khan

## MU Calculations — SSD & SAD

### DOS-23 · _recall_
For an SSD (fixed-distance) setup, the monitor-unit equation uses which depth-dose function?

- **A.** TMR
- **B.** PDD
- **C.** TPR
- **D.** TAR

**Answer:** B
**Explanation:** SSD calculations are normalized at dmax at a fixed SSD, so PDD/100 carries the dose to depth; SAD setups use TMR/TPR instead.
**Source:** Khan; AAPM TG-71

### DOS-24 · _recall_
In the SAD MU equation MU = Dose / (D0 × TMR × Sc × Sp × WF × TF), what does Sc represent?

- **A.** Phantom (patient) scatter factor measured in a phantom
- **B.** Wedge transmission factor
- **C.** Tray transmission factor
- **D.** Collimator (head) scatter factor measured in air

**Answer:** D
**Explanation:** Sc is the collimator/head scatter factor measured in air with a buildup cap, whereas Sp is the phantom scatter factor; Scp = Sc × Sp.
**Source:** AAPM TG-71

### DOS-25 · _calculation_
Compute the MU for an SAD treatment: deliver 200 cGy with TMR = 0.85, Sc = Sp = WF = TF = 1.0, and calibration D0 = 1.0 cGy/MU at the reference point.

- **A.** 170 MU
- **B.** 235 MU
- **C.** 200 MU
- **D.** 256 MU

**Answer:** B
**Explanation:** MU = 200 / (1.0 × 0.85 × 1 × 1 × 1 × 1) = 235 MU.
**Source:** AAPM TG-71

### DOS-26 · _calculation_
Take the previous SAD plan (200 cGy, TMR 0.85, D0 1.0, other factors 1.0) and add a physical wedge with WF = 0.70. What is the new MU?

- **A.** 336 MU
- **B.** 235 MU
- **C.** 165 MU
- **D.** 280 MU

**Answer:** A
**Explanation:** MU = 200 / (1.0 × 0.85 × 0.70) = 200/0.595 ≈ 336 MU; the wedge lowers dose per MU, so MUs rise.
**Source:** AAPM TG-71

### DOS-27 · _calculation_
An SSD field must deliver 150 cGy at depth where PDD = 80%. With Sc = Sp = 1.0, D0 = 1.0 cGy/MU at dmax, and no wedge or tray, what is the MU?

- **A.** 120 MU
- **B.** 150 MU
- **C.** 200 MU
- **D.** 188 MU

**Answer:** D
**Explanation:** MU = Dose / (D0 × PDD/100 × Sc × Sp) = 150 / (1.0 × 0.80) = 187.5 ≈ 188 MU.
**Source:** AAPM TG-71

### DOS-28 · _calculation_
An SSD field needs 200 cGy at depth, PDD = 65%, Sc = Sp = 1.0, D0 = 1.0 cGy/MU, with a blocking tray TF = 0.96. What is the MU?

- **A.** 308 MU
- **B.** 295 MU
- **C.** 320 MU
- **D.** 130 MU

**Answer:** C
**Explanation:** MU = 200 / (1.0 × 0.65 × 0.96) = 200/0.624 ≈ 320 MU; the tray attenuates the beam, raising MU.
**Source:** AAPM TG-71

### DOS-29 · _calculation_
For an SAD plan: 250 cGy, TMR = 0.90, Sc = 1.01, Sp = 0.99, WF = 1.0, TF = 1.0, D0 = 1.0 cGy/MU. What is the MU (to the nearest whole)?

- **A.** 250 MU
- **B.** 278 MU
- **C.** 225 MU
- **D.** 309 MU

**Answer:** B
**Explanation:** Scp = 1.01 × 0.99 ≈ 1.0; MU = 250 / (1.0 × 0.90 × 1.0) = 277.8 ≈ 278 MU.
**Source:** AAPM TG-71

### DOS-30 · _application_
A student computes an MU and accidentally divides by the wedge factor (0.6) twice instead of once. What error results?

- **A.** The MU is too high and the patient is overdosed
- **B.** The MU is too low and the patient is underdosed
- **C.** No effect, since the wedge factor cancels
- **D.** Only the depth dose is affected

**Answer:** A
**Explanation:** Dividing by 0.6 twice inflates the MU (× 1/0.36 instead of × 1/0.6), so too many MU are delivered and the patient is overdosed.
**Source:** AAPM TG-71

### DOS-31 · _application_
Two MU calculations for the same prescription give 250 MU (no wedge) and 357 MU (wedge, WF = 0.70). Why is the wedged value higher?

- **A.** The wedge transmits less than 100% of the beam, lowering dose per MU, so more MU are needed
- **B.** The wedge increases dose per MU
- **C.** The wedge changes the prescription depth
- **D.** The wedge increases the field size

**Answer:** A
**Explanation:** A wedge factor < 1 means the wedge attenuates the beam, reducing cGy/MU; MU = 250/0.70 ≈ 357, so more MU compensate.
**Source:** AAPM TG-71; Khan

### DOS-32 · _recall_
Compared with a physical wedge, a dynamic (virtual) wedge produced by moving a collimator jaw during the beam:

- **A.** Has a fixed wedge factor close to 0.3 regardless of field size
- **B.** Hardens the beam more than a physical wedge
- **C.** Cannot be used for breast tangents
- **D.** Generally has a wedge/effective factor closer to 1.0 and reduces beam hardening and peripheral dose

**Answer:** D
**Explanation:** Dynamic wedges modulate dose with jaw motion rather than an absorber, so they avoid beam hardening and tray-like attenuation and have effective factors nearer 1.0.
**Source:** Khan

### DOS-33 · _recall_
Both the wedge factor and the tray (blocking-tray) factor are:

- **A.** Greater than 1.0, so they lower the required MU
- **B.** Less than 1.0, so they raise the required MU
- **C.** Equal to the inverse-square correction
- **D.** Independent of the beam

**Answer:** B
**Explanation:** Each accessory attenuates the beam (factor < 1.0), reducing cGy/MU; since MU = Dose ÷ (… × WF × TF), a smaller denominator increases MU.
**Source:** AAPM TG-71

## Tissue Inhomogeneity Corrections

### DOS-34 · _recall_
When a photon beam traverses lung tissue, how is the dose beyond the lung affected relative to a unit-density (water) calculation?

- **A.** The dose is reduced because lung absorbs more
- **B.** The dose is increased because the low-density lung attenuates less
- **C.** The dose is unchanged
- **D.** Only the surface dose changes

**Answer:** B
**Explanation:** Low-density lung attenuates the beam less than water, so points distal to the lung receive a higher dose than a homogeneous (water) calculation predicts.
**Source:** AAPM Report 85 (TG-65)

### DOS-35 · _recall_
Which historical inhomogeneity-correction method scales the depth by the radiological (effective) path length to look up TAR/TMR, but ignores the position of the inhomogeneity?

- **A.** Effective-depth (ratio of TARs) method
- **B.** Batho power-law method
- **C.** Convolution/superposition
- **D.** Monte Carlo

**Answer:** A
**Explanation:** The effective-depth method (ratio of TARs) corrects only for the amount of intervening tissue density, not its location relative to the point of calculation.
**Source:** AAPM Report 85 (TG-65)

### DOS-36 · _recall_
Which inhomogeneity-correction approach is considered the most accurate, especially near low-density tissue interfaces where electronic equilibrium is lost?

- **A.** Ratio of TARs
- **B.** Batho power law
- **C.** Manual effective-depth scaling
- **D.** Monte Carlo (and modern convolution/superposition) methods

**Answer:** D
**Explanation:** Monte Carlo and modern convolution/superposition algorithms model secondary electron transport, giving the best accuracy at interfaces where simpler density-scaling methods fail.
**Source:** AAPM Report 85 (TG-65)

### DOS-37 · _application_
A 10 cm geometric path includes 4 cm of lung with relative electron density 0.25. What is the approximate radiological (effective) depth used for inhomogeneity correction?

- **A.** 10 cm
- **B.** 4 cm
- **C.** 7 cm
- **D.** 13 cm

**Answer:** C
**Explanation:** Effective depth = (6 cm soft tissue × 1.0) + (4 cm lung × 0.25) = 6 + 1 = 7 cm.
**Source:** AAPM Report 85 (TG-65)

### DOS-38 · _application_
Why must bony anatomy be considered separately from soft tissue in inhomogeneity corrections?

- **A.** Bone has higher density and attenuates more, reducing transmitted dose while increasing local absorbed dose at the interface
- **B.** Bone has the same density as water
- **C.** Bone is transparent to megavoltage photons
- **D.** Bone only affects electron beams

**Answer:** A
**Explanation:** Higher-density bone attenuates the primary beam more (lowering distal dose) and alters local dose at bone–tissue interfaces, so density scaling matters.
**Source:** AAPM Report 85 (TG-65)

## Field Junctions, Gaps & Plan Setup

### DOS-39 · _calculation_
Two adjacent SSD fields each have a length L = 20 cm at the surface and treat to a depth d = 5 cm at SSD = 100 cm. What total skin gap is required so the fields match at depth (gap = (L/2)(d/SSD) per field, summed)?

- **A.** 0.5 cm
- **B.** 2.0 cm
- **C.** 1.0 cm
- **D.** 0.25 cm

**Answer:** C
**Explanation:** Each field contributes (L/2)(d/SSD) = (10)(5/100) = 0.5 cm; for two fields the total gap = 2 × 0.5 = 1.0 cm.
**Source:** Khan

### DOS-40 · _calculation_
A single field with L = 16 cm is matched to a fixed line at a depth of 8 cm, SSD = 100 cm. What is that field's contribution to the surface gap, (L/2)(d/SSD)?

- **A.** 0.64 cm
- **B.** 0.32 cm
- **C.** 1.28 cm
- **D.** 0.16 cm

**Answer:** A
**Explanation:** (L/2)(d/SSD) = (8)(8/100) = 8 × 0.08 = 0.64 cm.
**Source:** Khan

### DOS-41 · _application_
Why is a calculated skin gap used between abutting photon fields rather than letting the fields meet at the skin surface?

- **A.** To create an intentional hot spot at the surface
- **B.** To reduce the field size at depth
- **C.** Because diverging beam edges would overlap with depth, causing a hot spot, so a surface gap makes the 50% edges meet at the prescribed depth
- **D.** Because the couch blocks the junction

**Answer:** C
**Explanation:** Each beam diverges, so fields touching at the skin overlap deeper; a calculated gap lets the diverging 50% isodose edges meet at the chosen depth, avoiding overdose.
**Source:** Khan

### DOS-42 · _application_
A junction between two fields is moved ("feathered") several times during a course of treatment primarily to:

- **A.** Increase the total dose at the junction
- **B.** Spread any dose inhomogeneity at the match line over a larger area, reducing the impact of a hot or cold spot
- **C.** Eliminate the need for a gap calculation
- **D.** Shorten the overall treatment time

**Answer:** B
**Explanation:** Feathering (shifting the junction) blurs the dose gradient at the match over several positions, so a residual hot/cold spot is not concentrated at one line.
**Source:** Khan

### DOS-43 · _application_
When converting an SSD setup to an SAD/isocentric setup for the same target, which change to the MU calculation is required?

- **A.** Replace PDD/100 with TMR and account for the inverse-square shift of the reference point to the isocenter
- **B.** Continue using PDD with no other change
- **C.** Replace Sc with Sp only
- **D.** Add a wedge factor automatically

**Answer:** A
**Explanation:** Isocentric calculations use TMR (distance-independent) at the isocenter and incorporate inverse-square corrections for the change in reference distance, unlike the fixed-SSD PDD approach.
**Source:** AAPM TG-71; Khan

### DOS-44 · _application_
A breast tangent plan shows a 115% hot spot in the superficial subcutaneous tissue. Which adjustment most directly improves dose homogeneity?

- **A.** Adding wedges or field-in-field segments to compensate for the missing tissue/contour curvature
- **B.** Removing all wedges
- **C.** Increasing the prescription dose
- **D.** Reducing the SSD

**Answer:** A
**Explanation:** Wedges or field-in-field (forward-planned) segments compensate for the sloping breast contour and tissue deficit, flattening the dose and reducing the superficial hot spot.
**Source:** Khan

### DOS-45 · _calculation_
A patient is treated with two equally weighted parallel-opposed fields. One field delivers 100 cGy at the midplane point and the opposed field delivers 100 cGy at the same point. If the prescription to the midplane is 200 cGy/fraction, and the calibration is 1.0 cGy/MU with combined factor product (TMR × Sc × Sp) = 0.80 per field, what is the MU per field?

- **A.** 125 MU
- **B.** 100 MU
- **C.** 160 MU
- **D.** 250 MU

**Answer:** A
**Explanation:** Each field delivers 100 cGy to the midplane; MU = 100 / (1.0 × 0.80) = 125 MU per field.
**Source:** AAPM TG-71

_Educational use only; original practice questions, not affiliated with or endorsed by the ARRT._
