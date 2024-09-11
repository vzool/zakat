import os
from zakat import ZakatTracker, Helper, DictModel

def test_zakat_tracker():
    start = Helper.time()
    os.chdir('tests')
    ledger = ZakatTracker(
        model=DictModel(
            db_path='./zakat_test_db/test.camel',
            history_mode=True,
        ),
    )
    ledger.test(True)
    print("#########################")
    print("######## TEST DONE ########")
    print("#########################")
    print(Helper.duration_from_nanoseconds(Helper.time() - start))
    print("#########################")