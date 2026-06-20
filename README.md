# my-first-project

An interactive **RT Image Matching Trainer** for radiation therapy students — practice aligning treatment-setup imaging to reference data, just like a real treatment setup.

> **Training simulator — educational use only. Not approved for clinical decision-making. All patient offsets and values shown are fictional.**

## ▶ Launch the trainer

### **https://rtimagematch.com**

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

The app is `index.html` (markup, styles, and logic). Large static assets are kept
in separate, cacheable files so the HTML stays small: embedded DRR/CBCT images live
in `image_data.js`, web fonts in `assets/fonts/`, and the 3D volume datasets in the
`*3d_data.js` files (loaded on demand). It's still plain static — no build step.

```bash
git clone https://github.com/cju11199/my-first-project.git
```

The site is hosted on [Vercel](https://vercel.com). Changes pushed to `main`
redeploy automatically to the link above. See [DEPLOY.md](DEPLOY.md) for setup details.

## License

Copyright (c) 2026 Craig Utter. All rights reserved. Unauthorized copying, reuse, or distribution is prohibited. See [LICENSE](LICENSE).
