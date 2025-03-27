import os
import time
from zakat import ZakatTracker, Time

def test_zakat_tracker():
    start = time.time_ns()
    os.chdir('tests')
    ledger = ZakatTracker('./zakat_test_db')
    ledger.test(True)
    print("#########################")
    print("######## TEST DONE ########")
    print("#########################")
    print(Time.duration_from_nanoseconds(time.time_ns() - start))
    print("#########################")
