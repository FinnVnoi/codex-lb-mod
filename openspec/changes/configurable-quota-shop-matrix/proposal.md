# Configure Paid Quota Shop with Dynamic Sale Rules

## Why

API keys can have several independent limit rules, such as `total_tokens/5h`, `total_tokens/weekly`, and `cost_usd/lifetime`. The shop must not apply one price or sale decision to every rule sharing a quota type. Operators need to set a distinct price for each exact type/window pair or disable that pair entirely.

## What Changes

- Let Codex-LB expose and fulfill all supported windows for purchasable quota types while preserving exact `limit_id + type + window + model_filter` validation.
- Store hosting sale rules by composite identity `(limit_type, limit_window)`.
- Keep any existing configured rows and their current pricing during migration, without auto-creating missing type/window pairs.
- Let admin add only the type/window pairs they want to sell, edit price/minimum/step/maximum and active state, or delete a rule.
- Show buyers only configured rules whose exact type/window pair is active. Periodic purchases apply only until the selected rule's current reset and are removed when that rule resets.

## Impact

- Affected capability: `api-keys`
- Affected code: `app/modules/api_keys/quota_shop.py`, quota-shop integration tests, FinnVnoi quota pricing schema/admin/shop PHP.
- Operator-visible: admin maintains a compact list of configured sale rules; different windows of the same quota type can have different prices or be absent entirely.
