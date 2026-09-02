## 1. Persistence and API
- [x] Add a default-on model-source database column and migrate existing sources to enabled.
- [x] Expose the field through create/update/list schemas and service mapping.

## 2. Proxy accounting
- [x] Estimate chat/responses request tokens and buffered SSE output tokens.
- [x] Apply estimates only for enabled sources when upstream stream usage is absent.
- [x] Preserve upstream usage precedence and strict behavior when disabled.

## 3. Dashboard
- [x] Add schema/form payload support and a translated checkbox with caution text.

## 4. Verification
- [x] Add backend and frontend regression tests.
- [x] Run focused lint/type/test/build gates and OpenSpec validation.
- [x] Enable the option for the three xpiki sources and smoke test the live service.
