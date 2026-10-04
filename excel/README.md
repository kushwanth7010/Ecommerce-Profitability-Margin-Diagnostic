# Excel pricing sensitivity model

The companion `Pricing_Sensitivity_Model.xlsx` contains:

- **Assumptions:** baseline values from `outputs/summary.json`; editable input cells.
- **Pricing Scenarios:** formulas for 0%, 3%, 5%, 8% and 10% price changes applied only to negative-contribution SKUs.
- **Read Me:** modeling assumptions and limitations.

The workbook is a snapshot of the default synthetic dataset, not a live database link. After generating a different dataset, copy the new baseline values from `outputs/summary.json` into the input cells.

These scenarios hold unit volume, discounts, returns and shipping fixed and adjust revenue-dependent fees. They are illustrative sensitivities, not real savings or demand-aware forecasts.
