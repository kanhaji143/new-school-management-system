# Frontend — Next.js + TypeScript

Part of the Smart School & College Management Automation System.

## Stack

- Next.js (App Router) · React 19 · TypeScript
- Tailwind CSS + shadcn/ui
- React Query (server state) · Zustand (auth/session)
- React Hook Form + Zod (validation)
- Axios (API client with silent token refresh)

## Layout

```
src/
├── app/
│   ├── (auth)/            login, register (public)
│   ├── (dashboard)/       protected shell — all admin/teacher modules
│   └── (parent)/          parent portal
├── components/
│   ├── layout/            AppShell, Sidebar, Header, PageHeader
│   └── ui/                shadcn/ui primitives
├── hooks/                 React Query data hooks
├── lib/                   api client, auth helpers, utils
├── providers/             QueryClient provider
├── store/                 Zustand auth store (persisted)
└── types/                 shared TS interfaces
```

## Run

```bash
cp .env.local.example .env.local
npm install
npm run dev          # http://localhost:3000
```

## Conventions

- Feature data fetching goes in `hooks/` using React Query.
- Route protection happens in the layout (hydration-safe) + middleware + the DRF backend.
- Auth tokens are persisted by Zustand; `lib/api.ts` refreshes on 401.
- Never store sensitive data in localStorage beyond the tokens the auth store needs.

## Scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm run start` | Run the production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
