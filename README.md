# my-first-project

An interactive **RT Image Matching Trainer** for radiation therapy students — practice aligning orthogonal portal images to reference DRRs, just like a real treatment setup.

## ▶ Launch the trainer

### **https://cju11199.github.io/my-first-project/**

Open it in any browser — no install or account needed. Share that link with students.

## Cases

- **Spine · CT DRR**
- **Brain · AP + Lateral**
- **Pelvis · CT DRR**

Switch between them with the dropdown in the top-left.

## Features

- Dual-view alignment (AP/PA + Lateral) with 6DOF correction (Lat / Lng / Vrt / Roll / Pitch)
- **Color Wash**, **Spyglass**, and **Contrast** matching tools
- Blend sliders, cm tick-mark crosshair on the isocenter, and live residual-error readout
- Drag to translate/rotate, scroll to zoom, **Ctrl+Z** to undo, **New Offset** to generate a fresh case
- Press **How to use** in the app for the full list of keyboard shortcuts

## Development

The whole app is a single self-contained `index.html` (images embedded), so it runs anywhere.

```bash
git clone https://github.com/cju11199/my-first-project.git
```

Changes pushed to `main` redeploy automatically to the link above.
