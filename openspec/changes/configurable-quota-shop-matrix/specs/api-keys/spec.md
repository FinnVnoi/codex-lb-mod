## ADDED Requirements

### Requirement: Paid quota rules retain their exact window identity

The quota-shop catalog SHALL expose every API-key limit rule whose quota type is purchasable, including both periodic and lifetime windows. Fulfillment SHALL validate the exact `limit_id`, quota type, window, and model filter before changing the rule. A periodic rule whose current reset boundary has already passed SHALL be rejected so a stale order cannot add quota to a new period.

#### Scenario: One key has multiple windows of the same quota type
- **GIVEN** an API key has `total_tokens/5h`, `total_tokens/weekly`, and `total_tokens/lifetime` rules
- **WHEN** the key requests the quota-shop catalog
- **THEN** the response contains three distinct rules with their exact windows

#### Scenario: Stale periodic order cannot cross a reset boundary
- **GIVEN** an order snapshot targets a periodic rule and its captured reset boundary has passed
- **WHEN** fulfillment runs
- **THEN** fulfillment returns a conflict
- **AND** the rule maximum and purchase ledger remain unchanged

### Requirement: Periodic purchased quota expires with the selected period

A successful periodic quota purchase SHALL increase only the selected rule and record its current reset boundary in the purchase ledger. When that rule resets at that boundary, the purchased delta SHALL be subtracted from its maximum and usage SHALL reset to zero. A lifetime purchase SHALL not be removed by periodic reset processing.

#### Scenario: Weekly add-on expires at weekly reset
- **GIVEN** a buyer purchases an add-on for a weekly rule
- **WHEN** that exact weekly rule reaches its recorded reset boundary
- **THEN** its usage resets to zero
- **AND** its maximum returns to the value it had before the add-on

### Requirement: Operators configure dynamic sale rules by quota type and window

The shop price catalog SHALL identify configured sale rules by the composite identity `(limit_type, limit_window)`. Operators SHALL be able to add a desired type/window pair, edit its active state and pricing fields, or delete it. The admin surface SHALL render configured rules rather than pre-populating every supported pair. Buyer-facing pricing SHALL be attached only when both the API-key rule type and window match an active configured sale rule.

#### Scenario: Same type has different prices across windows
- **GIVEN** `total_tokens/5h` is active at one price and `total_tokens/lifetime` is active at a different price
- **WHEN** a key has both rules and opens the shop
- **THEN** each rule displays and calculates quota using its own price row

#### Scenario: Admin disables one pair without disabling siblings
- **GIVEN** `cost_usd/weekly` is disabled and `cost_usd/lifetime` is active
- **WHEN** a key has both rules and opens the shop
- **THEN** the weekly rule is unavailable for purchase
- **AND** the lifetime rule remains available

#### Scenario: Admin adds only a desired periodic rule
- **GIVEN** the price catalog contains only lifetime rules
- **WHEN** an operator adds `total_tokens/5h` with its own price
- **THEN** the admin list contains that new rule and the existing lifetime rules
- **AND** unrelated supported pairs are not created or displayed

#### Scenario: Admin deletes a sale rule
- **GIVEN** `total_tokens/5h` is configured
- **WHEN** the operator deletes that sale rule
- **THEN** the configured row is removed
- **AND** a key's matching 5h limit is no longer offered by the buyer shop

#### Scenario: Existing configured rules survive migration
- **GIVEN** a deployment migrates an existing price catalog
- **WHEN** dynamic sale-rule support is enabled
- **THEN** existing configured active states and prices are preserved
- **AND** no missing type/window pair is created without an operator action
