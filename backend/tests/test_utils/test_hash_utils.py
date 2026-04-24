from backend.app.utils.hash_utils import hash_issues


def test_hash_issues_deterministic():
    issues = [{"type": "garble", "severity": "complex"}]
    h1 = hash_issues(issues)
    h2 = hash_issues(issues)
    assert h1 == h2


def test_hash_issues_different_inputs():
    a = [{"type": "garble", "severity": "complex"}]
    b = [{"type": "empty_content", "severity": "complex"}]
    assert hash_issues(a) != hash_issues(b)


def test_hash_issues_order_independent():
    issues_a = [{"type": "a", "severity": "x"}, {"type": "b", "severity": "y"}]
    issues_b = [{"type": "b", "severity": "y"}, {"type": "a", "severity": "x"}]
    assert hash_issues(issues_a) == hash_issues(issues_b)


def test_hash_issues_empty_list():
    h = hash_issues([])
    assert isinstance(h, int)


def test_hash_issues_ignores_extra_keys():
    a = [{"type": "garble", "severity": "complex", "description": "foo"}]
    b = [{"type": "garble", "severity": "complex", "description": "bar"}]
    assert hash_issues(a) == hash_issues(b)
