# Data Intelligence Platform — Frontend

Next.js 14 (App Router) frontend for the AI-Powered Data Intelligence Platform.

## Stack

- **Next.js 16** (App Router)
- **React 19**
- **Vanilla CSS** (design tokens from `docs/DESIGN.md`)
- No Tailwind, no component library — all styles are in `src/app/globals.css`

## Pages

| Route | Description |
|---|---|
| `/` | Prompt intake — describe your data need in plain English |
| `/tasks` | All workflow runs with live status (auto-polls on active tasks) |
| `/tasks/[id]` | Live run monitor — step-by-step progress, plan sidebar |
| `/tasks/[id]/results` | Results table with search, filter, source inspector, export |
| `/history` | Completed workflows for re-inspection |

## Running locally

```bash
npm install
npm run dev
# → http://localhost:3000
```

Requires the FastAPI backend running on `http://localhost:8000`.
Set `NEXT_PUBLIC_API_URL` in `.env.local` to override.

## Environment

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Design system

All design tokens (colors, spacing, radius, typography) are in `src/app/globals.css`.
Refer to `docs/DESIGN.md` for the full visual language reference.
Never use ad-hoc hex values — always use the CSS variables.
