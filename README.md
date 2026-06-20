# my-first-project

An interactive **RT Image Matching Trainer** for radiation therapy students — practice aligning treatment-setup imaging to reference data, just like a real treatment setup.

## ▶ Launch the trainer

### **https://cju11199.github.io/my-first-project/**

Open it in any browser — no install or account needed. Share that link with students.

On launch, pick a workflow from the start screen:

- **2D / 2D** — orthogonal-pair (AP + Lateral) portal-to-DRR matching.
- **CBCT** — cone-beam CT volumetric registration in three planes (axial, coronal, sagittal) with 6DOF couch correction, real 3D CT volumes (MPR reslice), fusion color, windowing, a 3D volume view, and structure contours.

## Cases

**2D / 2D:** Brain · Pelvis · Thorax (CT DRR) · Breast L (SCV + medial-tangent field match, Varian-style). **CBCT:** Pelvis · Acoustic neuroma (vestibular schwannoma IAC SRS) · Breast (real 3D CT, MPR reslice with contours). Switch between them with the dropdown in the top-left.

## Features

- **2D / 2D:** dual-view alignment (AP/PA + Lateral) with 5DOF correction (Lat / Lng / Vrt / Roll / Pitch), plus **Color Wash**, **Spyglass**, and **Contrast** tools
- **CBCT:** three-plane fusion with full 6DOF correction (Lat / Lng / Vrt / Pitch / Roll / Yaw); each plane reveals two translations and one rotation, and **Fusion Color** shows CT in teal vs CBCT in orange
- Blend sliders, isocenter reticle, and live residual-error readout graded against tolerance
- Drag to translate/rotate, **Ctrl+Z** to undo, **New Offset** to generate a fresh setup error
- Press **How to use** in either workflow for the full list of keyboard shortcuts

## Development

The whole app is a single self-contained `index.html` (images embedded), so it runs anywhere.

```bash
git clone https://github.com/cju11199/my-first-project.git
```

Changes pushed to `main` redeploy automatically to the link above.
