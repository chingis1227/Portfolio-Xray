# Portfolio MRI Frontend Prototype

Clean Next.js/React prototype for Portfolio MRI as an institutional Investment Decision Room.

## Scope boundaries

- No Python analytics engine changes.
- No backend logic changes.
- No API routes yet.
- No live backend connection yet.
- Raw Stitch HTML/CSS/JS is not integrated.
- Imported Stitch screenshots and design tokens are used only as visual reference.

## Architecture

- `app/` contains seven route screens plus root redirect.
- `components/layout/` contains the application shell, sidebar, top journey progress, and page header.
- `components/ui/` contains reusable card, metric, badge, and hero primitives.
- `components/portfolio/`, `diagnosis/`, `evidence/`, `hypothesis/`, `comparison/`, `verdict/`, and `report/` contain product-stage components.
- `data/demo/` contains local static JSON used by pages during prototype phase.
- `lib/` contains shared journey metadata and TypeScript types.
- `styles/` contains global Tailwind and Portfolio MRI CSS variables.

## Portfolio Input validation

- Investor currency is required.
- Every visible portfolio row must use a selected instrument from the local instrument list and a weight greater than 0.
- At least 2 valid rows are required before diagnosis.
- Portfolio weights must add up to 100%, with a 0.01 tolerance for rounding.
- Weights are never auto-normalized or silently corrected; the diagnosis CTA remains disabled until blocking validation passes.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Optional checks:

```bash
npm run typecheck
npm run build
```
