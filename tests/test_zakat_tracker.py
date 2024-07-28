import os
from zakat import ZakatTracker

def test_zakat_tracker():
    start = ZakatTracker.time()
    os.chdir('tests')
    ledger = ZakatTracker('./zakat_test_db/test.camel')
    ledger.test(True)
    print("#########################")
    print("######## TEST DONE ########")
    print("#########################")
    print(ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - start))
    print("#########################")