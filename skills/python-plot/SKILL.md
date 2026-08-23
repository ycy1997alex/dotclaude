---
name: python-plot
description: >-
  Rules for Python plotting with matplotlib / seaborn: GridSpec layout, seaborn style baseline, dynamic 5% y-axis padding, alpha layering, save defaults (dpi=300, tight bbox), CJK label fonts. Apply to any task that creates, edits, or saves plots, subplots, or figures with matplotlib or seaborn.
paths:
  - "**/*.py"
  - "**/*.ipynb"
model: sonnet
effort: medium
---

# Python Plotting Rules (matplotlib / seaborn)

## 1. Layout

- Prefer `matplotlib.gridspec.GridSpec` for figure layout, especially multi-panel or uneven layouts:

  ```python
  from matplotlib.gridspec import GridSpec
  fig = plt.figure(figsize=(10, 6))
  gs = GridSpec(2, 2, figure=fig, width_ratios=[2, 1], hspace=0.3, wspace=0.25)
  ax_main = fig.add_subplot(gs[:, 0])
  ax_top  = fig.add_subplot(gs[0, 1])
  ax_bot  = fig.add_subplot(gs[1, 1])
  ```

- Set `width_ratios` / `height_ratios` / `hspace` / `wspace` explicitly rather than relying on defaults.

## 2. Style baseline

- Apply the seaborn style BEFORE plotting; default is:

  ```python
  import seaborn as sns
  sns.set_style('white')
  ```

  Switch styles only when the user asks.

- 中文標籤 (optional, Windows): if any label/title contains Chinese, set the font first to avoid tofu boxes:

  ```python
  plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
  plt.rcParams['axes.unicode_minus'] = False
  ```

## 3. Y-axis padding

- Compute the data range and dynamically reserve 5% headroom on BOTH sides, applied after all series are drawn:

  ```python
  def pad_ylim(ax, ymin, ymax, ratio=0.05):
      span = ymax - ymin
      pad = span * ratio if span > 0 else max(abs(ymax), 1.0) * ratio  # 全距為 0 時的退場機制
      ax.set_ylim(ymin - pad, ymax + pad)
  ```

- `ymin`/`ymax` come from the actual plotted data (all series combined), not from a single series.

## 4. Layering with alpha

- Use low alpha deliberately to create depth when elements overlap; keep the PRIMARY series fully opaque:
  - dense scatter clouds: `alpha=0.3–0.6`
  - `fill_between` / confidence bands: `alpha=0.15–0.3`
  - secondary/background lines: `alpha=0.5–0.8`
- Don't apply alpha to everything — contrast between opaque foreground and translucent background is what creates the layering.

## 5. Saving

- Defaults for every save: `dpi=300` and `bbox_inches='tight'`. Prefer one helper so the defaults stay consistent across a project:

  ```python
  def save_fig(fig, path, dpi=300):
      fig.savefig(path, dpi=dpi, bbox_inches='tight')
  ```

- Deviate (e.g., higher dpi for print, no tight bbox for fixed-canvas exports) only when the user asks or the output target requires it — say so when deviating.
