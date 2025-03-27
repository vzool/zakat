import json
import ujson
import msgspec
import time
import random

def generate_complex_data(size=1000):
    """Generates complex nested data for benchmarking."""
    data = {
        "id": random.randint(1, 100000),
        "timestamp": time.time(),
        "data": [
            {
                "name": f"Item {i}",
                "value": random.random(),
                "details": {
                    "nested_list": [random.randint(1, 100) for _ in range(10)],
                    "nested_string": "A" * random.randint(10, 100),
                },
            }
            for i in range(size)
        ],
    }
    return data

def benchmark(data, iterations=1000):
    """Benchmarks json, ujson, and msgspec for dumps and loads."""

    results = {}

    # json
    json_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        json_string = json.dumps(data)
        json.loads(json_string)
        end = time.perf_counter()
        json_times.append(end - start)
    results["json"] = sum(json_times) / iterations

    # ujson
    ujson_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        ujson_string = ujson.dumps(data)
        ujson.loads(ujson_string)
        end = time.perf_counter()
        ujson_times.append(end - start)
    results["ujson"] = sum(ujson_times) / iterations

    # msgspec
    encoder = msgspec.json.Encoder()
    decoder = msgspec.json.Decoder(type=dict)
    msgspec_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        msgspec_string = encoder.encode(data)
        decoder.decode(msgspec_string)
        end = time.perf_counter()
        msgspec_times.append(end - start)
    results["msgspec"] = sum(msgspec_times) / iterations

    return results

if __name__ == "__main__":
    data = generate_complex_data(size=500)  # Adjust size for data complexity
    results = benchmark(data, iterations=1000) #adjust iterations for accuracy.

    print("Benchmark Results (average time per iteration):")
    for lib, time_taken in results.items():
        print(f"{lib}: {time_taken:.6f} seconds")

    fastest = min(results, key=results.get)
    print(f"\n{fastest} is the fastest.")

    for lib, time_taken in results.items():
        if lib != fastest:
            speedup = results[fastest] / time_taken
            print(f"{fastest} is {1/speedup:.2f} times faster than {lib}.")
