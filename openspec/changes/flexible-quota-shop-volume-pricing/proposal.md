# Flexible Quota Shop Volume Pricing

## Why

FinnVnoi quota-shop operators need exact VND pricing instead of a mandatory 500 VND increment, and optional volume-price tiers such as 2,000 VND per 1M tokens normally and 1,800 VND per 1M for orders from 100,000 VND.

## What Changes

- Allow positive integer VND amounts on the internal quota fulfillment contract instead of requiring 500 VND multiples.
- Let the external FinnVnoi pricing source attach zero or more order-value thresholds to each exact quota type/window rule.
- Resolve the highest qualifying threshold when an order is created and snapshot its effective unit price and purchased quota into that order.

## Impact

- Affected capability: `api-keys`
- Affected code: `app/modules/api_keys/quota_shop.py`, quota-shop integration tests, and FinnVnoi quota pricing/admin/shop PHP.
