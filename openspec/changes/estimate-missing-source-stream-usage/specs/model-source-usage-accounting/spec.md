## ADDED Requirements

### Requirement: Missing streaming usage estimation is opt-in per model source
The system MUST provide a per-model-source option, enabled by default for existing and newly created sources, that permits local usage estimation when an OpenAI-compatible streaming response omits valid usage metadata. Operators MUST be able to disable it for strict fail-closed accounting.

#### Scenario: Existing and new sources default to estimation enabled
- **GIVEN** an existing source is migrated or a new source is created without an explicit option value
- **THEN** missing-usage estimation MUST be enabled.

#### Scenario: Disabled source remains strict
- **GIVEN** a limited API key routes to a source whose missing-usage estimation option is disabled
- **WHEN** the source stream completes without valid usage metadata
- **THEN** the request MUST retain the existing `usage_unavailable` behavior
- **AND** the usage reservation MUST be released.

#### Scenario: Enabled source settles estimated usage
- **GIVEN** a limited API key routes to a source whose missing-usage estimation option is enabled
- **WHEN** the source stream completes successfully without valid usage metadata
- **THEN** the system MUST estimate non-negative input and output token counts from the request and buffered response
- **AND** it MUST settle quota and source cost using that estimate
- **AND** it MUST return the successful buffered stream to the client.

#### Scenario: Upstream usage takes precedence
- **GIVEN** missing-usage estimation is enabled for a source
- **WHEN** the source supplies valid usage metadata
- **THEN** the system MUST use the upstream-reported usage without replacing it with an estimate.

### Requirement: Dashboard exposes the source option
The model-source create and edit forms MUST expose the missing streaming usage estimation option with text explaining that values are approximate.
