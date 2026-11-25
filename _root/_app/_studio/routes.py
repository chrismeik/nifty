from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from _app._postgres.db import engine

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Studio</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Courier New', monospace; background: #0f1117; color: #e2e8f0; min-height: 100vh; }
  header { padding: 1.25rem 2rem; border-bottom: 1px solid #1e2433; }
  header h1 { font-size: 0.85rem; font-weight: 600; color: #64748b; letter-spacing: 0.1em; text-transform: uppercase; }
  #tree { padding: 2rem; }
  .node { margin: 0; }
  .row {
    display: flex; align-items: baseline; gap: 0.5rem;
    padding: 0.3rem 0.5rem; border-radius: 0.3rem; cursor: pointer;
    user-select: none;
  }
  .row:hover { background: #1a2030; }
  .row:hover .rel-btn { opacity: 1; }
  .toggle {
    width: 1rem; flex-shrink: 0; color: #475569; font-size: 0.75rem;
    transition: transform 0.15s;
  }
  .toggle.open { transform: rotate(90deg); }
  .toggle.empty { color: transparent; cursor: default; }
  .name { font-size: 0.875rem; color: #94a3b8; }
  .name .seg { color: #e2e8f0; font-weight: 500; }
  .desc { font-size: 0.775rem; color: #475569; margin-left: 0.25rem; }
  .badge {
    font-size: 0.65rem; padding: 0.1rem 0.4rem; border-radius: 2rem;
    background: #1e2433; color: #64748b; flex-shrink: 0;
  }
  .rel-btn {
    margin-left: auto; flex-shrink: 0;
    font-size: 0.85rem; color: #475569; opacity: 0;
    transition: color 0.15s, opacity 0.15s;
    cursor: pointer; padding: 0 0.25rem; line-height: 1;
  }
  .rel-btn:hover { color: #94a3b8; }
  .children { margin-left: 1.75rem; border-left: 1px solid #1e2433; display: none; }
  .children.open { display: block; }
  #loading { padding: 2rem; color: #475569; font-size: 0.875rem; }
  #error { padding: 2rem; color: #ef4444; font-size: 0.875rem; }

  /* Modal */
  #modal-backdrop {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.65); backdrop-filter: blur(2px);
    z-index: 100; align-items: center; justify-content: center;
  }
  #modal-backdrop.open { display: flex; }
  #modal {
    background: #0d1117; border: 1px solid #1e2433;
    border-radius: 0.5rem; width: 620px; max-width: 95vw;
    max-height: 85vh; display: flex; flex-direction: column;
    overflow: hidden;
  }
  #modal-header {
    padding: 0.9rem 1.25rem; border-bottom: 1px solid #1e2433;
    display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0;
  }
  #modal-title { font-size: 0.875rem; font-weight: 600; color: #e2e8f0; }
  #modal-subtitle { font-size: 0.75rem; color: #475569; }
  #modal-close {
    margin-left: auto; cursor: pointer; color: #475569;
    font-size: 1rem; line-height: 1; flex-shrink: 0;
  }
  #modal-close:hover { color: #94a3b8; }
  #modal-graph {
    flex: 1; overflow: auto; padding: 0;
    display: flex; align-items: center; justify-content: center;
  }
  #modal-loading { padding: 2rem; color: #475569; font-size: 0.8rem; text-align: center; }
  #modal-err { padding: 1rem 1.25rem; color: #ef4444; font-size: 0.8rem; }
  #modal-empty { padding: 2rem; color: #334155; font-size: 0.8rem; text-align: center; font-style: italic; }
</style>
</head>
<body>
<header><h1>Studio &mdash; Product Tree</h1></header>
<div id="tree"><div id="loading">Loading...</div></div>

<div id="modal-backdrop">
  <div id="modal">
    <div id="modal-header">
      <span id="modal-title"></span>
      <span id="modal-subtitle"></span>
      <span id="modal-close">✕</span>
    </div>
    <div id="modal-graph">
      <div id="modal-loading">Loading relationships…</div>
      <div id="modal-err" style="display:none"></div>
      <div id="modal-empty" style="display:none">No relationships found in graph.</div>
    </div>
  </div>
</div>

<script>
// ── Utilities ────────────────────────────────────────────────────────────────

function shortName(fullName) {
  const parts = fullName.split('/');
  return parts[parts.length - 1];
}

function displayName(fullName) {
  const parts = fullName.split('/');
  const last = parts[parts.length - 1];
  const prefix = parts.slice(0, -1).join('/');
  return prefix
    ? `<span style="color:#475569">${prefix}/</span><span class="seg">${last}</span>`
    : `<span class="seg">${last}</span>`;
}

// ── Tree ─────────────────────────────────────────────────────────────────────

async function loadTree() {
  const container = document.getElementById('tree');
  try {
    const res = await fetch('/studio/tree');
    if (!res.ok) throw new Error(await res.text());
    const roots = await res.json();
    container.innerHTML = '';
    roots.forEach(node => container.appendChild(buildNode(node, true)));
  } catch (e) {
    container.innerHTML = `<div id="error">Failed to load tree: ${e.message}</div>`;
  }
}

function buildNode(node, startOpen) {
  const wrapper = document.createElement('div');
  wrapper.className = 'node';
  const hasChildren = node.children && node.children.length > 0;

  const row = document.createElement('div');
  row.className = 'row';

  const toggle = document.createElement('span');
  toggle.className = `toggle${hasChildren ? '' : ' empty'}`;
  toggle.textContent = '▶';

  const nameEl = document.createElement('span');
  nameEl.className = 'name';
  nameEl.innerHTML = displayName(node.name);

  const badge = document.createElement('span');
  badge.className = 'badge';
  badge.textContent = node.type || 'product';

  const relBtn = document.createElement('span');
  relBtn.className = 'rel-btn';
  relBtn.textContent = '⫚';
  relBtn.title = 'View relationships';
  relBtn.addEventListener('click', e => { e.stopPropagation(); openModal(node.id, node.name); });

  row.appendChild(toggle);
  row.appendChild(nameEl);
  row.appendChild(badge);
  if (node.description) {
    const desc = document.createElement('span');
    desc.className = 'desc';
    desc.textContent = '— ' + node.description;
    row.appendChild(desc);
  }
  row.appendChild(relBtn);

  const childrenEl = document.createElement('div');
  childrenEl.className = 'children';
  if (hasChildren) {
    node.children.forEach(child => childrenEl.appendChild(buildNode(child, false)));
    row.addEventListener('click', () => {
      const open = childrenEl.classList.toggle('open');
      toggle.classList.toggle('open', open);
    });
    if (startOpen) { childrenEl.classList.add('open'); toggle.classList.add('open'); }
  }

  wrapper.appendChild(row);
  wrapper.appendChild(childrenEl);
  return wrapper;
}

// ── Modal ─────────────────────────────────────────────────────────────────────

const backdrop   = document.getElementById('modal-backdrop');
const modalTitle = document.getElementById('modal-title');
const modalSub   = document.getElementById('modal-subtitle');
const modalGraph = document.getElementById('modal-graph');

document.getElementById('modal-close').addEventListener('click', closeModal);
backdrop.addEventListener('click', e => { if (e.target === backdrop) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function closeModal() { backdrop.classList.remove('open'); }

async function openModal(id, name) {
  modalTitle.textContent = shortName(name);
  modalSub.textContent = '';
  modalGraph.innerHTML = '<div id="modal-loading">Loading relationships…</div>';
  backdrop.classList.add('open');

  try {
    const res = await fetch(`/studio/relationships/${id}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    const total = (data.parents||[]).length + (data.children||[]).length +
                  (data.dependencies||[]).length + (data.dependents||[]).length;
    modalSub.textContent = total === 0 ? '' : `${total} relationship${total !== 1 ? 's' : ''}`;
    renderGraph(data, name);
  } catch (e) {
    modalGraph.innerHTML = `<div id="modal-err">${e.message}</div>`;
  }
}

// ── SVG Graph ────────────────────────────────────────────────────────────────

const NS = 'http://www.w3.org/2000/svg';

const COLORS = {
  focal:     '#94a3b8',
  parent:    '#60a5fa',
  child:     '#4ade80',
  dep:       '#fbbf24',
  dependent: '#c084fc',
};

// Node dimensions
const NW = 112, NH = 26, RX = 4;
const FW = 132, FH = 34;
const HGAP = 48;   // horizontal gap between focal edge and side-node edge
const VGAP = 48;   // vertical gap between focal edge and top/bottom-node edge
const SGAP = 10;   // gap between sibling nodes in a stack/row
const PAD  = 20;   // outer padding

function stackH(arr) { return arr.length ? arr.length * NH + (arr.length - 1) * SGAP : 0; }
function rowW(arr)   { return arr.length ? arr.length * NW + (arr.length - 1) * SGAP : 0; }

// Find where a line exits a rectangle (rect centered at rx,ry with half-dims hw,hh)
// given unit direction (ndx,ndy) going AWAY from center. Returns edge intersection.
function rectExit(cx, cy, hw, hh, ndx, ndy) {
  const ax = Math.abs(ndx), ay = Math.abs(ndy);
  let t;
  if (ax < 1e-9) { t = hh / ay; }
  else if (ay < 1e-9) { t = hw / ax; }
  else { t = Math.min(hw / ax, hh / ay); }
  return [cx + ndx * t, cy + ndy * t];
}

function mkMarker(id, color) {
  const m = document.createElementNS(NS, 'marker');
  m.setAttribute('id', id);
  m.setAttribute('viewBox', '0 0 8 8');
  m.setAttribute('refX', '8');
  m.setAttribute('refY', '4');
  m.setAttribute('markerWidth', '5');
  m.setAttribute('markerHeight', '5');
  m.setAttribute('orient', 'auto');
  const p = document.createElementNS(NS, 'path');
  p.setAttribute('d', 'M 0 1 L 7 4 L 0 7 Z');
  p.setAttribute('fill', color);
  m.appendChild(p);
  return m;
}

function mkNode(cx, cy, w, h, name, color, isFocal) {
  const g = document.createElementNS(NS, 'g');

  const rect = document.createElementNS(NS, 'rect');
  rect.setAttribute('x', cx - w / 2);
  rect.setAttribute('y', cy - h / 2);
  rect.setAttribute('width', w);
  rect.setAttribute('height', h);
  rect.setAttribute('rx', RX);
  rect.setAttribute('fill', isFocal ? '#1a2744' : '#111827');
  rect.setAttribute('stroke', color);
  rect.setAttribute('stroke-width', isFocal ? '1.5' : '1');
  g.appendChild(rect);

  const text = document.createElementNS(NS, 'text');
  text.setAttribute('x', cx);
  text.setAttribute('y', cy);
  text.setAttribute('dominant-baseline', 'middle');
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('fill', isFocal ? '#e2e8f0' : color);
  text.setAttribute('font-family', "'Courier New', monospace");
  text.setAttribute('font-size', isFocal ? '11' : '10');
  const seg = shortName(name);
  const maxChars = Math.floor((w - 10) / 6.4);
  text.textContent = seg.length > maxChars ? seg.slice(0, maxChars - 1) + '…' : seg;
  g.appendChild(text);

  return g;
}

function mkEdge(x1, y1, w1, h1, x2, y2, w2, h2, color, markerId) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 2) return null;
  const nx = dx / len, ny = dy / len;

  const [sx, sy] = rectExit(x1, y1, w1 / 2, h1 / 2, nx, ny);
  const [ex, ey] = rectExit(x2, y2, w2 / 2, h2 / 2, -nx, -ny);

  const line = document.createElementNS(NS, 'line');
  line.setAttribute('x1', sx);
  line.setAttribute('y1', sy);
  line.setAttribute('x2', ex);
  line.setAttribute('y2', ey);
  line.setAttribute('stroke', color);
  line.setAttribute('stroke-width', '1');
  line.setAttribute('opacity', '0.55');
  line.setAttribute('marker-end', `url(#${markerId})`);
  return line;
}

function renderGraph(data, focalName) {
  const parents    = data.parents     || [];
  const children   = data.children    || [];
  const deps       = data.dependencies|| [];
  const dependents = data.dependents  || [];

  const total = parents.length + children.length + deps.length + dependents.length;
  if (total === 0) {
    modalGraph.innerHTML = '<div id="modal-empty" style="display:block;padding:2rem;color:#334155;font-size:.8rem;text-align:center;font-style:italic">No relationships found in graph.</div>';
    return;
  }

  // Compute SVG dimensions
  const leftW  = dependents.length ? NW + HGAP : 0;
  const rightW = deps.length       ? HGAP + NW : 0;
  const midW   = PAD + leftW + FW + rightW + PAD;
  const topRowW  = parents.length  ? rowW(parents)  + PAD * 2 : 0;
  const botRowW  = children.length ? rowW(children) + PAD * 2 : 0;
  const LEGEND_H = 22;

  const svgW  = Math.max(midW, topRowW, botRowW, 320);
  const fcx   = svgW / 2;  // focal center x

  const sideH = Math.max(stackH(dependents), stackH(deps), FH);
  const topH  = parents.length  ? NH + VGAP : 0;
  const botH  = children.length ? VGAP + NH : 0;
  const svgH  = PAD + topH + sideH + botH + PAD + LEGEND_H;
  const fcy   = PAD + topH + sideH / 2;

  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('width',   svgW);
  svg.setAttribute('height',  svgH);
  svg.setAttribute('viewBox', `0 0 ${svgW} ${svgH}`);

  // Markers
  const defs = document.createElementNS(NS, 'defs');
  defs.appendChild(mkMarker('arr-parent',    COLORS.parent));
  defs.appendChild(mkMarker('arr-child',     COLORS.child));
  defs.appendChild(mkMarker('arr-dep',       COLORS.dep));
  defs.appendChild(mkMarker('arr-dependent', COLORS.dependent));
  svg.appendChild(defs);

  // Helper: draw edges first (so nodes sit on top)
  const edgeLayer = document.createElementNS(NS, 'g');
  const nodeLayer = document.createElementNS(NS, 'g');
  svg.appendChild(edgeLayer);
  svg.appendChild(nodeLayer);

  function addEdge(x1, y1, w1, h1, x2, y2, w2, h2, color, mid) {
    const el = mkEdge(x1, y1, w1, h1, x2, y2, w2, h2, color, mid);
    if (el) edgeLayer.appendChild(el);
  }

  // Focal
  nodeLayer.appendChild(mkNode(fcx, fcy, FW, FH, focalName, COLORS.focal, true));

  // Parents (above)
  if (parents.length) {
    const total = rowW(parents);
    const startX = fcx - total / 2 + NW / 2;
    parents.forEach((p, i) => {
      const px = startX + i * (NW + SGAP);
      const py = PAD + NH / 2;
      addEdge(px, py, NW, NH, fcx, fcy, FW, FH, COLORS.parent, 'arr-parent');
      nodeLayer.appendChild(mkNode(px, py, NW, NH, p.name, COLORS.parent, false));
    });
  }

  // Children (below)
  if (children.length) {
    const total = rowW(children);
    const startX = fcx - total / 2 + NW / 2;
    children.forEach((c, i) => {
      const cx2 = startX + i * (NW + SGAP);
      const cy2 = PAD + topH + sideH + VGAP + NH / 2;
      addEdge(fcx, fcy, FW, FH, cx2, cy2, NW, NH, COLORS.child, 'arr-child');
      nodeLayer.appendChild(mkNode(cx2, cy2, NW, NH, c.name, COLORS.child, false));
    });
  }

  // Dependents (left)
  if (dependents.length) {
    const total = stackH(dependents);
    const startY = fcy - total / 2 + NH / 2;
    dependents.forEach((d, i) => {
      const dx = PAD + NW / 2;
      const dy = startY + i * (NH + SGAP);
      addEdge(dx, dy, NW, NH, fcx, fcy, FW, FH, COLORS.dependent, 'arr-dependent');
      nodeLayer.appendChild(mkNode(dx, dy, NW, NH, d.name, COLORS.dependent, false));
    });
  }

  // Dependencies (right)
  if (deps.length) {
    const total = stackH(deps);
    const startY = fcy - total / 2 + NH / 2;
    deps.forEach((d, i) => {
      const dx = svgW - PAD - NW / 2;
      const dy = startY + i * (NH + SGAP);
      addEdge(fcx, fcy, FW, FH, dx, dy, NW, NH, COLORS.dep, 'arr-dep');
      nodeLayer.appendChild(mkNode(dx, dy, NW, NH, d.name, COLORS.dep, false));
    });
  }

  // Legend
  const legendItems = [
    { label: 'parent',     color: COLORS.parent     },
    { label: 'child',      color: COLORS.child      },
    { label: 'depends on', color: COLORS.dep        },
    { label: 'dependent',  color: COLORS.dependent  },
  ];
  const ly = svgH - 10;
  const legendW = legendItems.reduce((acc, it) => acc + 14 + it.label.length * 6.2 + 14, 0);
  let lx = (svgW - legendW) / 2;
  legendItems.forEach(({ label, color }) => {
    const seg = document.createElementNS(NS, 'line');
    seg.setAttribute('x1', lx); seg.setAttribute('y1', ly);
    seg.setAttribute('x2', lx + 10); seg.setAttribute('y2', ly);
    seg.setAttribute('stroke', color); seg.setAttribute('stroke-width', '1.5');
    svg.appendChild(seg);
    lx += 14;
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', lx); t.setAttribute('y', ly);
    t.setAttribute('dominant-baseline', 'middle');
    t.setAttribute('fill', color);
    t.setAttribute('font-family', "'Courier New', monospace");
    t.setAttribute('font-size', '8');
    t.setAttribute('opacity', '0.65');
    t.textContent = label;
    svg.appendChild(t);
    lx += label.length * 6.2 + 14;
  });

  modalGraph.innerHTML = '';
  modalGraph.style.cssText = 'flex:1; overflow:auto; padding:1rem; display:flex; align-items:center; justify-content:center;';
  modalGraph.appendChild(svg);
}

loadTree();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def studio_ui():
    return _HTML


@router.get("/tree")
async def studio_tree():
    async with engine.connect() as conn:
        products_result = await conn.execute(
            text("SELECT id, name, type, description, status FROM system.products")
        )
        products = {str(row.id): {**row._mapping, "id": str(row.id)} for row in products_result}

        rels_result = await conn.execute(
            text("SELECT source_id, target_id FROM system.product_relationships WHERE kind = 'child'")
        )
        child_map: dict[str, list[str]] = {}
        child_ids: set[str] = set()
        for row in rels_result:
            child_map.setdefault(str(row.source_id), []).append(str(row.target_id))
            child_ids.add(str(row.target_id))

    top_ids = [pid for pid in products if pid not in child_ids]

    # Skip the literal "root" product and promote its children as display roots
    display_ids: list[str] = []
    for pid in top_ids:
        if products[pid]["name"] == "root":
            display_ids.extend(child_map.get(pid, []))
        else:
            display_ids.append(pid)

    def build(pid: str) -> dict:
        p = products[pid]
        return {
            "id": pid,
            "name": p["name"],
            "type": p["type"],
            "description": p["description"],
            "status": p["status"],
            "children": [build(cid) for cid in child_map.get(pid, []) if cid in products],
        }

    return JSONResponse([build(pid) for pid in sorted(display_ids, key=lambda pid: products[pid]["name"])])


@router.get("/relationships/{product_id}")
async def studio_relationships(product_id: str):
    try:
        from _app._graphiti.client import get_driver
        driver = get_driver()
    except ImportError:
        return JSONResponse({"parents": [], "children": [], "dependencies": [], "dependents": []})

    async with driver.session() as session:
        def to_dict(n) -> dict:
            return {"id": n["id"], "name": n["name"], "type": n.get("type") or "product"}

        parents_r     = await session.run("MATCH (p:Product)-[:HAS_CHILD]->(n:Product {id:$id}) RETURN p", id=product_id)
        parents       = [to_dict(r["p"]) async for r in parents_r]

        children_r    = await session.run("MATCH (n:Product {id:$id})-[:HAS_CHILD]->(c:Product) RETURN c", id=product_id)
        children      = [to_dict(r["c"]) async for r in children_r]

        deps_r        = await session.run("MATCH (n:Product {id:$id})-[:DEPENDS_ON]->(d:Product) RETURN d", id=product_id)
        dependencies  = [to_dict(r["d"]) async for r in deps_r]

        dependents_r  = await session.run("MATCH (d:Product)-[:DEPENDS_ON]->(n:Product {id:$id}) RETURN d", id=product_id)
        dependents    = [to_dict(r["d"]) async for r in dependents_r]

    return JSONResponse({
        "parents":      parents,
        "children":     children,
        "dependencies": dependencies,
        "dependents":   dependents,
    })
