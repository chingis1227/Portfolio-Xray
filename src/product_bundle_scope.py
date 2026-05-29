"""
Product bundle scope for diagnosis-first materialization.

Orchestration only: controls which product-facing JSON adapters are written
after Blocks 1–3 (input, X-Ray, stress) complete.
"""

from __future__ import annotations

PRODUCT_BUNDLE_SCOPE_FULL = "full_product"
PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3 = "core_blocks_1_3"

PRODUCT_BUNDLE_SCOPE_VALUES = frozenset(
    {
        PRODUCT_BUNDLE_SCOPE_FULL,
        PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3,
    }
)
DEFAULT_PRODUCT_BUNDLE_SCOPE = PRODUCT_BUNDLE_SCOPE_FULL


def normalize_product_bundle_scope(scope: str | None) -> str:
    normalized = (scope or DEFAULT_PRODUCT_BUNDLE_SCOPE).strip().lower()
    if normalized not in PRODUCT_BUNDLE_SCOPE_VALUES:
        raise ValueError(
            f"Invalid product_bundle_scope {scope!r}; expected one of: "
            f"{', '.join(sorted(PRODUCT_BUNDLE_SCOPE_VALUES))}"
        )
    return normalized


def is_core_blocks_1_3_only(scope: str | None) -> bool:
    return normalize_product_bundle_scope(scope) == PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3
