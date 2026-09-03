## ADDED Requirements

### Requirement: Quota-shop fulfillment accepts exact VND amounts

The quota-shop fulfillment contract SHALL accept any positive integer VND amount within its configured maximum and SHALL NOT require the amount to be a multiple of 500 VND. The fulfillment ledger SHALL preserve the exact amount and purchased quota for idempotency.

#### Scenario: Exact non-500 VND amount is fulfilled

- **WHEN** the trusted shop submits an otherwise valid fulfillment for 750 VND
- **THEN** the request succeeds
- **AND** the purchase ledger records exactly 750 VND

### Requirement: FinnVnoi quota pricing supports deterministic volume tiers

Each configured FinnVnoi quota sale rule MAY define zero or more tiers consisting of a minimum order amount in VND and a unit price in VND. Order creation SHALL select the tier with the greatest minimum amount that does not exceed the submitted order amount, or the base price when no tier qualifies. It SHALL calculate purchased quota server-side with integer arithmetic and snapshot both purchased quota and the effective unit price in the order so later price edits do not change an existing order.

#### Scenario: Higher-volume order receives its configured price

- **GIVEN** a base price of 2,000 VND per 1M tokens
- **AND** a tier of 1,800 VND per 1M tokens from 100,000 VND
- **WHEN** a buyer creates an order for 100,000 VND
- **THEN** the effective price is 1,800 VND per 1M tokens
- **AND** the purchased quota is the integer floor of `100000 * 1000000 / 1800`

#### Scenario: Highest qualifying tier wins

- **GIVEN** several tiers qualify for the submitted order amount
- **WHEN** the order is created
- **THEN** the tier with the greatest minimum amount is selected

#### Scenario: Later edits do not reprice a pending order

- **GIVEN** an order has snapshotted an effective unit price and purchased quota
- **WHEN** an operator later edits or removes its pricing tier
- **THEN** fulfillment uses the values already stored on the order
