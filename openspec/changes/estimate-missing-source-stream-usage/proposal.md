# Change: Estimate missing model-source stream usage

## Why
Some OpenAI-compatible providers accept `stream_options.include_usage` but omit the final usage object. Limited API-key requests are currently rejected after a valid response has already streamed because quota settlement cannot proceed.

## What Changes
- Add a per-model-source option, enabled by default, to estimate missing streaming usage; operators can disable it for strict fail-closed accounting.
- When enabled, estimate input and output tokens from the forwarded request and buffered SSE output only when upstream usage is absent.
- Use estimated usage for quota settlement, request logging, and source pricing.
- Expose the option as a dashboard checkbox.

## Impact
Existing and newly created sources default to estimation-enabled behavior. Operators can opt individual sources into strict fail-closed accounting by disabling the option. Upstream-reported usage always takes precedence.
