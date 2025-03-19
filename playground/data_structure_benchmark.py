import timeit
from dataclass_example import create_dataclass_instance, access_dataclass_attribute
from attrs_example import create_attrs_instance, access_attrs_attribute

# Benchmarking
num_runs = 10_000

dataclass_creation_time = timeit.timeit(create_dataclass_instance, number=num_runs)
attrs_creation_time = timeit.timeit(create_attrs_instance, number=num_runs)

dataclass_instance = create_dataclass_instance()
attrs_instance = create_attrs_instance()

dataclass_access_time = timeit.timeit(lambda: access_dataclass_attribute(dataclass_instance), number=num_runs)
attrs_access_time = timeit.timeit(lambda: access_attrs_attribute(attrs_instance), number=num_runs)

print(f"Dataclass creation time: {dataclass_creation_time:.6f} seconds")
print(f"Attrs creation time: {attrs_creation_time:.6f} seconds")
print(f"Dataclass attribute access time: {dataclass_access_time:.6f} seconds")
print(f"Attrs attribute access time: {attrs_access_time:.6f} seconds")
