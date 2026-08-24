---
name: python-plot
description: >-
  Applies the house Matplotlib / seaborn figure conventions — GridSpec layout, seaborn style baseline, dynamic 5% y-axis padding, deliberate alpha layering, dpi=300 with a tight bounding box, and CJK-safe label fonts on Windows. Use this whenever a plot, chart, figure, or subplot is being produced, restyled, or saved in Python, including quick one-off diagnostic plots, and including requests phrased with no file in sight — "畫一張圖", "幫我畫個折線圖", "plot this", "把結果視覺化", "圖太醜幫我調一下", "存成圖檔" — as well as any call to plt.subplots, plt.figure, sns.lineplot, sns.barplot, or savefig.
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

- CJK labels (optional, Windows): if any label or title contains Chinese, set the font first to avoid tofu boxes:

  ```python
  plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
  plt.rcParams['axes.unicode_minus'] = False
  ```

## 3. Y-axis padding

- Compute the data range and dynamically reserve 5% headroom on BOTH sides, applied after all series are drawn:

  ```python
  def pad_ylim(ax, ymin, ymax, ratio=0.05):
      span = ymax - ymin
      pad = span * ratio if span > 0 else max(abs(ymax), 1.0) * ratio  # fallback for a zero-width range
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

## 6. Verification

A figure is not done until it has been rendered and looked at (global: Goal-Driven Execution):

1. Run the script and open the saved file — "the code looks right" is not a check.
2. No tofu boxes (`□`) in any label, title, tick, or legend entry. If any appear, §2's font block is missing or the chosen font lacks the glyph.
3. Nothing is clipped: the tight bounding box kept every axis label, legend, and title inside the canvas.
4. No series touches the top or bottom spine — §3's padding is applied and was computed from all series, not one.
5. The primary series is visually dominant; alpha was applied to background layers only.
6. Saved at `dpi=300` unless a deviation was stated.
