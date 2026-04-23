# 5D Bubble Dashboard (external Excel version)

This version reads `cm_data.xlsx` at runtime in the browser instead of embedding the data into the HTML.

## Files
- `index.html` – the static dashboard
- `cm_data.xlsx` – the source workbook read by the page

## Expected columns in the first sheet
- `Category`
- `Strategic`
- `Risk`
- `Sustainability`
- `Value`
- `GS`

## How updates work
1. Replace or edit `cm_data.xlsx` in the repo.
2. Commit and push.
3. Refresh the GitHub Pages site.

## GitHub Pages setup
Deploy the branch/folder containing these files. Keep `index.html` and `cm_data.xlsx` in the published folder.

## Notes
- The page fetches `./cm_data.xlsx` at runtime.
- It parses the workbook client-side using SheetJS and renders the chart with Plotly.
- The workbook must remain in the same folder as `index.html`, unless you change `EXCEL_PATH` in the script.
