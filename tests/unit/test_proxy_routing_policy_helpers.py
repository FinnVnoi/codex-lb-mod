from types import SimpleNamespace

from app.modules.proxy import service


def test_account_branch_attempts_honor_provider_after_first_failure() -> None:
    policy = service._routing_engine_policy_from_settings(
        SimpleNamespace(account_failure_policy="provider_after_first_failure", account_max_attempts=7)
    )
    assert service._account_branch_max_attempts(policy) == 1


def test_account_branch_attempts_are_bounded() -> None:
    high = service._routing_engine_policy_from_settings(
        SimpleNamespace(account_failure_policy="accounts_before_providers", account_max_attempts=999)
    )
    low = service._routing_engine_policy_from_settings(
        SimpleNamespace(account_failure_policy="account_only", account_max_attempts=0)
    )
    assert service._account_branch_max_attempts(high) == 10
    assert service._account_branch_max_attempts(low) == 1
