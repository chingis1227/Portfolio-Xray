# Optimization specs

Each optimization domain has its own spec file. This keeps logic separate and easier to maintain.

| Spec | File | Description |
|------|------|-------------|
| **ProLiquidity** | [optimization_proliquidity_spec.md](optimization_proliquidity_spec.md) | Liquidity: life floor, vol-scaling cash, cash policy, alpha-shift when prohibited |
| **View After Optimization** | [view_after_optimization_spec.md](view_after_optimization_spec.md) | Protocol for applying PM views (HEDGE/TACTICAL) after optimization: gates, funding rules, execution, reporting |

When you add new optimizations (e.g. risk budget, RC caps), add a new file here and a row to this table.
