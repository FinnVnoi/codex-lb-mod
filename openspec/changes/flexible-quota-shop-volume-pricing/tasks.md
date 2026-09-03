# Tasks: flexible-quota-shop-volume-pricing

## 1. Fulfillment contract

- [x] 1.1 Accept every positive integer VND amount within the existing upper bound.
- [x] 1.2 Preserve exact amount and purchased-value idempotency checks.

## 2. FinnVnoi pricing

- [x] 2.1 Store optional volume tiers by exact quota type/window and minimum order amount.
- [x] 2.2 Let admin add, edit, and remove tier rows and exact VND values.
- [x] 2.3 Resolve the highest qualifying tier server-side and snapshot the effective unit price on order creation.
- [x] 2.4 Render tier prices and live calculations in the buyer shop and checkout.

## 3. Verification and release

- [x] 3.1 Run Codex tests, Ruff, PHP lint, OpenSpec validation, and pricing unit tests.
- [x] 3.2 Back up Codex-LB and hosting files/data, deploy, and verify live health/UI/schema.
