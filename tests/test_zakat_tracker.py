import os
from zakat import ZakatTracker, Helper, DictModel


def test_zakat_tracker():
    durations = {}
    for model in [
        DictModel(db_path="./zakat_test_db/zakat.camel", history_mode=True),
        # SQLiteModel(db_path="./zakat_test_db/zakat.sqlite", history_mode=True),
    ]:
        assert model.test(debug=True)
        ledger = ZakatTracker(model=model)
        start = Helper.time()
        assert ledger.test(debug=True)
        durations[model.__class__.__name__] = Helper.time() - start
    print("#########################")
    print("######## TEST DONE ########")
    print("#########################")
    for model_name, duration in durations.items():
        print("------------- Model: [" + model_name + "] -------------")
        print(Helper.duration_from_nanoseconds(duration))
    print("#########################")
