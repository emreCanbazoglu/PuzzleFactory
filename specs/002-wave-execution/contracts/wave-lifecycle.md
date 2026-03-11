# Wave Lifecycle Contract

Stages:

1. initialize
2. cell_generation (parallel)
3. cell_spec_build (parallel)
4. cell_evaluation (parallel)
5. portfolio_sync (global)
6. decision_finalize (global)

Cross-cell reads are forbidden before `portfolio_sync`.
