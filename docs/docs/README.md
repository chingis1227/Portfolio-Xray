# Optimization specs

Каждая область оптимизации и пост-обработки описана отдельным файлом.

| Spec | File | Description |
|------|------|-------------|
| **Portfolio construction (canonical)** | [../portfolio_construction_policy.md](../portfolio_construction_policy.md) | Одностадийный оптимизатор, RC по активам, mandate, ProLiquidity, связь со стрессом |
| **ProLiquidity** | [optimization_proliquidity_spec.md](optimization_proliquidity_spec.md) | Ликвидность: life floor, vol-scaling cash, cash policy, alpha-shift при `prohibited` |
| **View After Optimization** | [view_after_optimization_spec.md](view_after_optimization_spec.md) | Протокол PM-представлений (HEDGE/TACTICAL) после оптимизации |

Двухэтапная схема и флаг **`--single-stage`** сняты: см. историю в репозитории / ExecPlan при необходимости.
