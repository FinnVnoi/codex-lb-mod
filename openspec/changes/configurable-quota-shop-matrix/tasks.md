# Tasks: configurable-quota-shop-matrix

## 1. Codex-LB behavior

- [x] 1.1 Return every supported window for purchasable quota types in the authenticated shop catalog.
- [x] 1.2 Fulfill exact periodic or lifetime rules after validating limit identity and current reset boundary.
- [x] 1.3 Preserve periodic-purchase reset accounting so purchased quota is removed at the selected rule reset.

## 2. FinnVnoi dynamic sale rules

- [x] 2.1 Migrate `api_quota_prices` to a composite primary key `(limit_type, limit_window)` without losing current lifetime pricing.
- [x] 2.2 Preserve existing configured rules without auto-seeding missing type/window pairs.
- [x] 2.3 Match buyer catalog rules to exact active type/window sale rules.
- [x] 2.4 Add admin controls to create, update, enable/disable, and delete configured sale rules.
- [x] 2.5 Update buyer-facing copy and reset labels for periodic and lifetime quota.

## 3. Verification and release

- [x] 3.1 Run Codex-LB integration tests, Ruff, PHP lint, OpenSpec validation, and schema checks.
- [x] 3.2 Back up Codex-LB, hosting files, and hosting price/order tables.
- [x] 3.3 Deploy and verify hashes/schema/service health.
- [x] 3.4 Run production E2E proving an added periodic rule appears at its own price, fulfills against the snapshotted reset, resets correctly, and disappears after deletion; remove temporary data.
