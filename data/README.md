# Synthetic inputs

Every row in this directory is generated, fictional example data with **no real customers, employees, businesses or company results**.

The deterministic generator creates three CSVs from seed 2026:

```bash
python -m src.generate_data --orders 12000 --seed 2026
```

- `products.csv`: 120 products with fictional categories, list prices and cost assumptions.
- `orders.csv`: 12,000 orders with simulated dates, regions, selling channels, shipping costs and variable fee rates.
- `order_items.csv`: 18,717 lines with fictional sold and returned quantities, unit prices, costs and discounts.

See `docs/DATA_DICTIONARY.md` for column definitions. The GitHub Actions workflow regenerates the baseline files on the main branch after testing.
