# E-commerce Profitability & Margin Diagnostic

A reproducible Python, SQL and Excel portfolio project analyzing **synthetic** e-commerce transactions, refunds, costs, shipping, contribution margins and hypothetical pricing scenarios. No real customer, client or company information is used.

The project generates 12,000 fictional orders and 18,717 order lines with a fixed random seed. Run `python -m src.generate_data --orders 12000 --seed 2026`, `python -m src.build_db`, `python -m src.analyze` and `python -m pytest -q` after installing `requirements.txt`.

**Limitations:** Contribution profit excludes overhead, tax, marketing and return-shipping costs. Price scenarios assume constant demand and returns and are not realized savings or a demand forecast. Generated data and analytics outputs can be rebuilt from the committed source files.
