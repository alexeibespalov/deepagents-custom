---
name: html-artifact-studio
description: "Create single-file HTML artifacts that render as interactive pages in ARIA, including inline JavaScript and optional Chart.js dashboards. Use when user asks for HTML artifacts, dashboards, data visualization pages, mini apps, or page-within-page outputs. Trigger on: 'create html artifact', 'make dashboard', 'build interactive page', 'chart this data', 'single-file web app'."
---

# HTML Artifact Studio

Create polished, single-page HTML artifacts that ARIA can render in the artifact viewer.

## When To Use

Use this skill when the user wants:

- A standalone HTML artifact (`.html`) in the Artifacts panel.
- An interactive page with inline JavaScript.
- A dashboard from tabular/JSON data.
- Data visualization (especially Chart.js).

## Core Rules

1. Always output a single `.html` artifact using `create_artifact`.
2. Keep everything self-contained in one file: HTML + CSS + JS.
3. Put JavaScript inline in `<script>` tags (no separate `.js` files).
4. Prefer semantic structure and responsive layout.
5. Default visual direction should prioritize dark mode and darker backgrounds unless the user explicitly asks for a light theme.
6. Include clear labels, legends, and units for charts.
7. Never create executable artifacts (`.sh`, `.bat`, etc.).

## Artifact Creation Path

Use:

```text
create_artifact(filename="<descriptive-name>.html", content="<!doctype html>...")
```

Artifacts are written to `sandbox/artifacts/` and rendered in the UI.

## Two Output Modes

### Mode A: Vanilla Interactive HTML

Use for calculators, forms, filters, status boards, or lightweight interactions.

Requirements:

- Modern, mobile-friendly layout with dark-first styling by default.
- Inline JS with small, readable functions.
- Visible empty/loading/error states when data may be missing.

### Mode B: Chart.js Dashboard

Use when user asks for graphs, trends, category comparison, distributions, or KPI widgets.

Chart.js include pattern:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

Requirements:

- At least one chart with explicit title and axis labels.
- Stable, deterministic color palette (avoid random colors), tuned for dark backgrounds by default.
- Graceful handling for empty arrays (show a message, not a broken chart).
- Keep chart config readable and grouped (`data`, `options`).

## Data Insertion Patterns

### Direct inline JSON (preferred)

```html
<script>
const DATA = {"labels": ["Jan", "Feb"], "values": [12, 19]};
</script>
```

### JSON script tag

```html
<script id="seed-data" type="application/json">{"rows":[...]}</script>
<script>
const seed = JSON.parse(document.getElementById('seed-data').textContent || '{}');
</script>
```

## Quality Checklist

Before saving artifact, verify:

- Filename is descriptive and ends in `.html`.
- Page renders without external build tools.
- No blocking runtime errors in normal path.
- Visual defaults are dark mode unless user asked for light styling.
- Dashboard has readable typography and spacing.
- Works at common viewport widths (desktop and mobile).

## Quick Skeleton

Use this baseline and adapt:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard</title>
  <style>
    :root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#9ca3af; --accent:#22d3ee; }
    * { box-sizing:border-box; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:linear-gradient(160deg,#020617,#111827); color:var(--text); }
    .wrap { max-width:1100px; margin:0 auto; padding:24px; }
    .grid { display:grid; gap:16px; grid-template-columns:repeat(12,minmax(0,1fr)); }
    .card { grid-column:span 12; background:rgba(17,24,39,.8); border:1px solid #1f2937; border-radius:14px; padding:16px; }
    @media (min-width: 900px) { .span-6 { grid-column:span 6; } }
    h1 { margin:0 0 8px; font-size:1.5rem; }
    p { margin:0; color:var(--muted); }
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Interactive Dashboard</h1>
    <p>Single-file HTML artifact with inline JavaScript.</p>
    <section class="grid" style="margin-top:16px;">
      <article class="card span-6"><canvas id="chartA" height="120"></canvas></article>
      <article class="card span-6" id="kpi"></article>
    </section>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    const rows = [
      { month: 'Jan', value: 12 },
      { month: 'Feb', value: 19 },
      { month: 'Mar', value: 15 },
      { month: 'Apr', value: 27 }
    ];

    const labels = rows.map(r => r.month);
    const values = rows.map(r => r.value);

    if (!labels.length) {
      document.getElementById('kpi').textContent = 'No data available.';
    } else {
      const total = values.reduce((a, b) => a + b, 0);
      document.getElementById('kpi').innerHTML = `<h2 style="margin:0 0 8px;">Total</h2><div style="font-size:2rem;font-weight:700;">${total}</div>`;

      new Chart(document.getElementById('chartA'), {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Value',
            data: values,
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(34,211,238,.2)',
            tension: 0.3,
            fill: true
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,.15)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,.15)' } }
          }
        }
      });
    }
  </script>
</body>
</html>
```

## Notes

- If the user asks for multiple pages, still start with one main `.html` artifact unless they explicitly request multi-file output.
- If Chart.js CDN is unavailable, fall back to a vanilla table + KPI view and explain the fallback.
- If the user requests "dark mode", "dark", "night", or gives no color preference, keep dark backgrounds as the default choice.
