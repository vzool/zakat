import pytest
from zakat import ZakatTracker

def test_zakat_tracker():
    ledger = ZakatTracker("test.pickle")
    ledger.test(True)