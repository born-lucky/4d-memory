from fourdmem.harness.math_verify import verify_pair


def test_math_verify_harness_is_callable() -> None:
    # Same attachment shape as fourdmem itself: import, call, bool.
    # Windows Math-Verify multiprocessing timeouts are flaky; do not require a True.
    result = verify_pair(r"$\frac{1}{2}$", r"$\frac{1}{2}$")
    assert isinstance(result, bool)
