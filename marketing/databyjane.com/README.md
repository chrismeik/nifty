# databyjane.com

One-page landing page for Jane Meik — part-time data help for school districts.
Astro 4, plain scoped CSS, no JS framework. Layout mirrors `marketing/niftyedtools.com`.

Status: **draft skeleton**. All copy marked `PLACEHOLDER` / `TODO(placeholder)` needs real content,
and `public/images/jane-placeholder.svg` needs a real photo.

## Run locally

```bash
cd marketing/databyjane.com/_platform/_astro
npm install
npm run dev      # http://localhost:4323
npm run build    # static output in dist/
```

## Layout

- `_platform/_astro/src/pages/index.astro` — the page; composes the five sections
- `_platform/_astro/src/components/` — `Layout`, `Hero`, `PartTime`, `Problems`, `Experience`, `Contact`
- `_platform/_astro/src/data/problems.ts` — the problem list; Problems and Experience both read it so each experience item maps to one problem
- `_platform/_astro/src/styles/_tokens.css` — color/layout tokens
- `product.json` — product manifest; component ids match the `<product id>` markers in the source

## Not deployed yet

There is deliberately no `_platform/_compose/` or `_platform/_nginx/` folder: `_root/_platform/up.sh`
autodiscovers those, so adding them would put this site into the production deploy.
