import pickle
import json
import shelve
import sys
import shutil
import os
import random
try:
    print("Trying method #1")
    sys.path.append('./zakat')
    from zakat_tracker import ZakatTracker, JSONEncoder, JSONDecoder
    print("Loaded method #1")
except Exception as e:
    print(e)
    print("Trying method #2")
    sys.path.append('../zakat')
    from zakat_tracker import ZakatTracker, JSONEncoder, JSONDecoder
    print("Loaded method #2" )

random.seed(1234567890)

path = './benchmark'

if os.path.exists(path):
    shutil.rmtree(path)

x = ZakatTracker(f'{path}/db')

t = ZakatTracker.time()
x.generate_random_csv_file(f'{path}/data.csv', 1_000_000, True)
print('generate_csv', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
y = x.import_csv(f'{path}/data.csv', debug=True)
print('import_csv', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))
print("accounts", len(x.accounts()), y)

t = ZakatTracker.time()
print(x.save())
print('Save-camel', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
print(x.load())
print('Load-camel', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with open(f"{path}/file.pkl", "wb") as f:
    pickle.dump(x.vault(), f)
print('Save-pickle', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with open(f"{path}/file.pkl", "rb") as f:
    pickle.load(f)
print('Load-pickle', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with open(f"{path}/file.json", "w") as f:
    json.dump(x.vault(), f, cls=JSONEncoder)
print('Save-json', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with open(f"{path}/file.json", "r") as f:
    json.load(f, cls=JSONDecoder)
print('Load-json', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with shelve.open(f"{path}/file.shlv") as db:
    db["db"] = x._vault
print('Save-shelve', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

t = ZakatTracker.time()
with shelve.open(f"{path}/file.shlv") as db:
    x._vault = db["db"]
print('Load-shelve', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

for _ in range(3):
    t = ZakatTracker.time()
    daily_logs = x.daily_logs()
    print('daily_logs', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))
    
for _ in range(3):
    t = ZakatTracker.time()
    report = x.check(2.5)
    print('check', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

    lock = x.lock()
    t = ZakatTracker.time()
    x.zakat(report)
    print('zakat', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))

    t = ZakatTracker.time()
    x.recall(lock=lock)
    print('recall', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))
    
    t = ZakatTracker.time()
    x.free(lock=lock, auto_save=False)
    print('free', ZakatTracker.duration_from_nanoseconds(ZakatTracker.time() - t))
