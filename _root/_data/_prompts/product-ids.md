# Product ID System

> **Status: Not yet implemented.** This document describes a pattern we are designing toward. Nothing described here exists in the codebase yet. When building new features, keep this pattern in mind — but do not implement it until explicitly instructed.

This project uses a fractal product graph to track every part of the codebase as a named, identifiable product. Every page, component, CSS section, and sub-section of UI carries a UUID that links it to a central registry. This document explains the schema, tagging rules, and how to use the system when working in this codebase.

---

## Core Concept

Everything is a product. A department owns products. A product owns pages and components. A page owns sections. A section owns sub-sections. This nesting can go as deep as needed — it is fractal by design.

Each product has a UUID. That UUID appears in three places:
1. `product.json` — the registry entry
2. The HTML — as a custom `<product>` element wrapping the DOM it owns
3. The CSS — as a comment block wrapping the rules it owns

All three always use the same UUID for the same thing.

---

## product.json Schema

Every product folder contains a `product.json`. Products without their own folder are declared inline as `children` in their parent's `product.json`.

```json
{
  "id": "uuid",
  "name": "kebab-case-name",
  "type": "system | department | product | webpage | component",
  "description": "One sentence.",
  "status": "active | inactive",
  "parents": ["parent-uuid"],
  "children": [],
  "dependencies": ["shared-component-uuid"],
  "capabilities": {}
}
```

### Fields

**`id`** — UUID v4. Generated once, never changed. This is the permanent identity of the product.

**`name`** — kebab-case. Must be unique across the entire system (enforced by `system.products`).

**`type`** — One of:
- `system` — the root node
- `department` — a business domain (e.g. `marketing`, `product`)
- `product` — a deployable or distributable thing (e.g. `acme.com`, `powerschool`)
- `webpage` — a page rendered at a URL (e.g. `index`, `about`, `calculator`)
- `component` — a reusable UI piece (e.g. `nav`, `footer`, `index-hero`)

**`parents`** — Direct parent IDs only. No grandparents. A product can have multiple parents (e.g. a shared component used in two departments).

**`children`** — Inline sub-products that don't have their own folder. Each child has the full schema recursively. Use this for sections of a page or sub-components of a component.

**`dependencies`** — IDs of shared Astro components this product imports. This is distinct from `parents` — a dependency is something you *use*, not something that *owns* you. Example: a page that imports `Nav.astro` lists nav's ID in `dependencies`.

**`capabilities`** — Feature flags for bootstrap (e.g. `"postgres": true`).

### Ownership vs. Usage

- `parents` / `children` = ownership tree (who owns whom)
- `dependencies` = usage graph (who uses whom)

A shared component like `Nav.astro` is *owned by* `acme.com` (its parent). It is *used by* `index`, `about`, and `calculator` (its dependents). Those pages list nav's ID in their `dependencies` — they do not become nav's parents.

---

## HTML Tagging

Use a custom `<product>` HTML element to mark the DOM boundaries of a product.

```html
<product id="uuid">
  <!-- all HTML owned by this product -->
</product>
```

### Rules

**Do tag** a section when it has its own entry in `product.json` — whether that's a top-level product, a webpage, or an inline child component.

**Do nest** product tags. A page tag wraps everything; section tags sit inside it; sub-section tags sit inside those.

```html
<product id="page-uuid">
  <product id="hero-uuid">
    <product id="hero-text-uuid">
      ...
    </product>
    <product id="hero-stats-uuid">
      ...
    </product>
  </product>
</product>
```

**Do not tag** a component file's slot or layout wrapper with its own ID — the file's identity is already in `product.json`. A `<slot />` wrapping itself is circular and adds no information.

**Do not tag** base resets, global tokens, or foundational layout wrappers that belong to the page as a whole — these are inferred as owned by the page.

---

## CSS Tagging

Use paired CSS comments to mark which product owns a group of CSS rules.

```css
/* <product id="uuid"> */
.some-class { ... }
.some-other-class { ... }
/* </product> */
```

### Rules

**Do tag** when a CSS section styles a specific named product (e.g. the nav, a hero section, a result card). The ID in the comment must match the HTML tag ID and the product.json ID for the same thing.

**Do not tag** base resets (`*, *::before, *::after`), `html`/`body` rules, or `@import` statements — these are inferred as owned by the file/page that contains them.

**Do not tag** shared utility sections (`.section`, `.container`, `.eyebrow`, etc.) that are page-level layout helpers with no specific sub-product owner — leave them untagged and they are inferred as belonging to the page.

**Do fold** responsive `@media` rules into the product block they affect, rather than leaving them in a separate block at the bottom of the file.

**Before tagging, strip dead CSS.** If a CSS section defines classes that are not used anywhere in the current HTML, remove it. Dead CSS should not be tagged — tagging it implies it is active.

---

## Database

Product relationships are stored in `system.product_relationships`:

```sql
CREATE TABLE system.product_relationships (
    source_id UUID NOT NULL REFERENCES system.products(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES system.products(id) ON DELETE CASCADE,
    kind      VARCHAR(50) NOT NULL CHECK (kind IN ('child', 'parent', 'dependency')),
    PRIMARY KEY (source_id, target_id, kind)
);
```

`bootstrap.py` reads every `product.json` at startup and writes all products and relationships to the DB. It handles:
- Folder-based products (own `product.json`)
- Inline children (nested in parent's `product.json`)
- Parent edges
- Dependency edges

---

## Using the System

### Development

When asked to build or change a feature, look up its product ID first. Then grep the codebase for that UUID — every file that references it (HTML tag, CSS block, product.json) defines the full scope of the feature. You know exactly which CSS belongs to it, which components it depends on, and which pages render it. You won't accidentally edit a sibling's CSS or miss a file.

When adding a new section to a page:
1. Generate a UUID
2. Add a `product.json` child entry under the page
3. Wrap the HTML in `<product id="uuid">`
4. Wrap the CSS in `/* <product id="uuid"> */ ... /* </product> */`

### Code Cleanup

Cross-reference product IDs between `product.json` and the codebase:

- A UUID in `product.json` with no matching `<product>` tag in any HTML file → untagged or dead product
- A `<product>` tag in HTML with no matching UUID in `product.json` → orphaned tag
- A CSS block tagged with a UUID that doesn't exist in `product.json` → orphaned styles
- A CSS section with no tag and classes not used anywhere → dead CSS, delete it

The fractal structure also reveals scope creep: if a leaf component has accumulated many children, it may need its own folder and `product.json`.

### Monitoring and Alerting

Map errors, slow queries, and failed requests back to a product ID. Instead of "the homepage is slow," you can pinpoint "the `index-demo` component (`9e59d01c`) — the Cal.com embed — is timing out."

Benefits:
- Set alert thresholds per product, not per page
- Track error rates at the component level
- The parent/child graph enables rollup: an alert on `index-hero-stats` automatically bubbles up to `index-hero` → `index` → `acme.com`
- Regressions surface in the exact sub-product that regressed, not the whole page

---

## Naming Conventions

- Top-level components: `nav`, `footer`, `layout`, `page-styles`
- Sub-components of a component: `nav-logo`, `nav-links`, `nav-mobile-menu`
- Page sections: `index-hero`, `index-problem`, `about-team`
- Sub-sections of a page section: `index-hero-text`, `index-hero-stats`, `index-problem-pains`, `index-problem-callout`
- Names must be unique across the entire system — prefix with page name when needed to avoid collisions (e.g. `nav-logo` and `footer-logo` are distinct, not just `logo`)
