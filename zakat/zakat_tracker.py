"""
'رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)' -- سورة الأعراف

```
 _____     _         _     _____               _
|__  /__ _| | ____ _| |_  |_   _| __ __ _  ___| | _____ _ __
  / // _` | |/ / _` | __|   | || '__/ _` |/ __| |/ / _ \ '__|
 / /| (_| |   < (_| | |_    | || | | (_| | (__|   <  __/ |
/____\__,_|_|\_\__,_|\__|   |_||_|  \__,_|\___|_|\_\___|_|
... Never Trust, Always Verify ...
```

This module provides a ZakatTracker class for tracking and calculating Zakat.

The ZakatTracker class allows users to record financial transactions, and calculate Zakat due based on the Nisab (the minimum threshold for Zakat) and Haul (after completing one year since every transaction received in the same account).
We use the current silver price and manage account balances.
It supports importing transactions from CSV files, exporting data to JSON format, and saving/loading the tracker state.

Key Features:

*   Tracking of positive and negative transactions
*   Calculation of Zakat based on Nisab, Haul and silver price
*   Import of transactions from CSV files
*   Export of data to JSON format
*   Persistence of tracker state using json files
*   History tracking (optional)

The module also includes a few helper functions and classes:

*   `JSONEncoder`: A custom JSON encoder for serializing enum values.
*   `Action` (Enum): An enumeration representing different actions in the tracker.
*   `MathOperation` (Enum): An enumeration representing mathematical operations in the tracker.

The ZakatTracker class is designed to be flexible and extensible, allowing users to customize it to their specific needs.

Example:

```python
from zakat_tracker import ZakatTracker

tracker = ZakatTracker()
tracker.track(10000, 'Initial deposit')
tracker.subtract(500, 'Expense')
report = tracker.check(2.5)  # Assuming silver price is 2.5 per gram
tracker.zakat(report)
```

In this file docstring:

1.  We begin with a verse from the Quran and a motivational quote.
2.  We provide a brief description of the module's purpose.
3.  We highlight the key features of the `ZakatTracker` class.
4.  We mention the additional helper functions and classes.
5.  We provide a simple usage example to illustrate how to use the `ZakatTracker` class.

Feel free to suggest any modifications or additions to tailor this file docstring to your preferences.
"""
import os
import sys
import csv
import json
import random
import datetime
import hashlib
import math
import time
import shutil
import inspect
import decimal
import enum
import pathlib
import tempfile
import dataclasses
import subprocess
import copy
import lzma
import tarfile
import io
import re
from typing import Optional
from pprint import PrettyPrinter as pp


# fix WindowsOS encoding issue
if not 'pytest' in sys.modules or sys.platform.startswith('win'): # workaround for https://github.com/pytest-dev/pytest/issues/4843
    sys.stdin.reconfigure(encoding='utf-8', errors='namereplace')
    sys.stdout.reconfigure(encoding='utf-8', errors='namereplace')


# assert is required even when option -O passed-in
failed = False
try:
    assert failed
except:
    failed = True
if not failed:
    raise AssertionError


@enum.unique
class WeekDay(enum.Enum):
    """
    Enumeration representing the days of the week.

    Members:
    - MONDAY: Represents Monday (0).
    - TUESDAY: Represents Tuesday (1).
    - WEDNESDAY: Represents Wednesday (2).
    - THURSDAY: Represents Thursday (3).
    - FRIDAY: Represents Friday (4).
    - SATURDAY: Represents Saturday (5).
    - SUNDAY: Represents Sunday (6).
    """
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@enum.unique
class Action(enum.Enum):
    """
    Enumeration representing various actions that can be performed.

    Members:
    - CREATE: Represents the creation action ('CREATE').
    - NAME: Represents the renaming action ('NAME').
    - TRACK: Represents the tracking action ('TRACK').
    - LOG: Represents the logging action ('LOG').
    - SUBTRACT: Represents the subtract action ('SUBTRACT').
    - ADD_FILE: Represents the action of adding a file ('ADD_FILE').
    - REMOVE_FILE: Represents the action of removing a file ('REMOVE_FILE').
    - BOX_TRANSFER: Represents the action of transferring a box ('BOX_TRANSFER').
    - EXCHANGE: Represents the exchange action ('EXCHANGE').
    - REPORT: Represents the reporting action ('REPORT').
    - ZAKAT: Represents a Zakat related action ('ZAKAT').
    """
    CREATE = 'CREATE'
    NAME = 'NAME'
    TRACK = 'TRACK'
    LOG = 'LOG'
    SUBTRACT = 'SUBTRACT'
    ADD_FILE = 'ADD_FILE'
    REMOVE_FILE = 'REMOVE_FILE'
    BOX_TRANSFER = 'BOX_TRANSFER'
    EXCHANGE = 'EXCHANGE'
    REPORT = 'REPORT'
    ZAKAT = 'ZAKAT'


@enum.unique
class MathOperation(enum.Enum):
    """
    Enumeration representing mathematical operations.

    Members:
    - ADDITION: Represents the addition operation ('ADDITION').
    - EQUAL: Represents the equality operation ('EQUAL').
    - SUBTRACTION: Represents the subtraction operation ('SUBTRACTION').
    """
    ADDITION = 'ADDITION'
    EQUAL = 'EQUAL'
    SUBTRACTION = 'SUBTRACTION'


def factory_value(value) -> callable:
    """
    Creates a factory function that always returns the given value.

    This is useful for providing default values in dataclasses that
    need to be callable (e.g., for default_factory).

    Parameters:
    - value: The value to be returned by the factory.

    Returns:
    - callable: A function that, when called, returns the value x.
    """
    def factory():
        return value
    return factory


class Timestamp(int):
    """Represents a timestamp as an integer, which must be greater than zero."""

    def __new__(cls, value):
        """
        Creates a new Timestamp instance.

        Parameters:
        - value (int or str): The integer value to be used as the timestamp.

        Raises:
        - TypeError: If the provided value is not an integer or a string representing an integer.
        - ValueError: If the provided value is not greater than zero.

        Returns:
        - Timestamp: A new Timestamp instance.
        """
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise TypeError(f"String value must represent an integer, instead ({type(value)}: {value}) is given.")
        if not isinstance(value, int):
            raise TypeError(f"Timestamp value must be an integer, instead ({type(value)}: {value}) is given.")

        if value <= 0:
            raise ValueError("Timestamp value must be greater than zero.")

        return super().__new__(cls, value)

    @classmethod
    def test(cls):
        """
        Runs tests for the Timestamp class to ensure it behaves correctly.
        """
        test_data = {
            123: True,
            "123": True,
            0: False,
            "0": False,
            -1: False,
            "-1": False,
            "abc": False,
            1: True,
            "1": True,
        }

        for input_value, expected_output in test_data.items():
            if expected_output:
                try:
                    timestamp = cls(input_value)
                    assert int(timestamp) == int(input_value), f"Test failed for valid input: '{input_value}'"
                except (TypeError, ValueError) as e:
                    assert False, f"Unexpected error for valid input: '{input_value}': {e}"
            else:
                try:
                    cls(input_value)
                    assert False, f"Expected error for invalid input: '{input_value}'"
                except (TypeError, ValueError):
                    pass  # Expected exception


class AccountID(str):
    """
    A class representing an Account ID, which is a string that must be a positive integer greater than zero.
    Inherits from str, so it behaves like a string.
    """

    def __new__(cls, value):
        """
        Creates a new AccountID instance.

        Parameters:
        - value (str): The string value to be used as the AccountID.

        Raises:
        - ValueError: If the provided value is not a valid AccountID.

        Returns:
        - AccountID: A new AccountID instance.
        """
        if isinstance(value, Timestamp):
            value = str(value) # convert timestamp to string
        if not cls.is_valid_account_id(value):
            raise ValueError(f"Invalid AccountID: '{value}'")
        return super().__new__(cls, value)

    @staticmethod
    def is_valid_account_id(s: str) -> bool:
        """
        Checks if a string is a valid AccountID (positive integer greater than zero).

        Parameters:
        - s (str): The string to check.

        Returns:
         - bool: True if the string is a valid AccountID, False otherwise.
        """
        if not s:
            return False

        try:
            if s[0] == '0':
                return False
            if s.startswith('-'):
                return False
            if not s.isdigit():
                return False
        except:
            pass

        try:
            num = int(s)
            return num > 0
        except ValueError:
            return False

    @classmethod
    def test(cls, debug: bool = False):
        """
        Runs tests for the AccountID class to ensure it behaves correctly.

        This method tests various valid and invalid input strings to verify that:
            - Valid AccountIDs are created successfully.
            - Invalid AccountIDs raise ValueError exceptions.
        """
        test_data = {
            "123": True,
            "0": False,
            "01": False,
            "-1": False,
            "abc": False,
            "12.3": False,
            "": False,
            "9999999999999999999999999999999999999": True,
            "1": True,
            "10": True,
            "000000000000000001": False,
            " ": False,
            "1 ": False,
            " 1": False,
            "1.0": False,
            Timestamp(12345): True, # Test timestamp input
        }

        for input_value, expected_output in test_data.items():
            if expected_output:
                try:
                    account_id = cls(input_value)
                    if debug:
                        print(f'"{str(account_id)}", "{input_value}"')
                    if isinstance(input_value, Timestamp):
                        input_value = str(input_value)
                    assert str(account_id) == input_value, f"Test failed for valid input: '{input_value}'"
                except ValueError as e:
                    assert False, f"Unexpected ValueError for valid input: '{input_value}': {e}"
            else:
                try:
                    cls(input_value)
                    assert False, f"Expected ValueError for invalid input: '{input_value}'"
                except ValueError as e:
                    pass  # Expected exception


@dataclasses.dataclass
class AccountDetails:
    """
    Details of an account.

    Attributes:
    - account_id: The unique identifier (ID) of the account.
    - account_name: Human-readable name of the account.
    - balance: The current cached balance of the account.
    """
    account_id: AccountID
    account_name: str
    balance: int


def _check_attribute(instance, name, value):
    """Raises an AttributeError if the attribute doesn't exist."""
    if name not in instance.__dataclass_fields__:
        raise AttributeError(f"Cannot set non-existent attribute '{name}'")
    object.__setattr__(instance, name, value)


@dataclasses.dataclass
class StrictDataclass:
    """A dataclass that prevents setting non-existent attributes."""
    def __setattr__(self, name: str, value: any) -> None:
        _check_attribute(self, name, value)


class ImmutableWithSelectiveFreeze:
    """
    A base class for creating immutable objects with the ability to selectively
    freeze specific fields.

    Inheriting from this class will automatically make all fields defined in
    dataclasses as frozen after initialization if their metadata contains
    `"frozen": True`. Attempting to set a value to a frozen field after
    initialization will raise a RuntimeError.

    Example:
    ```python
    @dataclasses.dataclass
    class MyObject(ImmutableWithSelectiveFreeze):
        name: str
        count: int = dataclasses.field(metadata={"frozen": True})
        description: str = "default"

    obj = MyObject(name="Test", count=5)
    print(obj.name)  # Output: Test
    print(obj.count) # Output: 5
    obj.name = "New Name" # This will work
    try:
        obj.count = 10  # This will raise a RuntimeError
    except RuntimeError as e:
        print(e)      # Output: Field 'count' is frozen!
    print(obj.description) # Output: default
    obj.description = "updated" # This will work
    ```
    """
    # Implementation based on: https://discuss.python.org/t/dataclasses-freezing-specific-fields-should-be-possible/59968/2
    def __post_init__(self):
        """
        Initializes the object and freezes fields marked with `"frozen": True`
        in their metadata.
        """
        self.__set_fields_frozen(self)

    @classmethod
    def __set_fields_frozen(cls, self):
        """
        Iterates through the dataclass fields and freezes those with the
        `"frozen": True` metadata.
        """
        flds = dataclasses.fields(cls)
        for fld in flds:
            if fld.metadata.get("frozen"):
                field_name = fld.name
                field_value = getattr(self, fld.name)
                setattr(self, f"_{fld.name}", field_value)

                def local_getter(self):
                    """Getter for the frozen field."""
                    return getattr(self, f"_{field_name}")

                def frozen(name):
                    """Creates a setter that raises a RuntimeError for frozen fields."""
                    def local_setter(self, value):
                        raise RuntimeError(f"Field '{name}' is frozen!")
                    return local_setter

                setattr(cls, field_name, property(local_getter, frozen(field_name)))


@dataclasses.dataclass
class BoxZakat(StrictDataclass):
    """
    Represents the accumulated zakat information for a financial box.

    Attributes:
    - count (int): The number of times zakat has been applied to the box.
    - last (int): The timestamp since 1AD epoch of the most recent zakat calculation.
    - total (int): The cumulative total value of zakat applied to the box.
    """
    count: int
    last: int
    total: int


@dataclasses.dataclass
class Box(
        StrictDataclass,
        # ImmutableWithSelectiveFreeze,
    ):
    """
    Represents a financial box with capital, remaining value, and zakat details.

    Attributes:
    - capital (int): The initial capital value of the box.
    - rest (int): The current remaining value within the box.
    - zakat (BoxZakat): A `BoxZakat` object containing the accumulated zakat information for the box.
    """
    capital: int #= dataclasses.field(metadata={"frozen": True})
    rest: int
    zakat: BoxZakat


@dataclasses.dataclass
class Log(StrictDataclass):
    """
    Represents a log entry for an account.

    Attributes:
    - value: The value of the log entry.
    - desc: A description of the log entry.
    - ref: An optional timestamp reference.
    - file: A dictionary mapping timestamps to file paths.
    """
    value: int
    desc: str
    ref: Optional[Timestamp]
    file: dict[Timestamp, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Account(StrictDataclass):
    """
    Represents a financial account.

    Attributes:
    - balance: The current balance of the account.
    - created: The timestamp when the account was created.
    - name: The name of the account.
    - box: A dictionary mapping timestamps to Box objects.
    - count: A counter for logs, initialized to 0.
    - log: A dictionary mapping timestamps to Log objects.
    - hide: A boolean indicating whether the account is hidden.
    - zakatable: A boolean indicating whether the account is subject to zakat.
    """
    balance: int
    created: Timestamp
    name: str = ''
    box: dict[Timestamp, Box] = dataclasses.field(default_factory=dict)
    count: int = dataclasses.field(default_factory=factory_value(0))
    log: dict[Timestamp, Log] = dataclasses.field(default_factory=dict)
    hide: bool = dataclasses.field(default_factory=factory_value(False))
    zakatable: bool = dataclasses.field(default_factory=factory_value(True))


@dataclasses.dataclass
class Exchange(StrictDataclass):
    """
    Represents an exchange rate and related information.

    Attributes:
    - rate: The exchange rate (optional).
    - description: A description of the exchange (optional).
    - time: The timestamp of the exchange (optional).
    """
    rate: Optional[float] = None
    description: Optional[str] = None
    time: Optional[Timestamp] = None


@dataclasses.dataclass
class History(StrictDataclass):
    """
    Represents a history entry for an account action.

    Attributes:
    - action: The action performed.
    - account: The ID of the account (optional).
    - ref: An optional timestamp reference.
    - file: An optional timestamp for a file.
    - key: An optional key.
    - value: An optional value.
    - math: An optional math operation.
    """
    action: Action
    account: Optional[AccountID]
    ref: Optional[Timestamp]
    file: Optional[Timestamp]
    key: Optional[str]
    value: Optional[any] # !!!
    math: Optional[MathOperation]


@dataclasses.dataclass
class BoxPlan(StrictDataclass):
    """
    Represents a plan for a box.

    Attributes:
    - box: The Box object.
    - log: The Log object.
    - exchange: The Exchange object.
    - below_nisab: A boolean indicating whether the value is below nisab.
    - total: The total value.
    - count: The count.
    - ref: The timestamp reference for related Box & Log.
    """
    box: Box
    log: Log
    exchange: Exchange
    below_nisab: bool
    total: float
    count: int
    ref: Timestamp


@dataclasses.dataclass
class ZakatSummary(StrictDataclass):
    """
    Summarizes key financial figures for a Zakat calculation.

    Attributes:
    - total_wealth (int): The total wealth collected from all rest of transactions.
    - num_wealth_items (int): The number of individual transactions contributing to the total wealth.
    - num_zakatable_items (int): The number of transactions subject to Zakat.
    - total_zakatable_amount (int): The total value of all transactions subject to Zakat.
    - total_zakat_due (int): The calculated amount of Zakat payable.
    """
    total_wealth: int = 0
    num_wealth_items: int = 0
    num_zakatable_items: int = 0
    total_zakatable_amount: int = 0
    total_zakat_due: int = 0


@dataclasses.dataclass
class ZakatReport(StrictDataclass):
    """
    Represents a Zakat report containing the calculation summary, plan, and parameters.

    Attributes:
    - created: The timestamp when the report was created.
    - valid: A boolean indicating whether the Zakat is available.
    - summary: The ZakatSummary object.
    - plan: A dictionary mapping account IDs to lists of BoxPlan objects.
    - parameters: A dictionary holding the input parameters used during the Zakat calculation.
    """
    created: Timestamp
    valid: bool
    summary: ZakatSummary
    plan: dict[AccountID, list[BoxPlan]]
    parameters: dict


@dataclasses.dataclass
class Cache(StrictDataclass):
    """
    A container for cached data related to Zakat.

    Attributes:
    - zakat: The most recent Zakat report.
    """
    zakat: Optional[ZakatReport] = None


@dataclasses.dataclass
class Vault(StrictDataclass):
    """
    Represents a vault containing accounts, exchanges, and history.

    Attributes:
    - account: A dictionary mapping account IDs to Account objects.
    - exchange: A dictionary mapping account IDs to dictionaries of timestamps and Exchange objects.
    - history: A dictionary mapping timestamps to dictionaries of History objects.
    - lock: An optional timestamp for a lock.
    - report: A dictionary mapping timestamps to tuples.
    - cache: A Cache object containing cached Zakat-related data.
    """
    account: dict[AccountID, Account] = dataclasses.field(default_factory=dict)
    exchange: dict[AccountID, dict[Timestamp, Exchange]] = dataclasses.field(default_factory=dict)
    history: dict[Timestamp, dict[Timestamp, History]] = dataclasses.field(default_factory=dict)
    lock: Optional[Timestamp] = None
    report: dict[Timestamp, ZakatReport] = dataclasses.field(default_factory=dict)
    cache: Cache = dataclasses.field(default_factory=Cache)


@dataclasses.dataclass
class AccountPaymentPart(StrictDataclass):
    """
    Represents a payment part for an account.

    Attributes:
    - balance: The balance of the payment part.
    - rate: The rate of the payment part.
    - part: The part of the payment.
    """
    balance: float
    rate: float
    part: float


@dataclasses.dataclass
class PaymentParts(StrictDataclass):
    """
    Represents payment parts for multiple accounts.

    Attributes:
    - exceed: A boolean indicating whether the payment exceeds a limit.
    - demand: The demand for payment.
    - total: The total payment.
    - account: A dictionary mapping account references to AccountPaymentPart objects.
    """
    exceed: bool
    demand: int
    total: float
    account: dict[AccountID, AccountPaymentPart] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SubtractAge(StrictDataclass):
    """
    Represents an age subtraction.

    Attributes:
    - box_ref: The timestamp reference for the box.
    - total: The total amount to subtract.
    """
    box_ref: Timestamp
    total: int


@dataclasses.dataclass
class SubtractAges(StrictDataclass, list[SubtractAge]):
    """A list of SubtractAge objects."""
    pass


@dataclasses.dataclass
class SubtractReport(StrictDataclass):
    """
    Represents a report of age subtractions.

    Attributes:
    - log_ref: The timestamp reference for the log.
    - ages: A list of SubtractAge objects.
    """
    log_ref: Timestamp
    ages: SubtractAges


@dataclasses.dataclass
class TransferTime(StrictDataclass):
    """
    Represents a transfer time.

    Attributes:
    - box_ref: The timestamp reference for the box.
    - log_ref: The timestamp reference for the log.
    """
    box_ref: Timestamp
    log_ref: Timestamp


@dataclasses.dataclass
class TransferTimes(StrictDataclass, list[TransferTime]):
    """A list of TransferTime objects."""
    pass


@dataclasses.dataclass
class TransferRecord(StrictDataclass):
    """
    Represents a transfer record.

    Attributes:
    - box_ref: The timestamp reference for the box.
    - times: A list of TransferTime objects.
    """
    box_ref: Timestamp
    times: TransferTimes


class TransferReport(StrictDataclass, list[TransferRecord]):
    """A list of TransferRecord objects."""
    pass


@dataclasses.dataclass
class ImportStatistics(StrictDataclass):
    """
    Statistics summarizing the results of an import operation.

    Attributes:
    - created (int): The number of new records successfully created.
    - found (int): The number of existing records found and potentially updated.
    - bad (int): The number of records that failed to import due to errors.
    """
    created: int
    found: int
    bad: int


@dataclasses.dataclass
class CSVRecord(StrictDataclass):
    """
    Represents a single record read from a CSV file.

    Attributes:
    - index (int): The original row number of the record in the CSV file (0-based).
    - account (str): The account identifier.
    - desc (str): A description associated with the record.
    - value (int): The numerical value of the record.
    - date (str): The date associated with the record (format may vary).
    - rate (float): A rate or factor associated with the record.
    - reference (str): An optional reference string.
    - hashed (str): A hashed representation of the record's content.
    - error (str): An error message if there was an issue processing this record.
    """
    index: int
    account: str
    desc: str
    value: int
    date: str
    rate: float
    reference: str
    hashed: str
    error: str


@dataclasses.dataclass
class ImportReport(StrictDataclass):
    """
    A report summarizing the outcome of an import operation.

    Attributes:
    - statistics (ImportStatistics): Statistical information about the import.
    - bad (list[CSVRecord]): A list of CSV records that failed to import,
                                 including any error messages.
    """
    statistics: ImportStatistics
    bad: list[CSVRecord]


@dataclasses.dataclass
class SizeInfo(StrictDataclass):
    """
    Represents size information in bytes and human-readable format.
    
    Attributes:
    - bytes (float): The size in bytes.
    - human_readable (str): The human-readable representation of the size.
    """
    bytes: float
    human_readable: str


@dataclasses.dataclass
class FileInfo(StrictDataclass):
    """
    Represents information about a file.
    
    Attributes:
    - type (str): The type of the file.
    - path (str): The full path to the file.
    - exists (bool): A boolean indicating whether the file exists.
    - size (int): The size of the file in bytes.
    - human_readable_size (str): The human-readable representation of the file size.
    """
    type: str
    path: str
    exists: bool
    size: int
    human_readable_size: str


@dataclasses.dataclass
class FileStats(StrictDataclass):
    """
    Represents statistics related to file storage.
    
    Attributes:
    - ram (:class:`SizeInfo`): Information about the RAM usage.
    - database (:class:`SizeInfo`): Information about the database size.
    """
    ram: SizeInfo
    database: SizeInfo


@dataclasses.dataclass
class TimeSummary(StrictDataclass):
    """Summary of positive, negative, and total values over a period."""
    positive: int = 0
    negative: int = 0
    total: int = 0


@dataclasses.dataclass
class Transaction(StrictDataclass):
    """Represents a single transaction record."""
    account: str
    account_id: AccountID
    desc: str
    file: dict[Timestamp, str]
    value: int
    time: Timestamp
    transfer: bool


@dataclasses.dataclass
class DailyRecords(TimeSummary, StrictDataclass):
    """Represents the records for a single day, including a summary and a list of transactions."""
    rows: list[Transaction] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Timeline(StrictDataclass):
    """Aggregated transaction data organized by daily, weekly, monthly, and yearly summaries."""
    daily: dict[str, DailyRecords] = dataclasses.field(default_factory=dict)
    weekly: dict[datetime.datetime, TimeSummary] = dataclasses.field(default_factory=dict)
    monthly: dict[str, TimeSummary] = dataclasses.field(default_factory=dict)
    yearly: dict[int, TimeSummary] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Backup:
    """
    Represents a backup of a file.

    Attributes:
    - path (str): The path to the back-up file.
    - hash (str): The hash (SHA1) of the backed-up data for integrity verification.
    """
    path: str
    hash: str


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle specific object types.

    This encoder overrides the default `default` method to serialize:
    - `Action` and `MathOperation` enums as their member names.
    - `decimal.Decimal` instances as floats.

    Example:
    ```bash
    >>> json.dumps(Action.CREATE, cls=JSONEncoder)
    'CREATE'
    >>> json.dumps(decimal.Decimal('10.5'), cls=JSONEncoder)
    '10.5'
    ```
    """
    def default(self, o):
        """
        Overrides the default `default` method to serialize specific object types.

        Parameters:
        - o: The object to serialize.

        Returns:
        - The serialized object.
        """
        if isinstance(o, (Action, MathOperation)):
            return o.name  # Serialize as the enum member's name
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, Exception):
            return str(o)
        if isinstance(o, Vault) or isinstance(o, ImportReport):
            return dataclasses.asdict(o)
        return super().default(o)


class JSONDecoder(json.JSONDecoder):
    """
    Custom JSON decoder to handle specific object types.

    This decoder overrides the `object_hook` method to deserialize:
    - Strings representing enum member names back to their respective enum values.
    - Floats back to `decimal.Decimal` instances.

    Example:
    ```bash
    >>> json.loads('{"action": "CREATE"}', cls=JSONDecoder)
    {'action': <Action.CREATE: 1>}
    >>> json.loads('{"value": 10.5}', cls=JSONDecoder)
    {'value': Decimal('10.5')}
    ```
    """
    def object_hook(self, obj):
        """
        Overrides the default `object_hook` method to deserialize specific object types.

        Parameters:
        - obj: The object to deserialize.

        Returns:
        - The deserialized object.
        """
        if isinstance(obj, str) and obj in Action.__members__:
            return Action[obj]
        if isinstance(obj, str) and obj in MathOperation.__members__:
            return MathOperation[obj]
        if isinstance(obj, float):
            return decimal.Decimal(str(obj))
        return obj


def print_stack(simple: bool = True, local: bool = False, skip_first: bool = True):
    """
    Prints the current function call stack.

    Parameters:
    - simple (bool, optional): If True, prints a simplified stack trace with filename,
        line number, and function name. If False, prints more detailed information.
        Defaults to True.
    - local (bool, optional): If True, prints the local variables for each frame in the stack.
        Defaults to False.
    - skip_first (bool, optional): If True, skips the first frame in the stack (which is
        typically the call to this function itself). Defaults to True.

    Prints:
        The function call stack to the console, with the level of detail controlled by the
        `simple` and `locals` arguments.

    Example:
        To print a simple stack trace:

    ```bash
    >>> print_stack()
    File: <filename>, Line: <line number>, Function: <function_name>
    ...

    To print a detailed stack trace with local variables:

    >>> print_stack(simple=False, locals=True)
    ----------------------------------------
    Filename: <filename>
    Line Number: <line number>
    Function Name: <function_name>
    ...
        Arguments:
        arg1 = value1
        arg2 = value2
        Local Variables:
        local_var = local_value
    ...
    ```
    """
    for frame_info in inspect.stack():
        if skip_first:
            skip_first = False
            continue
        frame = frame_info.frame
        if simple:
            print(f'File: {frame_info.filename}, Line: {frame_info.lineno}, Function: {frame_info.function}')
        else:
            print('-' * 40)  # Separator for readability
            print(f'Filename: {frame_info.filename}')
            print(f'Line Number: {frame_info.lineno}')
            print(f'Function Name: {frame_info.function}')
            print(f'Code Context: {frame_info.code_context}')
            print(f'Index in Code Context: {frame_info.index}')
            print(f'Frame Object: {frame}')

        args, varargs, keywords, values = inspect.getargvalues(frame)
        if args:
            print('  Arguments:')
            for arg in args:
                print(f'    {arg} = {values[arg]}')
        if varargs:
            print(f'  *args: {values[varargs]}')
        if keywords:
            print(f'  **kwargs: {values[keywords]}')

        if local:
            print('  Local Variables:')
            for name, value in values.items():
                print(f'    {name} = {value}')


def get_git_status() -> tuple[str, int, int]:
    """
    Retrieves the git hash of the current commit, the number of unstaged file changes and Counts the number of commits since the last git tag.

    Returns:
    - tuple: (git_hash, unstaged_changes_count, commit_count_since_last_tag) or ('', 0, 0) if an error occurs.
    """
    try:
        # Get the current git hash
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()

        # Get the status of unstaged changes
        status = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')

        # Count the number of lines, which corresponds to the number of changed files.
        unstaged_changes_count = len([line for line in status.splitlines() if not line.startswith('??')]) #exclude untracked files
        
        # Get the latest tag
        latest_tag = subprocess.check_output(['git', 'describe', '--abbrev=0', '--tags']).decode('utf-8').strip()

        # Count the commits since the latest tag
        commit_count_since_last_tag = int(subprocess.check_output(['git', 'rev-list', '--count', f'{latest_tag}..HEAD']).decode('utf-8').strip())

        return git_hash, unstaged_changes_count, commit_count_since_last_tag

    except subprocess.CalledProcessError:
        return '', 0, 0
    except FileNotFoundError:
        return '', 0, 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return '', 0, 0


def get_first_directory_inside(directory_path: str) -> str | None:
    """
    Gets the name of the first directory found immediately inside the given directory.

    Parameters:
    - directory_path: The path to the directory to inspect.

    Returns:
    - The name of the first subdirectory found, or None if no subdirectories exist.
    """
    if not os.path.isdir(directory_path):
        return None

    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            return item

    return None


class Time:
    """
    Utility class for generating and manipulating nanosecond-precision timestamps.

    This class provides static methods for converting between datetime objects and
    nanosecond-precision timestamps, ensuring uniqueness and monotonicity.
    """
    __last_time_ns = None
    __time_diff_ns = None

    @staticmethod
    def minimum_time_diff_ns() -> tuple[int, int]:
        """
        Calculates the minimum time difference between two consecutive calls to
        `Time._time()` in nanoseconds.

        This method is used internally to determine the minimum granularity of
        time measurements within the system.

        Returns:
        - tuple[int, int]:
            - The minimum time difference in nanoseconds.
            - The number of iterations required to measure the difference.
        """
        i = 0
        x = y = Time._time()
        while x == y:
            y = Time._time()
            i += 1
        return y - x, i

    @staticmethod
    def _time(now: Optional[datetime.datetime] = None) -> Timestamp:
        """
        Internal method to generate a nanosecond-precision timestamp from a datetime object.

        Parameters:
        - now (datetime.datetime, optional): The datetime object to generate the timestamp from.
        If not provided, the current datetime is used.

        Returns:
        - int: The timestamp in nanoseconds since the epoch (January 1, 1AD).
        """
        if now is None:
            now = datetime.datetime.now()
        ns_in_day = (now - now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )).total_seconds() * 10 ** 9
        return Timestamp(int(now.toordinal() * 86_400_000_000_000 + ns_in_day))

    @staticmethod
    def time(now: Optional[datetime.datetime] = None) -> Timestamp:
        """
        Generates a unique, monotonically increasing timestamp based on the provided
        datetime object or the current datetime.

        This method ensures that timestamps are unique even if called in rapid succession
        by introducing a small delay if necessary, based on the system's minimum
        time resolution.

        Parameters:
        - now (datetime.datetime, optional): The datetime object to generate the timestamp from. If not provided, the current datetime is used.

        Returns:
        - Timestamp: The unique timestamp in nanoseconds since the epoch (January 1, 1AD).
        """
        new_time = Time._time(now)
        if Time.__last_time_ns is None:
            Time.__last_time_ns = new_time
            return new_time
        while new_time == Time.__last_time_ns:
            if Time.__time_diff_ns is None:
                diff, _ = Time.minimum_time_diff_ns()
                Time.__time_diff_ns = math.ceil(diff)
            time.sleep(Time.__time_diff_ns / 1_000_000_000)
            new_time = Time._time()
        Time.__last_time_ns = new_time
        return new_time

    @staticmethod
    def time_to_datetime(ordinal_ns: Timestamp) -> datetime.datetime:
        """
        Converts a nanosecond-precision timestamp (ordinal number of nanoseconds since 1AD)
        back to a datetime object.

        Parameters:
        - ordinal_ns (Timestamp): The timestamp in nanoseconds since the epoch (January 1, 1AD).

        Returns:
        - datetime.datetime: The corresponding datetime object.
        """
        d = datetime.datetime.fromordinal(ordinal_ns // 86_400_000_000_000)
        t = datetime.timedelta(seconds=(ordinal_ns % 86_400_000_000_000) // 10 ** 9)
        return datetime.datetime.combine(d, datetime.time()) + t

    @staticmethod
    def duration_from_nanoseconds(ns: int,
                                  show_zeros_in_spoken_time: bool = False,
                                  spoken_time_separator=',',
                                  millennia: str = 'Millennia',
                                  century: str = 'Century',
                                  years: str = 'Years',
                                  days: str = 'Days',
                                  hours: str = 'Hours',
                                  minutes: str = 'Minutes',
                                  seconds: str = 'Seconds',
                                  milli_seconds: str = 'MilliSeconds',
                                  micro_seconds: str = 'MicroSeconds',
                                  nano_seconds: str = 'NanoSeconds',
                                  ) -> tuple:
        """
        REF https://github.com/JayRizzo/Random_Scripts/blob/master/time_measure.py#L106
        Convert NanoSeconds to Human Readable Time Format.
        A NanoSeconds is a unit of time in the International System of Units (SI) equal
        to one millionth (0.000001 or 10−6 or 1⁄1,000,000) of a second.
        Its symbol is μs, sometimes simplified to us when Unicode is not available.
        A microsecond is equal to 1000 nanoseconds or 1⁄1,000 of a millisecond.

        INPUT : ms (AKA: MilliSeconds)
        OUTPUT: tuple(string time_lapsed, string spoken_time) like format.
        OUTPUT Variables: time_lapsed, spoken_time

        Example  Input: duration_from_nanoseconds(ns)
        **'Millennium:Century:Years:Days:Hours:Minutes:Seconds:MilliSeconds:MicroSeconds:NanoSeconds'**
        Example Output: ('039:0001:047:325:05:02:03:456:789:012', ' 39 Millennia,    1 Century,  47 Years,  325 Days,  5 Hours,  2 Minutes,  3 Seconds,  456 MilliSeconds,  789 MicroSeconds,  12 NanoSeconds')
        duration_from_nanoseconds(1234567890123456789012)
        """
        us, ns = divmod(ns, 1000)
        ms, us = divmod(us, 1000)
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        c, y = divmod(y, 100)
        n, c = divmod(c, 10)
        time_lapsed = f'{n:03.0f}:{c:04.0f}:{y:03.0f}:{d:03.0f}:{h:02.0f}:{m:02.0f}:{s:02.0f}::{ms:03.0f}::{us:03.0f}::{ns:03.0f}'
        spoken_time_part = []
        if n > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{n: 3d} {millennia}')
        if c > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{c: 4d} {century}')
        if y > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{y: 3d} {years}')
        if d > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{d: 4d} {days}')
        if h > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{h: 2d} {hours}')
        if m > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{m: 2d} {minutes}')
        if s > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{s: 2d} {seconds}')
        if ms > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{ms: 3d} {milli_seconds}')
        if us > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{us: 3d} {micro_seconds}')
        if ns > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f'{ns: 3d} {nano_seconds}')
        return time_lapsed, spoken_time_separator.join(spoken_time_part)

    @staticmethod
    def test(debug: bool = False):
        """
        Performs unit tests to verify the correctness of the `Time` class methods.

        This method checks the conversion between datetime objects and timestamps,
        ensuring accuracy and consistency across various date ranges.

        Parameters:
        - debug (bool, optional): If True, prints the timestamp and converted datetime for each test case. Defaults to False.
        """
        test_cases = [
            datetime.datetime(1, 1, 1),
            datetime.datetime(1970, 1, 1),
            datetime.datetime(1969, 12, 31),
            datetime.datetime.now(),
            datetime.datetime(9999, 12, 31, 23, 59, 59),
        ]

        for test_date in test_cases:
            timestamp = Time.time(test_date)
            converted = Time.time_to_datetime(timestamp)
            if debug:
                print(f'{timestamp} <=> {converted}')
            assert timestamp > 0
            assert test_date.year == converted.year
            assert test_date.month == converted.month
            assert test_date.day == converted.day
            assert test_date.hour == converted.hour
            assert test_date.minute == converted.minute
            assert test_date.second in [converted.second - 1, converted.second, converted.second + 1]

        # sanity check - convert date since 1AD to 9999AD

        for year in range(1, 10_000):
            ns = Time.time(datetime.datetime.strptime(f'{year:04d}-12-30 18:30:45.906030', '%Y-%m-%d %H:%M:%S.%f'))
            date = Time.time_to_datetime(ns)
            if debug:
                print(date, date.microsecond)
            assert ns > 0
            assert date.year == year
            assert date.month == 12
            assert date.day == 30
            assert date.hour == 18
            assert date.minute == 30
            assert date.second in [44, 45]
            #assert date.microsecond == 906030


def is_number(s):
    """Checks if a string is a number (including negative numbers, decimals, and scientific notation)."""
    try:
        float(s)  # or int(s)
        return True
    except ValueError:
        return False


class ZakatTracker:
    """
    A class for tracking and calculating Zakat.

    This class provides functionalities for recording transactions, calculating Zakat due,
    and managing account balances. It also offers features like importing transactions from
    CSV files, exporting data to JSON format, and saving/loading the tracker state.

    The `ZakatTracker` class is designed to handle both positive and negative transactions,
    allowing for flexible tracking of financial activities related to Zakat. It also supports
    the concept of a 'Nisab' (minimum threshold for Zakat) and a 'haul' (complete one year for Transaction) can calculate Zakat due
    based on the current silver price.

    The class uses a json file as its database to persist the tracker state,
    ensuring data integrity across sessions. It also provides options for enabling or
    disabling history tracking, allowing users to choose their preferred level of detail.

    In addition, the `ZakatTracker` class includes various helper methods like
    `time`, `time_to_datetime`, `lock`, `free`, `recall`, `save`, `load`
    and more. These methods provide additional functionalities and flexibility
    for interacting with and managing the Zakat tracker.

    Attributes:
    - ZakatTracker.ZakatCut (function): A function to calculate the Zakat percentage.
    - ZakatTracker.TimeCycle (function): A function to determine the time cycle for Zakat.
    - ZakatTracker.Nisab (function): A function to calculate the Nisab based on the silver price.
    - ZakatTracker.Version (function): The version of the ZakatTracker class.

    Data Structure:
    
    The ZakatTracker class utilizes a nested dataclasses structure called '__vault' to store and manage data, here below is just a demonstration:

        __vault (dict):
            - account (dict):
                - {account_id} (dict):
                    - balance (int): The current balance of the account.
                    - name (str): The name of the account.
                    - created (int): The creation time for the account.
                    - box (dict): A dictionary storing transaction details.
                        - {timestamp} (dict):
                            - capital (int): The initial amount of the transaction.
                            - rest (int): The remaining amount after Zakat deductions and withdrawal.
                            - zakat (dict):
                                - count (int): The number of times Zakat has been calculated for this transaction.
                                - last (int): The timestamp of the last Zakat calculation.
                                - total (int): The total Zakat deducted from this transaction.
                    - count (int): The total number of transactions for the account.
                    - log (dict): A dictionary storing transaction logs.
                        - {timestamp} (dict):
                            - value (int): The transaction amount (positive or negative).
                            - desc (str): The description of the transaction.
                            - ref (int): The box reference (positive or None).
                            - file (dict): A dictionary storing file references associated with the transaction.
                    - hide (bool): Indicates whether the account is hidden or not.
                    - zakatable (bool): Indicates whether the account is subject to Zakat.
            - exchange (dict):
                - {account_id} (dict):
                    - {timestamps} (dict):
                        - rate (float): Exchange rate when compared to local currency.
                        - description (str): The description of the exchange rate.
            - history (dict):
                - {lock_timestamp} (dict): A list of dictionaries storing the history of actions performed.
                    - {order_timestamp} (dict):
                        - {action_dict} (dict):
                            - action (Action): The type of action (CREATE, TRACK, LOG, SUB, ADD_FILE, REMOVE_FILE, BOX_TRANSFER, EXCHANGE, REPORT, ZAKAT).
                            - account (str): The account reference associated with the action.
                            - ref (int): The reference number of the transaction.
                            - file (int): The reference number of the file (if applicable).
                            - key (str): The key associated with the action (e.g., 'rest', 'total').
                            - value (int): The value associated with the action.
                            - math (MathOperation): The mathematical operation performed (if applicable).
            - lock (int or None): The timestamp indicating the current lock status (None if not locked).
            - report (dict):
                - {timestamp} (tuple): A tuple storing Zakat report details.
    """

    @staticmethod
    def Version() -> str:
        """
        Returns the current version of the software.

        This function returns a string representing the current version of the software,
        including major, minor, and patch version numbers in the format 'X.Y.Z'.

        Returns:
        - str: The current version of the software.
        """
        version = '0.3.5'
        git_hash, unstaged_count, commit_count_since_last_tag = get_git_status()
        if git_hash and (unstaged_count > 0 or commit_count_since_last_tag > 0):
            version += f".{commit_count_since_last_tag}dev{unstaged_count}+{git_hash}"
            print(version)
        return version

    @staticmethod
    def ZakatCut(x: float) -> float:
        """
        Calculates the Zakat amount due on an asset.

        This function calculates the zakat amount due on a given asset value over one lunar year.
        Zakat is an Islamic obligatory alms-giving, calculated as a fixed percentage of an individual's wealth
        that exceeds a certain threshold (Nisab).

        Parameters:
        - x (float): The total value of the asset on which Zakat is to be calculated.

        Returns:
        - float: The amount of Zakat due on the asset, calculated as 2.5% of the asset's value.
        """
        return 0.025 * x  # Zakat Cut in one Lunar Year

    @staticmethod
    def TimeCycle(days: int = 355) -> int:
        """
        Calculates the approximate duration of a lunar year in nanoseconds.

        This function calculates the approximate duration of a lunar year based on the given number of days.
        It converts the given number of days into nanoseconds for use in high-precision timing applications.

        Parameters:
        - days (int, optional): The number of days in a lunar year. Defaults to 355,
              which is an approximation of the average length of a lunar year.

        Returns:
        - int: The approximate duration of a lunar year in nanoseconds.
        """
        return int(60 * 60 * 24 * days * 1e9)  # Lunar Year in nanoseconds

    @staticmethod
    def Nisab(gram_price: float, gram_quantity: float = 595) -> float:
        """
        Calculate the total value of Nisab (a unit of weight in Islamic jurisprudence) based on the given price per gram.

        This function calculates the Nisab value, which is the minimum threshold of wealth,
        that makes an individual liable for paying Zakat.
        The Nisab value is determined by the equivalent value of a specific amount
        of gold or silver (currently 595 grams in silver) in the local currency.

        Parameters:
        - gram_price (float): The price per gram of Nisab.
        - gram_quantity (float, optional): The quantity of grams in a Nisab. Default is 595 grams of silver.

        Returns:
        - float: The total value of Nisab based on the given price per gram.
        """
        return gram_price * gram_quantity

    @staticmethod
    def ext() -> str:
        """
        Returns the file extension used by the ZakatTracker class.

        Parameters:
        None

        Returns:
        - str: The file extension used by the ZakatTracker class, which is 'json'.
        """
        return 'json'

    __base_path = pathlib.Path("")
    __vault_path = pathlib.Path("")
    __memory_mode = False
    __debug_output: list[any] = []
    __vault: Vault

    def __init__(self, db_path: str = './zakat_db/', history_mode: bool = True):
        """
        Initialize ZakatTracker with database path and history mode.

        Parameters:
        - db_path (str, optional): The path to the database  directory. Defaults to './zakat_db/'. Use ':memory:' for an in-memory database.
        - history_mode (bool, optional): The mode for tracking history. Default is True.

        Returns:
        None
        """
        self.reset()
        self.__memory_mode = db_path == ':memory:'
        self.__history(history_mode)
        if not self.__memory_mode:
            self.path(f'{db_path}/db.{self.ext()}')

    def memory_mode(self) -> bool:
        """
        Check if the ZakatTracker is operating in memory mode.

        Returns:
        - bool: True if the database is in memory, False otherwise.
        """
        return self.__memory_mode

    def path(self, path: Optional[str] = None) -> str:
        """
        Set or get the path to the database file.

        If no path is provided, the current path is returned.
        If a path is provided, it is set as the new path.
        The function also creates the necessary directories if the provided path is a file.

        Parameters:
        - path (str, optional): The new path to the database file. If not provided, the current path is returned.

        Returns:
        - str: The current or new path to the database file.
        """
        if path is None:
            return str(self.__vault_path)
        self.__vault_path = pathlib.Path(path).resolve()
        base_path = pathlib.Path(path).resolve()
        if base_path.is_file() or base_path.suffix:
            base_path = base_path.parent
        base_path.mkdir(parents=True, exist_ok=True)
        self.__base_path = base_path
        return str(self.__vault_path)

    def base_path(self, *args) -> str:
        """
        Generate a base path by joining the provided arguments with the existing base path.

        Parameters:
        - *args (str): Variable length argument list of strings to be joined with the base path.

        Returns:
        - str: The generated base path. If no arguments are provided, the existing base path is returned.
        """
        if not args:
            return str(self.__base_path)
        filtered_args = []
        ignored_filename = None
        for arg in args:
            if pathlib.Path(arg).suffix:
                ignored_filename = arg
            else:
                filtered_args.append(arg)
        base_path = pathlib.Path(self.__base_path)
        full_path = base_path.joinpath(*filtered_args)
        full_path.mkdir(parents=True, exist_ok=True)
        if ignored_filename is not None:
            return full_path.resolve() / ignored_filename  # Join with the ignored filename
        return str(full_path.resolve())

    @staticmethod
    def scale(x: float | int | decimal.Decimal, decimal_places: int = 2) -> int:
        """
        Scales a numerical value by a specified power of 10, returning an integer.

        This function is designed to handle various numeric types (`float`, `int`, or `decimal.Decimal`) and
        facilitate precise scaling operations, particularly useful in financial or scientific calculations.

        Parameters:
        - x (float | int | decimal.Decimal): The numeric value to scale. Can be a floating-point number, integer, or decimal.
        - decimal_places (int, optional): The exponent for the scaling factor (10**y). Defaults to 2, meaning the input is scaled
            by a factor of 100 (e.g., converts 1.23 to 123).

        Returns:
        - The scaled value, rounded to the nearest integer.

        Raises:
        - TypeError: If the input `x` is not a valid numeric type.

        Examples:
        ```bash
        >>> ZakatTracker.scale(3.14159)
        314
        >>> ZakatTracker.scale(1234, decimal_places=3)
        1234000
        >>> ZakatTracker.scale(decimal.Decimal('0.005'), decimal_places=4)
        50
        ```
        """
        if not isinstance(x, (float, int, decimal.Decimal)):
            raise TypeError(f'Input "{x}" must be a float, int, or decimal.Decimal.')
        return int(decimal.Decimal(f'{x:.{decimal_places}f}') * (10 ** decimal_places))

    @staticmethod
    def unscale(x: int, return_type: type = float, decimal_places: int = 2) -> float | decimal.Decimal:
        """
        Unscales an integer by a power of 10.

        Parameters:
        - x (int): The integer to unscale.
        - return_type (type, optional): The desired type for the returned value. Can be float, int, or decimal.Decimal. Defaults to float.
        - decimal_places (int, optional): The power of 10 to use. Defaults to 2.

        Returns:
        - float | int | decimal.Decimal: The unscaled number, converted to the specified return_type.

        Raises:
        - TypeError: If the return_type is not float or decimal.Decimal.
        """
        if return_type not in (float, decimal.Decimal):
            raise TypeError(f'Invalid return_type({return_type}). Supported types are float, int, and decimal.Decimal.')
        return round(return_type(x / (10 ** decimal_places)), decimal_places)

    def reset(self) -> None:
        """
        Reset the internal data structure to its initial state.

        Parameters:
        None

        Returns:
        None
        """
        self.__vault = Vault()

    def clean_history(self, lock: Optional[Timestamp] = None) -> int:
        """
        Cleans up the empty history records of actions performed on the ZakatTracker instance.

        Parameters:
        - lock (Timestamp, optional): The lock ID is used to clean up the empty history.
            If not provided, it cleans up the empty history records for all locks.

        Returns:
        - int: The number of locks cleaned up.
        """
        count = 0
        if lock in self.__vault.history:
            if len(self.__vault.history[lock]) <= 0:
                count += 1
                del self.__vault.history[lock]
            return count
        for key in self.__vault.history:
            if len(self.__vault.history[key]) <= 0:
                count += 1
                del self.__vault.history[key]
        return count

    def __history(self, status: Optional[bool] = None) -> bool:
        """
        Enable or disable history tracking.

        Parameters:
        - status (bool, optional): The status of history tracking. Default is True.

        Returns:
        None
        """
        if status is not None:
            self.__history_mode = status
        return self.__history_mode

    def __step(self, action: Optional[Action] = None,
                    account: Optional[AccountID] = None,
                    ref: Optional[Timestamp] = None,
                    file: Optional[Timestamp] = None,
                    value: Optional[any] = None, # !!!
                    key: Optional[str] = None,
                    math_operation: Optional[MathOperation] = None,
                    lock_once: bool = True,
                    debug: bool = False,
                ) -> Optional[Timestamp]:
        """
        This method is responsible for recording the actions performed on the ZakatTracker.

        Parameters:
        - action (Action, optional): The type of action performed.
        - account (AccountID, optional): The account reference on which the action was performed.
        - ref (Optional, optional): The reference number of the action.
        - file (Timestamp, optional): The file reference number of the action.
        - value (any, optional): The value associated with the action.
        - key (str, optional): The key associated with the action.
        - math_operation (MathOperation, optional): The mathematical operation performed during the action.
        - lock_once (bool, optional): Indicates whether a lock should be acquired only once. Defaults to True.
        - debug (bool, optional): If True, the function will print debug information. Default is False.

        Returns:
        - Optional[Timestamp]: The lock time of the recorded action. If no lock was performed, it returns 0.
        """
        if not self.__history():
            return None
        no_lock = self.nolock()
        lock = self.__vault.lock
        if no_lock:
            lock = self.__vault.lock = Time.time()
            self.__vault.history[lock] = {}
        if action is None:
            if lock_once:
                assert no_lock, 'forbidden: lock called twice!!!'
            return lock
        if debug:
             print_stack()
        assert lock is not None
        assert lock > 0
        assert account is None or action != Action.REPORT
        self.__vault.history[lock][Time.time()] = History(
            action=action,
            account=account,
            ref=ref,
            file=file,
            key=key,
            value=value,
            math=math_operation,
        )
        return lock

    def nolock(self) -> bool:
        """
        Check if the vault lock is currently not set.

        Parameters:
        None

        Returns:
        - bool: True if the vault lock is not set, False otherwise.
        """
        return self.__vault.lock is None

    def __lock(self) -> Optional[Timestamp]:
        """
        Acquires a lock, potentially repeatedly, by calling the internal `_step` method.

        This method specifically invokes the `_step` method with `lock_once` set to `False`
        indicating that the lock should be acquired even if it was previously acquired.
        This is useful for ensuring a lock is held throughout a critical section of code

        Returns:
        - Optional[Timestamp]: The status code or result returned by the `_step` method, indicating theoutcome of the lock acquisition attempt.
        """
        return self.__step(lock_once=False)

    def lock(self) -> Optional[Timestamp]:
        """
        Acquires a lock on the ZakatTracker instance.

        Parameters:
        None

        Returns:
        - Optional[Timestamp]: The lock ID. This ID can be used to release the lock later.
        """
        return self.__step()

    def steps(self) -> dict:
        """
        Returns a copy of the history of steps taken in the ZakatTracker.

        The history is a dictionary where each key is a unique identifier for a step,
        and the corresponding value is a dictionary containing information about the step.

        Parameters:
        None

        Returns:
        - dict: A copy of the history of steps taken in the ZakatTracker.
        """
        return {
            lock: {
                timestamp: dataclasses.asdict(history)
                for timestamp, history in steps.items()
            }
            for lock, steps in self.__vault.history.items()
        }

    def free(self, lock: Timestamp, auto_save: bool = True) -> bool:
        """
        Releases the lock on the database.

        Parameters:
        - lock (Timestamp): The lock ID to be released.
        - auto_save (bool, optional): Whether to automatically save the database after releasing the lock.

        Returns:
        - bool: True if the lock is successfully released and (optionally) saved, False otherwise.
        """
        if lock == self.__vault.lock:
            self.clean_history(lock)
            self.__vault.lock = None
            if auto_save and not self.memory_mode():
                return self.save(self.path())
            return True
        return False

    def recall(self, dry: bool = True, lock: Optional[Timestamp] = None, debug: bool = False) -> bool:
        """
        Revert the last operation.

        Parameters:
        - dry (bool): If True, the function will not modify the data, but will simulate the operation. Default is True.
        - lock (Timestamp, optional): An optional lock value to ensure the recall
                operation is performed on the expected history entry. If provided,
                it checks if the current lock and the most recent history key
                match the given lock value. Defaults to None.
        - debug (bool, optional): If True, the function will print debug information. Default is False.

        Returns:
        - bool: True if the operation was successful, False otherwise.
        """
        if not self.nolock() or len(self.__vault.history) == 0:
            return False
        if len(self.__vault.history) <= 0:
            return False
        ref = sorted(self.__vault.history.keys())[-1]
        if debug:
            print('recall', ref)
        memory = sorted(self.__vault.history[ref], reverse=True)
        if debug:
            print(type(memory), 'memory', memory)
        if lock is not None:
            assert self.__vault.lock == lock, "Invalid current lock"
            assert ref == lock, "Invalid last lock"
            assert self.__history(), "History mode should be enabled, found off!!!"
        sub_positive_log_negative = 0
        for i in memory:
            x = self.__vault.history[ref][i]
            if debug:
                print(type(x), x)
            if x.action != Action.REPORT:
                assert x.account is not None
                if x.action != Action.EXCHANGE:
                    assert self.account_exists(x.account)
            match x.action:
                case Action.CREATE:
                    if debug:
                        print('account', self.__vault.account[x.account])
                    assert len(self.__vault.account[x.account].box) == 0
                    assert len(self.__vault.account[x.account].log) == 0
                    assert self.__vault.account[x.account].balance == 0
                    assert self.__vault.account[x.account].count == 0
                    assert self.__vault.account[x.account].name == ''
                    if dry:
                        continue
                    del self.__vault.account[x.account]

                case Action.NAME:
                    assert x.value is not None
                    if dry:
                        continue
                    self.__vault.account[x.account].name = x.value

                case Action.TRACK:
                    assert x.value is not None
                    assert x.ref is not None
                    if dry:
                        continue
                    self.__vault.account[x.account].balance -= x.value
                    self.__vault.account[x.account].count -= 1
                    del self.__vault.account[x.account].box[x.ref]

                case Action.LOG:
                    assert x.ref in self.__vault.account[x.account].log
                    assert x.value is not None
                    if dry:
                        continue
                    if sub_positive_log_negative == -x.value:
                        self.__vault.account[x.account].count -= 1
                        sub_positive_log_negative = 0
                    box_ref = self.__vault.account[x.account].log[x.ref].ref
                    if not box_ref is None:
                        assert self.box_exists(x.account, box_ref)
                        box_value = self.__vault.account[x.account].log[x.ref].value
                        assert box_value < 0

                        try:
                            self.__vault.account[x.account].box[box_ref].rest += -box_value
                        except TypeError:
                            self.__vault.account[x.account].box[box_ref].rest += decimal.Decimal(-box_value)

                        try:
                            self.__vault.account[x.account].balance += -box_value
                        except TypeError:
                            self.__vault.account[x.account].balance += decimal.Decimal(-box_value)

                        self.__vault.account[x.account].count -= 1
                    del self.__vault.account[x.account].log[x.ref]

                case Action.SUBTRACT:
                    assert x.ref in self.__vault.account[x.account].box
                    assert x.value is not None
                    if dry:
                        continue
                    self.__vault.account[x.account].box[x.ref].rest += x.value
                    self.__vault.account[x.account].balance += x.value
                    sub_positive_log_negative = x.value

                case Action.ADD_FILE:
                    assert x.ref in self.__vault.account[x.account].log
                    assert x.file is not None
                    assert dry or x.file in self.__vault.account[x.account].log[x.ref].file
                    if dry:
                        continue
                    del self.__vault.account[x.account].log[x.ref].file[x.file]

                case Action.REMOVE_FILE:
                    assert x.ref in self.__vault.account[x.account].log
                    assert x.file is not None
                    assert x.value is not None
                    if dry:
                        continue
                    self.__vault.account[x.account].log[x.ref].file[x.file] = x.value

                case Action.BOX_TRANSFER:
                    assert x.ref in self.__vault.account[x.account].box
                    assert x.value is not None
                    if dry:
                        continue
                    self.__vault.account[x.account].box[x.ref].rest -= x.value

                case Action.EXCHANGE:
                    assert x.account in self.__vault.exchange
                    assert x.ref in self.__vault.exchange[x.account]
                    if dry:
                        continue
                    del self.__vault.exchange[x.account][x.ref]

                case Action.REPORT:
                    assert x.ref in self.__vault.report
                    if dry:
                        continue
                    del self.__vault.report[x.ref]

                case Action.ZAKAT:
                    assert x.ref in self.__vault.account[x.account].box
                    assert x.key is not None
                    assert hasattr(self.__vault.account[x.account].box[x.ref].zakat, x.key)
                    if dry:
                        continue
                    match x.math:
                        case MathOperation.ADDITION:
                            setattr(
                                self.__vault.account[x.account].box[x.ref].zakat,
                                x.key,
                                getattr(self.__vault.account[x.account].box[x.ref].zakat, x.key) - x.value,
                            )
                        case MathOperation.EQUAL:
                            setattr(
                                self.__vault.account[x.account].box[x.ref].zakat,
                                x.key,
                                x.value,
                            )
                        case MathOperation.SUBTRACTION:
                            setattr(
                                self.__vault.account[x.account].box[x.ref],
                                x.key,
                                getattr(self.__vault.account[x.account].box[x.ref], x.key) + x.value,
                            )

        if not dry:
            del self.__vault.history[ref]
        return True

    def vault(self) -> dict:
        """
        Returns a copy of the internal vault dictionary.

        This method is used to retrieve the current state of the ZakatTracker object.
        It provides a snapshot of the internal data structure, allowing for further
        processing or analysis.

        Parameters:
        None

        Returns:
        - dict: A copy of the internal vault dictionary.
        """
        return dataclasses.asdict(self.__vault)

    @staticmethod
    def stats_init() -> FileStats:
        """
        Initialize and return the initial file statistics.

        Returns:
        - FileStats: A :class:`FileStats` instance with initial values
            of 0 bytes for both RAM and database.
        """
        return FileStats(
            database=SizeInfo(0, '0'),
            ram=SizeInfo(0, '0'),
        )

    def stats(self, ignore_ram: bool = True) -> FileStats:
        """
        Calculates and returns statistics about the object's data storage.

        This method determines the size of the database file on disk and the
        size of the data currently held in RAM (likely within a dictionary).
        Both sizes are reported in bytes and in a human-readable format
        (e.g., KB, MB).

        Parameters:
        - ignore_ram (bool, optional): Whether to ignore the RAM size. Default is True

        Returns:
        - FileStats: A dataclass containing the following statistics:

            * 'database': A tuple with two elements:
                - The database file size in bytes (float).
                - The database file size in human-readable format (str).
            * 'ram': A tuple with two elements:
                - The RAM usage (dictionary size) in bytes (float).
                - The RAM usage in human-readable format (str).

        Example:
        ```bash
        >>> x = ZakatTracker()
        >>> stats = x.stats()
        >>> print(stats.database)
        SizeInfo(bytes=256000, human_readable='250.0 KB')
        >>> print(stats.ram)
        SizeInfo(bytes=12345, human_readable='12.1 KB')
        ```
        """
        ram_size = 0.0 if ignore_ram else self.get_dict_size(self.vault())
        file_size = os.path.getsize(self.path())
        return FileStats(
            database=SizeInfo(file_size, self.human_readable_size(file_size)),
            ram=SizeInfo(ram_size, self.human_readable_size(ram_size)),
        )

    def files(self) -> list[FileInfo]:
        """
        Retrieves information about files associated with this class.

        This class method provides a standardized way to gather details about
        files used by the class for storage, snapshots, and CSV imports.

        Parameters:
        None

        Returns:
        - list[FileInfo]: A list of dataclass, each containing information
            about a specific file:

            * type (str): The type of file ('database', 'snapshot', 'import_csv').
            * path (str): The full file path.
            * exists (bool): Whether the file exists on the filesystem.
            * size (int): The file size in bytes (0 if the file doesn't exist).
            * human_readable_size (str): A human-friendly representation of the file size (e.g., '10 KB', '2.5 MB').
        """
        result = []
        for file_type, path in {
            'database': self.path(),
            'snapshot': self.snapshot_cache_path(),
            'import_csv': self.import_csv_cache_path(),
        }.items():
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            human_readable_size = self.human_readable_size(size) if exists else '0'
            result.append(FileInfo(
                type=file_type,
                path=path,
                exists=exists,
                size=size,
                human_readable_size=human_readable_size,
            ))
        return result

    def account_exists(self, account: AccountID) -> bool:
        """
        Check if the given account exists in the vault.

        Parameters:
        - account (AccountID): The account reference to check.

        Returns:
        - bool: True if the account exists, False otherwise.
        """
        account = AccountID(account)
        return account in self.__vault.account

    def box_size(self, account: AccountID) -> int:
        """
        Calculate the size of the box for a specific account.

        Parameters:
        - account (AccountID): The account reference for which the box size needs to be calculated.

        Returns:
        - int: The size of the box for the given account. If the account does not exist, -1 is returned.
        """
        if self.account_exists(account):
            return len(self.__vault.account[account].box)
        return -1

    def log_size(self, account: AccountID) -> int:
        """
        Get the size of the log for a specific account.

        Parameters:
        - account (AccountID): The account reference for which the log size needs to be calculated.

        Returns:
        - int: The size of the log for the given account. If the account does not exist, -1 is returned.
        """
        if self.account_exists(account):
            return len(self.__vault.account[account].log)
        return -1

    @staticmethod
    def hash_data(data: bytes, algorithm: str = 'blake2b') -> str:
        """
        Calculates the hash of given byte data using the specified algorithm.

        Parameters:
        - data (bytes): The byte data to hash.
        - algorithm (str, optional): The hashing algorithm to use. Defaults to 'blake2b'.

        Returns:
        - str: The hexadecimal representation of the data's hash.
        """
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data)
        return hash_obj.hexdigest()

    @staticmethod
    def hash_file(file_path: str, algorithm: str = 'blake2b') -> str:
        """
        Calculates the hash of a file using the specified algorithm.

        Parameters:
        - file_path (str): The path to the file.
        - algorithm (str, optional): The hashing algorithm to use. Defaults to 'blake2b'.

        Returns:
        - str: The hexadecimal representation of the file's hash.
        """
        hash_obj = hashlib.new(algorithm)  # Create the hash object
        with open(file_path, 'rb') as file:  # Open file in binary mode for reading
            for chunk in iter(lambda: file.read(4096), b''):  # Read file in chunks
                hash_obj.update(chunk)
        return hash_obj.hexdigest()  # Return the hash as a hexadecimal string

    def snapshot_cache_path(self):
        """
        Generate the path for the cache file used to store snapshots.

        The cache file is a json file that stores the timestamps of the snapshots.
        The file name is derived from the main database file name by replacing the '.json' extension with '.snapshots.json'.

        Parameters:
        None

        Returns:
        - str: The path to the cache file.
        """
        path = str(self.path())
        ext = self.ext()
        ext_len = len(ext)
        if path.endswith(f'.{ext}'):
            path = path[:-ext_len - 1]
        _, filename = os.path.split(path + f'.snapshots.{ext}')
        return self.base_path(filename)

    def snapshot(self) -> bool:
        """
        This function creates a snapshot of the current database state.

        The function calculates the hash of the current database file and checks if a snapshot with the same hash already exists.
        If a snapshot with the same hash exists, the function returns True without creating a new snapshot.
        If a snapshot with the same hash does not exist, the function creates a new snapshot by saving the current database state
        in a new json file with a unique timestamp as the file name. The function also updates the snapshot cache file with the new snapshot's hash and timestamp.

        Parameters:
        None

        Returns:
        - bool: True if a snapshot with the same hash already exists or if the snapshot is successfully created. False if the snapshot creation fails.
        """
        current_hash = self.hash_file(self.path())
        cache: dict[str, int] = {}  # hash: time_ns
        try:
            with open(self.snapshot_cache_path(), 'r', encoding='utf-8') as stream:
                cache = json.load(stream, cls=JSONDecoder)
        except:
            pass
        if current_hash in cache:
            return True
        ref = time.time_ns()
        cache[current_hash] = ref
        if not self.save(self.base_path('snapshots', f'{ref}.{self.ext()}')):
            return False
        with open(self.snapshot_cache_path(), 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(cache, cls=JSONEncoder))
        return True

    def snapshots(self, hide_missing: bool = True, verified_hash_only: bool = False) \
            -> dict[int, tuple[str, str, bool]]:
        """
        Retrieve a dictionary of snapshots, with their respective hashes, paths, and existence status.

        Parameters:
        - hide_missing (bool, optional): If True, only include snapshots that exist in the dictionary. Default is True.
        - verified_hash_only (bool, optional): If True, only include snapshots with a valid hash. Default is False.

        Returns:
        - dict[int, tuple[str, str, bool]]: A dictionary where the keys are the timestamps of the snapshots,
        and the values are tuples containing the snapshot's hash, path, and existence status.
        """
        cache: dict[str, int] = {}  # hash: time_ns
        try:
            with open(self.snapshot_cache_path(), 'r', encoding='utf-8') as stream:
                cache = json.load(stream, cls=JSONDecoder)
        except:
            pass
        if not cache:
            return {}
        result: dict[int, tuple[str, str, bool]] = {}  # time_ns: (hash, path, exists)
        for hash_file, ref in cache.items():
            path = self.base_path('snapshots', f'{ref}.{self.ext()}')
            exists = os.path.exists(path)
            valid_hash = self.hash_file(path) == hash_file if verified_hash_only else True
            if (verified_hash_only and not valid_hash) or (verified_hash_only and not exists):
                continue
            if exists or not hide_missing:
                result[ref] = (hash_file, path, exists)
        return result

    def ref_exists(self, account: AccountID, ref_type: str, ref: Timestamp) -> bool:
        """
        Check if a specific reference (transaction) exists in the vault for a given account and reference type.

        Parameters:
        - account (AccountID): The account reference for which to check the existence of the reference.
        - ref_type (str): The type of reference (e.g., 'box', 'log', etc.).
        - ref (Timestamp): The reference (transaction) number to check for existence.

        Returns:
        - bool: True if the reference exists for the given account and reference type, False otherwise.
        """
        account = AccountID(account)
        if account in self.__vault.account:
            return ref in getattr(self.__vault.account[account], ref_type)
        return False

    def box_exists(self, account: AccountID, ref: Timestamp) -> bool:
        """
        Check if a specific box (transaction) exists in the vault for a given account and reference.

        Parameters:
        - account (AccountID): The account reference for which to check the existence of the box.
        - ref (Timestamp): The reference (transaction) number to check for existence.

        Returns:
        - bool: True if the box exists for the given account and reference, False otherwise.
        """
        return self.ref_exists(account, 'box', ref)

    def track(self, unscaled_value: float | int | decimal.Decimal = 0, desc: str = '', account: AccountID = AccountID('1'),
              created_time_ns: Optional[Timestamp] = None,
              debug: bool = False) -> Optional[Timestamp]:
        """
        This function tracks a transaction for a specific account, so it do creates a new account if it doesn't exist, logs the transaction if logging is True, and updates the account's balance and box.

        Parameters:
        - unscaled_value (float | int | decimal.Decimal, optional): The value of the transaction. Default is 0.
        - desc (str, optional): The description of the transaction. Default is an empty string.
        - account (AccountID, optional): The account reference for which the transaction is being tracked. Default is '1'.
        - created_time_ns (Timestamp, optional): The timestamp of the transaction in nanoseconds since epoch(1AD). If not provided, it will be generated. Default is None.
        - debug (bool, optional): Whether to print debug information. Default is False.

        Returns:
        - Optional[Timestamp]: The timestamp of the transaction in nanoseconds since epoch(1AD).

        Raises:
        - ValueError: The created_time_ns should be greater than zero.
        - ValueError: The log transaction happened again in the same nanosecond time.
        - ValueError: The box transaction happened again in the same nanosecond time.
        """
        return self.__track(
            unscaled_value=unscaled_value,
            desc=desc,
            account=account,
            logging=True,
            created_time_ns=created_time_ns,
            debug=debug,
        )

    def __track(self, unscaled_value: float | int | decimal.Decimal = 0, desc: str = '', account: AccountID = AccountID('1'),
              logging: bool = True,
              created_time_ns: Optional[Timestamp] = None,
              debug: bool = False) -> Optional[Timestamp]:
        """
        Internal function to track a transaction.

        This function handles the core logic for tracking a transaction, including account creation, logging, and box creation.

        Parameters:
        - unscaled_value (float | int | decimal.Decimal, optional): The monetary value of the transaction. Defaults to 0.
        - desc (str, optional): A description of the transaction. Defaults to an empty string.
        - account (AccountID, optional): The reference of the account to track the transaction for. Defaults to '1'.
        - logging (bool, optional): Enables transaction logging. Defaults to True.
        - created_time_ns (Timestamp, optional): The timestamp of the transaction in nanoseconds since the epoch. If not provided, the current time is used. Defaults to None.
        - debug (bool, optional): Enables debug printing. Defaults to False.

        Returns:
        - Optional[Timestamp]: The timestamp of the transaction in nanoseconds since the epoch.

        Raises:
        - ValueError: If `created_time_ns` is not greater than zero.
        - ValueError: If a box transaction already exists for the given `account` and `created_time_ns`.
        """
        if debug:
            print('track', f'unscaled_value={unscaled_value}, debug={debug}')
        account = AccountID(account)
        if created_time_ns is None:
            created_time_ns = Time.time()
        if created_time_ns <= 0:
            raise ValueError('The created should be greater than zero.')
        no_lock = self.nolock()
        lock = self.__lock()
        if not self.account_exists(account):
            if debug:
                print(f'account {account} created')
            self.__vault.account[account] = Account(
                balance=0,
                created=created_time_ns,
            )
            self.__step(Action.CREATE, account)
        if unscaled_value == 0:
            if no_lock:
                assert lock is not None
                self.free(lock)
            return None
        value = self.scale(unscaled_value)
        if logging:
            self.__log(value=value, desc=desc, account=account, created_time_ns=created_time_ns, ref=None, debug=debug)
        if debug:
            print('create-box', created_time_ns)
        if self.box_exists(account, created_time_ns):
            raise ValueError(f'The box transaction happened again in the same nanosecond time({created_time_ns}).')
        if debug:
            print('created-box', created_time_ns)
        self.__vault.account[account].box[created_time_ns] = Box(
            capital=value,
            rest=value,
            zakat=BoxZakat(0, 0, 0),
        )
        self.__step(Action.TRACK, account, ref=created_time_ns, value=value)
        if no_lock:
            assert lock is not None
            self.free(lock)
        return created_time_ns

    def log_exists(self, account: AccountID, ref: Timestamp) -> bool:
        """
        Checks if a specific transaction log entry exists for a given account.

        Parameters:
        - account (AccountID): The account reference associated with the transaction log.
        - ref (Timestamp): The reference to the transaction log entry.

        Returns:
        - bool: True if the transaction log entry exists, False otherwise.
        """
        return self.ref_exists(account, 'log', ref)

    def __log(self, value: int, desc: str = '', account: AccountID = AccountID('1'),
             created_time_ns: Optional[Timestamp] = None,
             ref: Optional[Timestamp] = None,
             debug: bool = False) -> Timestamp:
        """
        Log a transaction into the account's log by updates the account's balance, count, and log with the transaction details.
        It also creates a step in the history of the transaction.

        Parameters:
        - value (int): The value of the transaction.
        - desc (str, optional): The description of the transaction.
        - account (AccountID, optional): The account reference to log the transaction into. Default is '1'.
        - created_time_ns (int, optional): The timestamp of the transaction in nanoseconds since epoch(1AD).
                                           If not provided, it will be generated.
        - ref (Timestamp, optional): The reference of the object.
        - debug (bool, optional): Whether to print debug information. Default is False.

        Returns:
        - Timestamp: The timestamp of the logged transaction.

        Raises:
        - ValueError: The created_time_ns should be greater than zero.
        - ValueError: The log transaction happened again in the same nanosecond time.
        """
        if debug:
            print('_log', f'debug={debug}')
        account = AccountID(account)
        if created_time_ns is None:
            created_time_ns = Time.time()
        if created_time_ns <= 0:
            raise ValueError('The created should be greater than zero.')
        try:
            self.__vault.account[account].balance += value
        except TypeError:
            self.__vault.account[account].balance += decimal.Decimal(value)
        self.__vault.account[account].count += 1
        if debug:
            print('create-log', created_time_ns)
        if self.log_exists(account, created_time_ns):
            raise ValueError(f'The log transaction happened again in the same nanosecond time({created_time_ns}).')
        if debug:
            print('created-log', created_time_ns)
        self.__vault.account[account].log[created_time_ns] = Log(
            value=value,
            desc=desc,
            ref=ref,
            file={},
        )
        self.__step(Action.LOG, account, ref=created_time_ns, value=value)
        return created_time_ns

    def exchange(self, account: AccountID, created_time_ns: Optional[Timestamp] = None,
                 rate: Optional[float] = None, description: Optional[str] = None, debug: bool = False) -> Exchange:
        """
        This method is used to record or retrieve exchange rates for a specific account.

        Parameters:
        - account (AccountID): The account reference for which the exchange rate is being recorded or retrieved.
        - created_time_ns (Timestamp, optional): The timestamp of the exchange rate. If not provided, the current timestamp will be used.
        - rate (float, optional): The exchange rate to be recorded. If not provided, the method will retrieve the latest exchange rate.
        - description (str, optional): A description of the exchange rate.
        - debug (bool, optional): Whether to print debug information. Default is False.

        Returns:
        - Exchange: A dictionary containing the latest exchange rate and its description. If no exchange rate is found,
        it returns a dictionary with default values for the rate and description.

        Raises:
        - ValueError: The created should be greater than zero.
        """
        if debug:
            print('exchange', f'debug={debug}')
        account = AccountID(account)
        if created_time_ns is None:
            created_time_ns = Time.time()
        if created_time_ns <= 0:
            raise ValueError('The created should be greater than zero.')
        if rate is not None:
            if rate <= 0:
                return Exchange()
            if account not in self.__vault.exchange:
                self.__vault.exchange[account] = {}
            if len(self.__vault.exchange[account]) == 0 and rate <= 1:
                return Exchange(time=created_time_ns, rate=1)
            no_lock = self.nolock()
            lock = self.__lock()
            self.__vault.exchange[account][created_time_ns] = Exchange(rate=rate, description=description)
            self.__step(Action.EXCHANGE, account, ref=created_time_ns, value=rate)
            if no_lock:
                assert lock is not None
                self.free(lock)
            if debug:
                print('exchange-created-1',
                      f'account: {account}, created: {created_time_ns}, rate:{rate}, description:{description}')

        if account in self.__vault.exchange:
            valid_rates = [(ts, r) for ts, r in self.__vault.exchange[account].items() if ts <= created_time_ns]
            if valid_rates:
                latest_rate = max(valid_rates, key=lambda x: x[0])
                if debug:
                    print('exchange-read-1',
                          f'account: {account}, created: {created_time_ns}, rate:{rate}, description:{description}',
                          'latest_rate', latest_rate)
                result = latest_rate[1]
                result.time = latest_rate[0]
                return result  # إرجاع قاموس يحتوي على المعدل والوصف
        if debug:
            print('exchange-read-0', f'account: {account}, created: {created_time_ns}, rate:{rate}, description:{description}')
        return Exchange(time=created_time_ns, rate=1, description=None)  # إرجاع القيمة الافتراضية مع وصف فارغ

    @staticmethod
    def exchange_calc(x: float, x_rate: float, y_rate: float) -> float:
        """
        This function calculates the exchanged amount of a currency.

        Parameters:
        - x (float): The original amount of the currency.
        - x_rate (float): The exchange rate of the original currency.
        - y_rate (float): The exchange rate of the target currency.

        Returns:
        - float: The exchanged amount of the target currency.
        """
        return (x * x_rate) / y_rate

    def exchanges(self) -> dict[AccountID, dict[Timestamp, Exchange]]:
        """
        Retrieve the recorded exchange rates for all accounts.

        Parameters:
        None

        Returns:
        - dict[AccountID, dict[Timestamp, Exchange]]: A dictionary containing all recorded exchange rates.
        The keys are account references or numbers, and the values are dictionaries containing the exchange rates.
        Each exchange rate dictionary has timestamps as keys and exchange rate details as values.
        """
        return self.__vault.exchange.copy()

    def accounts(self) -> dict[AccountID, AccountDetails]:
        """
        Returns a dictionary containing account references as keys and their respective account details as values.

        Parameters:
        None

        Returns:
        - dict[AccountID, AccountDetails]: A dictionary where keys are account references and values are their respective details.
        """
        return {
            account_id: AccountDetails(
                account_id=account_id,
                account_name=self.__vault.account[account_id].name,
                balance=self.__vault.account[account_id].balance,
            )
            for account_id in self.__vault.account
        }

    def boxes(self, account: AccountID) -> dict[Timestamp, Box]:
        """
        Retrieve the boxes (transactions) associated with a specific account.

        Parameters:
        - account (AccountID): The account reference for which to retrieve the boxes.

        Returns:
        - dict[Timestamp, Box]: A dictionary containing the boxes associated with the given account.
        If the account does not exist, an empty dictionary is returned.
        """
        if self.account_exists(account):
            return self.__vault.account[account].box
        return {}

    def logs(self, account: AccountID) -> dict[Timestamp, Log]:
        """
        Retrieve the logs (transactions) associated with a specific account.

        Parameters:
        - account (AccountID): The account reference for which to retrieve the logs.

        Returns:
        - dict[Timestamp, Log]: A dictionary containing the logs associated with the given account.
        If the account does not exist, an empty dictionary is returned.
        """
        if self.account_exists(account):
            return self.__vault.account[account].log
        return {}

    def timeline(self, weekday: WeekDay = WeekDay.FRIDAY, debug: bool = False) -> Timeline:
        """
        Aggregates transaction logs into a structured timeline.

        This method retrieves transaction logs from all accounts and organizes them
        into daily, weekly, monthly, and yearly summaries. Each level of the
        timeline includes a `TimeSummary` object with the total positive, negative,
        and overall values for that period. The daily level also includes a list
        of individual `Transaction` records.

        Parameters:
        - weekday (WeekDay, optional): The day of the week to use as the anchor
                for weekly summaries. Defaults to WeekDay.FRIDAY.
        - debug (bool, optional): If True, prints intermediate debug information
                during processing. Defaults to False.

        Returns:
        - Timeline: An object containing the aggregated transaction data, organized
                into daily, weekly, monthly, and yearly summaries. The 'daily'
                attribute is a dictionary where keys are dates (YYYY-MM-DD) and
                values are `DailyRecords` objects. The 'weekly' attribute is a
                dictionary where keys are the starting datetime of the week and
                values are `TimeSummary` objects. The 'monthly' attribute is a
                dictionary where keys are year-month strings (YYYY-MM) and values
                are `TimeSummary` objects. The 'yearly' attribute is a dictionary
                where keys are years (YYYY) and values are `TimeSummary` objects.

        Example:
        ```bash
        >>> from zakat import tracker
        >>> ledger = tracker(':memory:')
        >>> account1_id = ledger.create_account('account1')
        >>> account2_id = ledger.create_account('account2')
        >>> ledger.subtract(51, 'desc', account1_id)
        >>> ref = ledger.track(100, 'desc', account2_id)
        >>> ledger.add_file(account2_id, ref, 'file_0')
        >>> ledger.add_file(account2_id, ref, 'file_1')
        >>> ledger.add_file(account2_id, ref, 'file_2')
        >>> ledger.timeline()
        Timeline(
            daily={
                "2025-04-06": DailyRecords(
                    positive=10000,
                    negative=5100,
                    total=4900,
                    rows=[
                        Transaction(
                            account="account2",
                            account_id="63879638114290122752",
                            desc="desc2",
                            file={
                                63879638220705865728: "file_0",
                                63879638223391350784: "file_1",
                                63879638225766047744: "file_2",
                            },
                            value=10000,
                            time=63879638181936513024,
                            transfer=False,
                        ),
                        Transaction(
                            account="account1",
                            account_id="63879638104007106560",
                            desc="desc",
                            file={},
                            value=-5100,
                            time=63879638149199421440,
                            transfer=False,
                        ),
                    ],
                )
            },
            weekly={
                datetime.datetime(2025, 4, 2, 15, 56, 21): TimeSummary(
                    positive=10000, negative=0, total=10000
                ),
                datetime.datetime(2025, 4, 2, 15, 55, 49): TimeSummary(
                    positive=0, negative=5100, total=-5100
                ),
            },
            monthly={"2025-04": TimeSummary(positive=10000, negative=5100, total=4900)},
            yearly={2025: TimeSummary(positive=10000, negative=5100, total=4900)},
        )
        ```
        """
        logs: dict[Timestamp, list[Transaction]] = {}
        for account_id in self.accounts():
            for log_ref, log in self.logs(account_id).items():
                if log_ref not in logs:
                    logs[log_ref] = []
                logs[log_ref].append(Transaction(
                    account=self.name(account_id),
                    account_id=account_id,
                    desc=log.desc,
                    file=log.file,
                    value=log.value,
                    time=log_ref,
                    transfer=False,
                ))
        if debug:
            print('logs', logs)
        y = Timeline()
        for i in sorted(logs, reverse=True):
            dt = Time.time_to_datetime(i)
            daily = f'{dt.year}-{dt.month:02d}-{dt.day:02d}'
            weekly = dt - datetime.timedelta(days=weekday.value)
            monthly = f'{dt.year}-{dt.month:02d}'
            yearly = dt.year
            # daily
            if daily not in y.daily:
                y.daily[daily] = DailyRecords()
            transfer = len(logs[i]) > 1
            if debug:
                print('logs[i]', logs[i])
            for z in logs[i]:
                if debug:
                    print('z', z)
                # daily
                value = z.value
                if value > 0:
                    y.daily[daily].positive += value
                else:
                    y.daily[daily].negative += -value
                y.daily[daily].total += value
                z.transfer = transfer
                y.daily[daily].rows.append(z)
                # weekly
                if weekly not in y.weekly:
                    y.weekly[weekly] = TimeSummary()
                if value > 0:
                    y.weekly[weekly].positive += value
                else:
                    y.weekly[weekly].negative += -value
                y.weekly[weekly].total += value
                # monthly
                if monthly not in y.monthly:
                    y.monthly[monthly] = TimeSummary()
                if value > 0:
                    y.monthly[monthly].positive += value
                else:
                    y.monthly[monthly].negative += -value
                y.monthly[monthly].total += value
                # yearly
                if yearly not in y.yearly:
                    y.yearly[yearly] = TimeSummary()
                if value > 0:
                    y.yearly[yearly].positive += value
                else:
                    y.yearly[yearly].negative += -value
                y.yearly[yearly].total += value
        if debug:
            print('y', y)
        return y

    def add_file(self, account: AccountID, ref: Timestamp, path: str) -> Timestamp:
        """
        Adds a file reference to a specific transaction log entry in the vault.

        Parameters:
        - account (AccountID): The account reference associated with the transaction log.
        - ref (Timestamp): The reference to the transaction log entry.
        - path (str): The path of the file to be added.

        Returns:
        - Timestamp: The reference of the added file. If the account or transaction log entry does not exist, returns 0.
        """
        if self.account_exists(account):
            if ref in self.__vault.account[account].log:
                no_lock = self.nolock()
                lock = self.__lock()
                file_ref = Time.time()
                self.__vault.account[account].log[ref].file[file_ref] = path
                self.__step(Action.ADD_FILE, account, ref=ref, file=file_ref)
                if no_lock:
                    assert lock is not None
                    self.free(lock)
                return file_ref
        return Timestamp(0)

    def remove_file(self, account: AccountID, ref: Timestamp, file_ref: Timestamp) -> bool:
        """
        Removes a file reference from a specific transaction log entry in the vault.

        Parameters:
        - account (AccountID): The account reference associated with the transaction log.
        - ref (Timestamp): The reference to the transaction log entry.
        - file_ref (Timestamp): The reference of the file to be removed.

        Returns:
        - bool: True if the file reference is successfully removed, False otherwise.
        """
        if self.account_exists(account):
            if ref in self.__vault.account[account].log:
                if file_ref in self.__vault.account[account].log[ref].file:
                    no_lock = self.nolock()
                    lock = self.__lock()
                    x = self.__vault.account[account].log[ref].file[file_ref]
                    del self.__vault.account[account].log[ref].file[file_ref]
                    self.__step(Action.REMOVE_FILE, account, ref=ref, file=file_ref, value=x)
                    if no_lock:
                        assert lock is not None
                        self.free(lock)
                    return True
        return False

    def balance(self, account: AccountID = AccountID('1'), cached: bool = True) -> int:
        """
        Calculate and return the balance of a specific account.

        Parameters:
        - account (AccountID, optional): The account reference. Default is '1'.
        - cached (bool, optional): If True, use the cached balance. If False, calculate the balance from the box. Default is True.

        Returns:
        - int: The balance of the account.

        Notes:
        - If cached is True, the function returns the cached balance.
        - If cached is False, the function calculates the balance from the box by summing up the 'rest' values of all box items.
        """
        account = AccountID(account)
        if cached:
            return self.__vault.account[account].balance
        x = 0
        return [x := x + y.rest for y in self.__vault.account[account].box.values()][-1]

    def hide(self, account: AccountID, status: Optional[bool] = None) -> bool:
        """
        Check or set the hide status of a specific account.

        Parameters:
        - account (AccountID): The account reference.
        - status (bool, optional): The new hide status. If not provided, the function will return the current status.

        Returns:
        - bool: The current or updated hide status of the account.

        Raises:
        None

        Example:
        ```bash
        >>> tracker = ZakatTracker()
        >>> ref = tracker.track(51, 'desc', 'account1')
        >>> tracker.hide('account1')  # Set the hide status of 'account1' to True
        False
        >>> tracker.hide('account1', True)  # Set the hide status of 'account1' to True
        True
        >>> tracker.hide('account1')  # Get the hide status of 'account1' by default
        True
        >>> tracker.hide('account1', False)
        False
        ```
        """
        if self.account_exists(account):
            if status is None:
                return self.__vault.account[account].hide
            self.__vault.account[account].hide = status
            return status
        return False

    def account(self, name: str, exact: bool = True) -> Optional[AccountDetails]:
        """
        Retrieves an AccountDetails object for the first account matching the given name.

        This method searches for accounts with names that contain the provided 'name'
        (case-insensitive substring matching). If a match is found, it returns an
        AccountDetails object containing the account's ID, name and balance. If no matching
        account is found, it returns None.

        Parameters:
        - name: The name (or partial name) of the account to retrieve.
        - exact: If True, performs a case-insensitive exact match.
                 If False, performs a case-insensitive substring search.
                 Defaults to True.

        Returns:
        - AccountDetails: An AccountDetails object representing the found account, or None if no
            matching account exists.
        """
        for account_name, account_id in self.names(name).items():
            if not exact or account_name.lower() == name.lower():
                return AccountDetails(
                    account_id=account_id,
                    account_name=account_name,
                    balance=self.__vault.account[account_id].balance,
                )
        return None

    def create_account(self, name: str) -> AccountID:
        """
        Creates a new account with the given name and returns its unique ID.

        This method:
        1. Checks if an account with the same name (case-insensitive) already exists.
        2. Generates a unique `AccountID` based on the current time.
        3. Tracks the account creation internally.
        4. Sets the account's name.
        5. Verifies that the name was set correctly.
    
        Parameters:
        - name: The name of the new account.
    
        Returns:
        - AccountID: The unique `AccountID` of the newly created account.
    
        Raises:
        - AssertionError: Empty account name is forbidden.
        - AssertionError: Account name in number is forbidden.
        - AssertionError: If an account with the same name already exists (case-insensitive).
        - AssertionError: If the provided name does not match the name set for the account.
        """
        assert name.strip(), 'empty account name is forbidden'
        assert not name.isdigit() and not name.isdecimal() and not name.isnumeric() and not is_number(name), f'Account name({name}) in number is forbidden'
        account_ref = self.account(name, exact=True)
        # check if account not exists
        assert account_ref is None, f'account name({name}) already used'
        # create new account
        account_id = AccountID(Time.time())
        self.__track(0, '', account_id)
        new_name = self.name(
            account=account_id,
            new_name=name,
        )
        assert name == new_name
        return account_id

    def names(self, keyword: str = '') -> dict[str, AccountID]:
        """
        Retrieves a dictionary of account IDs and names, optionally filtered by a keyword.

        Parameters:
        - keyword: An optional string to filter account names. If provided, only accounts whose
            names contain the keyword (case-insensitive) will be included in the result.
            Defaults to an empty string, which returns all accounts.

        Returns:
        - A dictionary where keys are account names and values are AccountIDs. The dictionary
            contains only accounts that match the provided keyword (if any).
        """
        return {
            account.name: account_id
            for account_id, account in self.__vault.account.items()
            if keyword.lower() in account.name.lower()
        }

    def name(self, account: AccountID, new_name: Optional[str] = None) -> str:
        """
        Retrieves or sets the name of an account.

        Parameters:
        - account: The AccountID of the account.
        - new_name: The new name to set for the account. If None, the current name is retrieved.

        Returns:
        - The current name of the account if `new_name` is None, or the `new_name` if it is set.

        Note: Returns an empty string if the account does not exist.
        """
        if self.account_exists(account):
            if new_name is None:
                return self.__vault.account[account].name
            assert new_name != ''
            no_lock = self.nolock()
            lock = self.__lock()
            self.__step(Action.NAME, account, value=self.__vault.account[account].name)
            self.__vault.account[account].name = new_name
            if no_lock:
                    assert lock is not None
                    self.free(lock)
            return new_name
        return ''

    def zakatable(self, account: AccountID, status: Optional[bool] = None) -> bool:
        """
        Check or set the zakatable status of a specific account.

        Parameters:
        - account (AccountID): The account reference.
        - status (bool, optional): The new zakatable status. If not provided, the function will return the current status.

        Returns:
        - bool: The current or updated zakatable status of the account.

        Raises:
        None

        Example:
        ```bash
        >>> tracker = ZakatTracker()
        >>> ref = tracker.track(51, 'desc', 'account1')
        >>> tracker.zakatable('account1')  # Set the zakatable status of 'account1' to True
        True
        >>> tracker.zakatable('account1', True)  # Set the zakatable status of 'account1' to True
        True
        >>> tracker.zakatable('account1')  # Get the zakatable status of 'account1' by default
        True
        >>> tracker.zakatable('account1', False)
        False
        ```
        """
        if self.account_exists(account):
            if status is None:
                return self.__vault.account[account].zakatable
            self.__vault.account[account].zakatable = status
            return status
        return False

    def subtract(self, unscaled_value: float | int | decimal.Decimal, desc: str = '', account: AccountID = AccountID('1'),
            created_time_ns: Optional[Timestamp] = None,
            debug: bool = False) \
            -> SubtractReport:
        """
        Subtracts a specified value from an account's balance, if the amount to subtract is greater than the account's balance,
        the remaining amount will be transferred to a new transaction with a negative value.

        Parameters:
        - unscaled_value (float | int | decimal.Decimal): The amount to be subtracted.
        - desc (str, optional): A description for the transaction. Defaults to an empty string.
        - account (AccountID, optional): The account reference from which the value will be subtracted. Defaults to '1'.
        - created_time_ns (Timestamp, optional): The timestamp of the transaction in nanoseconds since epoch(1AD).
                                           If not provided, the current timestamp will be used.
        - debug (bool, optional): A flag indicating whether to print debug information. Defaults to False.

        Returns:
        - SubtractReport: A class containing the timestamp of the transaction and a list of tuples representing the age of each transaction.

        Raises:
        - ValueError: The unscaled_value should be greater than zero.
        - ValueError: The created_time_ns should be greater than zero.
        - ValueError: The box transaction happened again in the same nanosecond time.
        - ValueError: The log transaction happened again in the same nanosecond time.
        """
        if debug:
            print('sub', f'debug={debug}')
        account = AccountID(account)
        if unscaled_value <= 0:
            raise ValueError('The unscaled_value should be greater than zero.')
        if created_time_ns is None:
            created_time_ns = Time.time()
        if created_time_ns <= 0:
            raise ValueError('The created should be greater than zero.')
        no_lock = self.nolock()
        lock = self.__lock()
        self.__track(0, '', account)
        value = self.scale(unscaled_value)
        self.__log(value=-value, desc=desc, account=account, created_time_ns=created_time_ns, ref=None, debug=debug)
        ids = sorted(self.__vault.account[account].box.keys())
        limit = len(ids) + 1
        target = value
        if debug:
            print('ids', ids)
        ages = SubtractAges()
        for i in range(-1, -limit, -1):
            if target == 0:
                break
            j = ids[i]
            if debug:
                print('i', i, 'j', j)
            rest = self.__vault.account[account].box[j].rest
            if rest >= target:
                self.__vault.account[account].box[j].rest -= target
                self.__step(Action.SUBTRACT, account, ref=j, value=target)
                ages.append(SubtractAge(box_ref=j, total=target))
                target = 0
                break
            elif target > rest > 0:
                chunk = rest
                target -= chunk
                self.__vault.account[account].box[j].rest = 0
                self.__step(Action.SUBTRACT, account, ref=j, value=chunk)
                ages.append(SubtractAge(box_ref=j, total=chunk))
        if target > 0:
            self.__track(
                unscaled_value=self.unscale(-target),
                desc=desc,
                account=account,
                logging=False,
                created_time_ns=created_time_ns,
            )
            ages.append(SubtractAge(box_ref=created_time_ns, total=target))
        if no_lock:
            assert lock is not None
            self.free(lock)
        return SubtractReport(
            log_ref=created_time_ns,
            ages=ages,
        )

    def transfer(self, unscaled_amount: float | int | decimal.Decimal, from_account: AccountID, to_account: AccountID, desc: str = '',
                 created_time_ns: Optional[Timestamp] = None,
                 debug: bool = False) -> Optional[TransferReport]:
        """
        Transfers a specified value from one account to another.

        Parameters:
        - unscaled_amount (float | int | decimal.Decimal): The amount to be transferred.
        - from_account (AccountID): The account reference from which the value will be transferred.
        - to_account (AccountID): The account reference to which the value will be transferred.
        - desc (str, optional): A description for the transaction. Defaults to an empty string.
        - created_time_ns (Timestamp, optional): The timestamp of the transaction in nanoseconds since epoch(1AD). If not provided, the current timestamp will be used.
        - debug (bool, optional): A flag indicating whether to print debug information. Defaults to False.

        Returns:
        - Optional[TransferReport]: A class of timestamps corresponding to the transactions made during the transfer.

        Raises:
        - ValueError: Transfer to the same account is forbidden.
        - ValueError: The created_time_ns should be greater than zero.
        - ValueError: The box transaction happened again in the same nanosecond time.
        - ValueError: The log transaction happened again in the same nanosecond time.
        """
        if debug:
            print('transfer', f'debug={debug}')
        from_account = AccountID(from_account)
        to_account = AccountID(to_account)
        if from_account == to_account:
            raise ValueError(f'Transfer to the same account is forbidden. {to_account}')
        if unscaled_amount <= 0:
            return None
        if created_time_ns is None:
            created_time_ns = Time.time()
        if created_time_ns <= 0:
            raise ValueError('The created should be greater than zero.')
        no_lock = self.nolock()
        lock = self.__lock()
        subtract_report = self.subtract(unscaled_amount, desc, from_account, created_time_ns, debug=debug)
        source_exchange = self.exchange(from_account, created_time_ns)
        target_exchange = self.exchange(to_account, created_time_ns)

        if debug:
            print('ages', subtract_report.ages)

        transfer_report = TransferReport()
        for subtract in subtract_report.ages:
            times = TransferTimes()
            age = subtract.box_ref
            value = subtract.total
            assert source_exchange.rate is not None
            assert target_exchange.rate is not None
            target_amount = int(self.exchange_calc(value, source_exchange.rate, target_exchange.rate))
            if debug:
                print('target_amount', target_amount)
            # Perform the transfer
            if self.box_exists(to_account, age):
                if debug:
                    print('box_exists', age)
                capital = self.__vault.account[to_account].box[age].capital
                rest = self.__vault.account[to_account].box[age].rest
                if debug:
                    print(
                        f'Transfer(loop) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).')
                selected_age = age
                if rest + target_amount > capital:
                    self.__vault.account[to_account].box[age].capital += target_amount
                    selected_age = Time.time()
                self.__vault.account[to_account].box[age].rest += target_amount
                self.__step(Action.BOX_TRANSFER, to_account, ref=selected_age, value=target_amount)
                y = self.__log(value=target_amount, desc=f'TRANSFER {from_account} -> {to_account}', account=to_account,
                              created_time_ns=None, ref=None, debug=debug)
                times.append(TransferTime(box_ref=age, log_ref=y))
                continue
            if debug:
                print(
                    f'Transfer(func) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).')
            box_ref = self.__track(
                unscaled_value=self.unscale(int(target_amount)),
                desc=desc,
                account=to_account,
                logging=True,
                created_time_ns=age,
                debug=debug,
            )
            transfer_report.append(TransferRecord(
                box_ref=box_ref,
                times=times,
            ))
        if no_lock:
            assert lock is not None
            self.free(lock)
        return transfer_report
    
    def check(self,
              silver_gram_price: float,
              unscaled_nisab: Optional[float | int | decimal.Decimal] = None,
              debug: bool = False,
              created_time_ns: Optional[Timestamp] = None,
              cycle: Optional[float] = None) -> ZakatReport:
        """
        Check the eligibility for Zakat based on the given parameters.

        Parameters:
        - silver_gram_price (float): The price of a gram of silver.
        - unscaled_nisab (float | int | decimal.Decimal, optional): The minimum amount of wealth required for Zakat.
                        If not provided, it will be calculated based on the silver_gram_price.
        - debug (bool, optional): Flag to enable debug mode.
        - created_time_ns (Timestamp, optional): The current timestamp. If not provided, it will be calculated using Time.time().
        - cycle (float, optional): The time cycle for Zakat. If not provided, it will be calculated using ZakatTracker.TimeCycle().

        Returns:
        - ZakatReport: A tuple containing a boolean indicating the eligibility for Zakat,
            a list of brief statistics, and a dictionary containing the Zakat plan.
        """
        if debug:
            print('check', f'debug={debug}')
        before_parameters = {
            "silver_gram_price": silver_gram_price,
            "unscaled_nisab": unscaled_nisab,
            "debug": debug,
            "created_time_ns": created_time_ns,
            "cycle": cycle,
        }
        if created_time_ns is None:
            created_time_ns = Time.time()
        if cycle is None:
            cycle = ZakatTracker.TimeCycle()
        if unscaled_nisab is None:
            unscaled_nisab = ZakatTracker.Nisab(silver_gram_price)
        nisab = self.scale(unscaled_nisab)
        plan: dict[AccountID, list[BoxPlan]] = {}
        summary = ZakatSummary()
        below_nisab = 0
        valid = False
        after_parameters = {
            "silver_gram_price": silver_gram_price,
            "unscaled_nisab": unscaled_nisab,
            "debug": debug,
            "created_time_ns": created_time_ns,
            "cycle": cycle,
        }
        if debug:
            print('exchanges', self.exchanges())
        for x in self.__vault.account:
            if not self.zakatable(x):
                continue
            _box = self.__vault.account[x].box
            _log = self.__vault.account[x].log
            limit = len(_box) + 1
            ids = sorted(self.__vault.account[x].box.keys())
            for i in range(-1, -limit, -1):
                j = ids[i]
                rest = float(_box[j].rest)
                if rest <= 0:
                    continue
                exchange = self.exchange(x, created_time_ns=Time.time())
                assert exchange.rate is not None
                rest = ZakatTracker.exchange_calc(rest, float(exchange.rate), 1)
                summary.num_wealth_items += 1
                summary.total_wealth += rest
                epoch = (created_time_ns - j) / cycle
                if debug:
                    print(f'Epoch: {epoch}', _box[j])
                if _box[j].zakat.last > 0:
                    epoch = (created_time_ns - _box[j].zakat.last) / cycle
                if debug:
                    print(f'Epoch: {epoch}')
                epoch = math.floor(epoch)
                if debug:
                    print(f'Epoch: {epoch}', type(epoch), epoch == 0, 1 - epoch, epoch)
                if epoch == 0:
                    continue
                if debug:
                    print('Epoch - PASSED')
                summary.num_zakatable_items += 1
                summary.total_zakatable_amount += rest
                is_nisab = rest >= nisab
                total = 0
                if is_nisab:
                    for _ in range(epoch):
                        total += ZakatTracker.ZakatCut(float(rest) - float(total))
                    valid = total > 0
                elif rest > 0:
                    below_nisab += rest
                    total = ZakatTracker.ZakatCut(float(rest))
                if total > 0:
                    if x not in plan:
                        plan[x] = []
                    summary.total_zakat_due += total
                    plan[x].append(BoxPlan(
                        below_nisab=not is_nisab,
                        total=total,
                        count=epoch,
                        ref=j,
                        box=_box[j],
                        log=_log[j],
                        exchange=exchange,
                    ))
        valid = valid or below_nisab >= nisab
        if debug:
            print(f'below_nisab({below_nisab}) >= nisab({nisab})')
        report = ZakatReport(
            created=Time.time(),
            valid=valid,
            summary=summary,
            plan=plan,
            parameters={
                'before': before_parameters,
                'after': after_parameters,
            },
        )
        self.__vault.cache.zakat = report if valid else None
        return report

    def build_payment_parts(self, scaled_demand: int, positive_only: bool = True) -> PaymentParts:
        """
        Build payment parts for the Zakat distribution.

        Parameters:
        - scaled_demand (int): The total demand for payment in local currency.
        - positive_only (bool, optional): If True, only consider accounts with positive balance. Default is True.

        Returns:
        - PaymentParts: A dictionary containing the payment parts for each account. The dictionary has the following structure:
        {
            'account': {
                'account_id': {'balance': float, 'rate': float, 'part': float},
                ...
            },
            'exceed': bool,
            'demand': int,
            'total': float,
        }
        """
        total = 0.0
        parts = PaymentParts(
            account={},
            exceed=False,
            demand=int(round(scaled_demand)),
            total=0,
        )
        for x, y in self.accounts().items():
            if positive_only and y.balance <= 0:
                continue
            total += float(y.balance)
            exchange = self.exchange(x)
            parts.account[x] = AccountPaymentPart(balance=y.balance, rate=exchange.rate, part=0)
        parts.total = total
        return parts

    @staticmethod
    def check_payment_parts(parts: PaymentParts, debug: bool = False) -> int:
        """
        Checks the validity of payment parts.

        Parameters:
        - parts (dict[str, PaymentParts): A dictionary containing payment parts information.
        - debug (bool, optional): Flag to enable debug mode.

        Returns:
        - int: Returns 0 if the payment parts are valid, otherwise returns the error code.

        Error Codes:
        1: 'demand', 'account', 'total', or 'exceed' key is missing in parts.
        2: 'balance', 'rate' or 'part' key is missing in parts['account'][x].
        3: 'part' value in parts['account'][x] is less than 0.
        4: If 'exceed' is False, 'balance' value in parts['account'][x] is less than or equal to 0.
        5: If 'exceed' is False, 'part' value in parts['account'][x] is greater than 'balance' value.
        6: The sum of 'part' values in parts['account'] does not match with 'demand' value.
        """
        if debug:
            print('check_payment_parts', f'debug={debug}')
        # for i in ['demand', 'account', 'total', 'exceed']:
        #     if i not in parts:
        #         return 1
        exceed = parts.exceed
        # for j in ['balance', 'rate', 'part']:
        #     if j not in parts.account[x]:
        #         return 2
        for x in parts.account:
            if parts.account[x].part < 0:
                return 3
            if not exceed and parts.account[x].balance <= 0:
                return 4
        demand = parts.demand
        z = 0.0
        for _, y in parts.account.items():
            if not exceed and y.part > y.balance:
                return 5
            z += ZakatTracker.exchange_calc(y.part, y.rate, 1.0)
        z = round(z, 2)
        demand = round(demand, 2)
        if debug:
            print('check_payment_parts', f'z = {z}, demand = {demand}')
            print('check_payment_parts', type(z), type(demand))
            print('check_payment_parts', z != demand)
            print('check_payment_parts', str(z) != str(demand))
        if z != demand and str(z) != str(demand):
            return 6
        return 0

    def zakat(self, report: ZakatReport,
        parts: Optional[PaymentParts] = None, debug: bool = False) -> bool:
        """
        Perform Zakat calculation based on the given report and optional parts.

        Parameters:
        - report (ZakatReport): A dataclass containing the validity of the report, the report data, and the zakat plan.
        - parts (PaymentParts, optional): A dictionary containing the payment parts for the zakat.
        - debug (bool, optional): A flag indicating whether to print debug information.

        Returns:
        - bool: True if the zakat calculation is successful, False otherwise.

        Raises:
        - AssertionError: Bad Zakat report, call `check` first then call `zakat`.
        """
        if debug:
            print('zakat', f'debug={debug}')
        if not report.valid:
            return report.valid
        assert report.plan
        parts_exist = parts is not None
        if parts_exist:
            if self.check_payment_parts(parts, debug=debug) != 0:
                return False
        if debug:
            print('######### zakat #######')
            print('parts_exist', parts_exist)
        assert report == self.__vault.cache.zakat, "Bad Zakat report, call `check` first then call `zakat`"
        no_lock = self.nolock()
        lock = self.__lock()
        report_time = Time.time()
        self.__vault.report[report_time] = report
        self.__step(Action.REPORT, ref=report_time)
        created_time_ns = Time.time()
        for x in report.plan:
            target_exchange = self.exchange(x)
            if debug:
                print(report.plan[x])
                print('-------------')
                print(self.__vault.account[x].box)
            if debug:
                print('plan[x]', report.plan[x])
            for plan in report.plan[x]:
                j = plan.ref
                if debug:
                    print('j', j)
                assert j
                self.__step(Action.ZAKAT, account=x, ref=j, value=self.__vault.account[x].box[j].zakat.last,
                           key='last',
                           math_operation=MathOperation.EQUAL)
                self.__vault.account[x].box[j].zakat.last = created_time_ns
                assert target_exchange.rate is not None
                amount = ZakatTracker.exchange_calc(float(plan.total), 1, float(target_exchange.rate))
                self.__vault.account[x].box[j].zakat.total += amount
                self.__step(Action.ZAKAT, account=x, ref=j, value=amount, key='total',
                           math_operation=MathOperation.ADDITION)
                self.__vault.account[x].box[j].zakat.count += plan.count
                self.__step(Action.ZAKAT, account=x, ref=j, value=plan.count, key='count',
                           math_operation=MathOperation.ADDITION)
                if not parts_exist:
                    try:
                        self.__vault.account[x].box[j].rest -= amount
                    except TypeError:
                        self.__vault.account[x].box[j].rest -= decimal.Decimal(amount)
                    # self.__step(Action.ZAKAT, account=x, ref=j, value=amount, key='rest',
                    #            math_operation=MathOperation.SUBTRACTION)
                    self.__log(-float(amount), desc='zakat-زكاة', account=x, created_time_ns=None, ref=j, debug=debug)
        if parts_exist:
            for account, part in parts.account.items():
                if part.part == 0:
                    continue
                if debug:
                    print('zakat-part', account, part.rate)
                target_exchange = self.exchange(account)
                assert target_exchange.rate is not None
                amount = ZakatTracker.exchange_calc(part.part, part.rate, target_exchange.rate)
                unscaled_amount = self.unscale(int(amount))
                if unscaled_amount <= 0:
                    if debug:
                        print(f"The amount({unscaled_amount:.20f}) it was {amount:.20f} should be greater tha zero.")
                    continue
                self.subtract(
                    unscaled_value=unscaled_amount,
                    desc='zakat-part-دفعة-زكاة',
                    account=account,
                    debug=debug,
                )
        if no_lock:
            assert lock is not None
            self.free(lock)
        self.__vault.cache.zakat = None
        return True

    @staticmethod
    def split_at_last_symbol(data: str, symbol: str) -> tuple[str, str]:
        """Splits a string at the last occurrence of a given symbol.
    
        Parameters:
        - data (str): The input string.
        - symbol (str): The symbol to split at.
    
        Returns:
        - tuple[str, str]: A tuple containing two strings, the part before the last symbol and
            the part after the last symbol. If the symbol is not found, returns (data, "").
        """
        last_symbol_index = data.rfind(symbol)
    
        if last_symbol_index != -1:
            before_symbol = data[:last_symbol_index]
            after_symbol = data[last_symbol_index + len(symbol):]
            return before_symbol, after_symbol
        return data, ""

    def save(self, path: Optional[str] = None, hash_required: bool = True) -> bool:
        """
        Saves the ZakatTracker's current state to a json file.

        This method serializes the internal data (`__vault`).

        Parameters:
        - path (str, optional): File path for saving. Defaults to a predefined location.
        - hash_required (bool, optional): Whether to add the data integrity using a hash. Defaults to True.

        Returns:
        - bool: True if the save operation is successful, False otherwise.
        """
        if path is None:
            path = self.path()
        # first save in tmp file
        temp = f'{path}.tmp'
        try:
            with open(temp, 'w', encoding='utf-8') as stream:
                data = json.dumps(self.__vault, cls=JSONEncoder)
                stream.write(data)
                if hash_required:
                    hashed = self.hash_data(data.encode())
                    stream.write(f'//{hashed}')
            # then move tmp file to original location
            shutil.move(temp, path)
            return True
        except (IOError, OSError) as e:
            print(f'Error saving file: {e}')
            if os.path.exists(temp):
                os.remove(temp)
            return False

    @staticmethod
    def load_vault_from_json(json_string: str) -> Vault:
        """Loads a Vault dataclass from a JSON string."""
        data = json.loads(json_string)

        vault = Vault()

        # Load Accounts
        for account_reference, account_data in data.get("account", {}).items():
            account_reference = AccountID(account_reference)
            box_data = account_data.get('box', {})
            box = {
                Timestamp(ts): Box(
                    capital=box_data[str(ts)]["capital"],
                    rest=box_data[str(ts)]["rest"],
                    zakat=BoxZakat(**box_data[str(ts)]["zakat"]),
                )
                for ts in box_data
            }

            log_data = account_data.get('log', {})
            log = {Timestamp(ts): Log(
                value=log_data[str(ts)]['value'],
                desc=log_data[str(ts)]['desc'],
                ref=Timestamp(log_data[str(ts)].get('ref')) if log_data[str(ts)].get('ref') is not None else None,
                file={Timestamp(ft): fv for ft, fv in log_data[str(ts)].get('file', {}).items()},
            ) for ts in log_data}

            vault.account[account_reference] = Account(
                balance=account_data["balance"],
                created=Timestamp(account_data["created"]),
                name=account_data.get("name", ""),
                box=box,
                count=account_data.get("count", 0),
                log=log,
                hide=account_data.get("hide", False),
                zakatable=account_data.get("zakatable", True),
            )

        # Load Exchanges
        for account_reference, exchange_data in data.get("exchange", {}).items():
            account_reference = AccountID(account_reference)
            vault.exchange[account_reference] = {}
            for timestamp, exchange_details in exchange_data.items():
                vault.exchange[account_reference][Timestamp(timestamp)] = Exchange(
                    rate=exchange_details.get("rate"),
                    description=exchange_details.get("description"),
                    time=Timestamp(exchange_details.get("time")) if exchange_details.get("time") is not None else None,
                )

        # Load History
        for timestamp, history_dict in data.get("history", {}).items():
            vault.history[Timestamp(timestamp)] = {}
            for history_key, history_data in history_dict.items():
                vault.history[Timestamp(timestamp)][Timestamp(history_key)] = History(
                    action=Action(history_data["action"]),
                    account=AccountID(history_data["account"]) if history_data.get("account") is not None else None,
                    ref=Timestamp(history_data.get("ref")) if history_data.get("ref") is not None else None,
                    file=Timestamp(history_data.get("file")) if history_data.get("file") is not None else None,
                    key=history_data.get("key"),
                    value=history_data.get("value"),
                    math=MathOperation(history_data.get("math")) if history_data.get("math") is not None else None,
                )

        # Load Lock
        vault.lock = Timestamp(data["lock"]) if data.get("lock") is not None else None

        # Load Report
        for timestamp, report_data in data.get("report", {}).items():
            zakat_plan: dict[AccountID, list[BoxPlan]] = {}
            for account_reference, box_plans in report_data.get("plan", {}).items():
                account_reference = AccountID(account_reference)
                zakat_plan[account_reference] = []
                for box_plan_data in box_plans:
                    zakat_plan[account_reference].append(BoxPlan(
                        box=Box(
                            capital=box_plan_data["box"]["capital"],
                            rest=box_plan_data["box"]["rest"],
                            zakat=BoxZakat(**box_plan_data["box"]["zakat"]),
                        ),
                        log=Log(**box_plan_data["log"]),
                        exchange=Exchange(**box_plan_data["exchange"]),
                        below_nisab=box_plan_data["below_nisab"],
                        total=box_plan_data["total"],
                        count=box_plan_data["count"],
                        ref=Timestamp(box_plan_data["ref"]),
                    ))

            vault.report[Timestamp(timestamp)] = ZakatReport(
                created=report_data["created"],
                valid=report_data["valid"],
                summary=ZakatSummary(**report_data["summary"]),
                plan=zakat_plan,
                parameters=report_data["parameters"],
            )

        # Load Cache
        vault.cache = Cache()
        cache_data = data.get("cache", {})
        if "zakat" in cache_data:
            cache_zakat_data = cache_data.get("zakat", {})
            if cache_zakat_data:
                zakat_plan: dict[AccountID, list[BoxPlan]] = {}
                for account_reference, box_plans in cache_zakat_data.get("plan", {}).items():
                    account_reference = AccountID(account_reference)
                    zakat_plan[account_reference] = []
                    for box_plan_data in box_plans:
                        zakat_plan[account_reference].append(BoxPlan(
                            box=Box(
                                capital=box_plan_data["box"]["capital"],
                                rest=box_plan_data["box"]["rest"],
                                zakat=BoxZakat(**box_plan_data["box"]["zakat"]),
                            ),
                            log=Log(**box_plan_data["log"]),
                            exchange=Exchange(**box_plan_data["exchange"]),
                            below_nisab=box_plan_data["below_nisab"],
                            total=box_plan_data["total"],
                            count=box_plan_data["count"],
                            ref=Timestamp(box_plan_data["ref"]),
                        ))

                vault.cache.zakat = ZakatReport(
                    created=cache_zakat_data["created"],
                    valid=cache_zakat_data["valid"],
                    summary=ZakatSummary(**cache_zakat_data["summary"]),
                    plan=zakat_plan,
                    parameters=cache_zakat_data["parameters"],
                )

        return vault

    def load(self, path: Optional[str] = None, hash_required: bool = True, debug: bool = False) -> bool:
        """
        Load the current state of the ZakatTracker object from a json file.

        Parameters:
        - path (str, optional): The path where the json file is located. If not provided, it will use the default path.
        - hash_required (bool, optional): Whether to verify the data integrity using a hash. Defaults to True.
        - debug (bool, optional): Flag to enable debug mode.

        Returns:
        - bool: True if the load operation is successful, False otherwise.
        """
        if path is None:
            path = self.path()
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as stream:
                    file = stream.read()
                    data, hashed = self.split_at_last_symbol(file, '//')
                    if hash_required:
                        assert hashed
                        if debug:
                            print('[debug-load]', hashed)
                        new_hash = self.hash_data(data.encode())
                        if debug:
                            print('[debug-load]', new_hash)
                        assert hashed == new_hash, "Hash verification failed. File may be corrupted."
                    self.__vault = self.load_vault_from_json(data)
                return True
            else:
                print(f'File not found: {path}')
                return False
        except (IOError, OSError) as e:
            print(f'Error loading file: {e}')
            return False

    def import_csv_cache_path(self):
        """
        Generates the cache file path for imported CSV data.

        This function constructs the file path where cached data from CSV imports
        will be stored. The cache file is a json file (.json extension) appended
        to the base path of the object.

        Parameters:
        None

        Returns:
        - str: The full path to the import CSV cache file.

        Example:
        ```bash
        >>> obj = ZakatTracker('/data/reports')
        >>> obj.import_csv_cache_path()
        '/data/reports.import_csv.json'
        ```
        """
        path = str(self.path())
        ext = self.ext()
        ext_len = len(ext)
        if path.endswith(f'.{ext}'):
            path = path[:-ext_len - 1]
        _, filename = os.path.split(path + f'.import_csv.{ext}')
        return self.base_path(filename)

    @staticmethod
    def get_transaction_csv_headers() -> list[str]:
        """
        Returns a list of strings representing the headers for a transaction CSV file.

        The headers include:
        - account: The account associated with the transaction.
        - desc: A description of the transaction.
        - value: The monetary value of the transaction.
        - date: The date of the transaction.
        - rate: The applicable rate (if any) for the transaction.
        - reference: An optional reference number or identifier for the transaction.

        Returns:
        - list[str]: A list containing the CSV header strings.
        """
        return [
            "account",
            "desc",
            "value",
            "date",
            "rate",
            "reference",
        ]

    def import_csv(self, path: str = 'file.csv', scale_decimal_places: int = 0, delimiter: str = ',', debug: bool = False) -> ImportReport:
        """
        The function reads the CSV file, checks for duplicate transactions and tries it's best to creates the transactions history accordingly in the system.

        Parameters:
        - path (str, optional): The path to the CSV file. Default is 'file.csv'.
        - scale_decimal_places (int, optional): The number of decimal places to scale the value. Default is 0.
        - delimiter (str, optional): The delimiter character to use in the CSV file. Defaults to ','.
        - debug (bool, optional): A flag indicating whether to print debug information.

        Returns:
        - ImportReport: A dataclass containing the number of transactions created, the number of transactions found in the cache,
                and a dictionary of bad transactions.

        Notes:
        * Currency Pair Assumption: This function assumes that the exchange rates stored for each account
                                    are appropriate for the currency pairs involved in the conversions.
        * The exchange rate for each account is based on the last encountered transaction rate that is not equal
            to 1.0 or the previous rate for that account.
        * Those rates will be merged into the exchange rates main data, and later it will be used for all subsequent
            transactions of the same account within the whole imported and existing dataset when doing `transfer`, `check` and
            `zakat` operations.

        Example:
            The CSV file should have the following format, rate and reference are optionals per transaction:
            account, desc, value, date, rate, reference
            For example:
            safe-45, 'Some text', 34872, 1988-06-30 00:00:00.000000, 1, 6554
        """
        if debug:
            print('import_csv', f'debug={debug}')
        cache: list[int] = []
        try:
            if not self.memory_mode():
                with open(self.import_csv_cache_path(), 'r', encoding='utf-8') as stream:
                    cache = json.load(stream)
        except Exception as e:
            if debug:
                print(e)
        date_formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H%M%S.%f',
            '%Y-%m-%d',
        ]
        statistics = ImportStatistics(0, 0, 0)
        data: dict[int, list[CSVRecord]] = {}
        with open(path, newline='', encoding='utf-8') as f:
            i = 0
            for row in csv.reader(f, delimiter=delimiter):
                if debug:
                    print(f"csv_row({i})", row, type(row))
                if row == self.get_transaction_csv_headers():
                    continue
                i += 1
                hashed = hash(tuple(row))
                if hashed in cache:
                    statistics.found += 1
                    continue
                account = row[0]
                desc = row[1]
                value = float(row[2])
                rate = 1.0
                reference = ''
                if row[4:5]: # Empty list if index is out of range
                    rate = float(row[4])
                if row[5:6]:
                    reference = row[5]
                date: int = 0
                for time_format in date_formats:
                    try:
                        date_str = row[3]
                        if "." not in date_str:
                            date_str += ".000000"
                        date = Time.time(datetime.datetime.strptime(date_str, time_format))
                        break
                    except Exception as e:
                        if debug:
                            print(e)
                record = CSVRecord(
                    index=i,
                    account=account,
                    desc=desc,
                    value=value,
                    date=date,
                    rate=rate,
                    reference=reference,
                    hashed=hashed,
                    error='',
                )
                if date <= 0:
                    record.error = 'invalid date'
                    statistics.bad += 1
                if value == 0:
                    record.error = 'invalid value'
                    statistics.bad += 1
                    continue
                if date not in data:
                    data[date] = []
                data[date].append(record)

        if debug:
            print('import_csv', len(data))

        if statistics.bad > 0:
            return ImportReport(
                statistics=statistics,
                bad=[
                    item
                    for sublist in data.values()
                    for item in sublist
                    if item.error
                ],
            )

        no_lock = self.nolock()
        lock = self.__lock()
        names = self.names()

        # sync accounts
        if debug:
            print('before-names', names, len(names))
        for date, rows in sorted(data.items()):
            new_rows: list[CSVRecord] = []
            for row in rows:
                if row.account not in names:
                    account_id = self.create_account(row.account)
                    names[row.account] = account_id
                account_id = names[row.account]
                assert account_id
                row.account = account_id
                new_rows.append(row)
            assert new_rows
            assert date in data
            data[date] = new_rows
        if debug:
            print('after-names', names, len(names))
            assert names == self.names()

        # do ops
        for date, rows in sorted(data.items()):
            try:
                def process(x: CSVRecord):
                    x.value = self.unscale(
                        x.value,
                        decimal_places=scale_decimal_places,
                    ) if scale_decimal_places > 0 else x.value
                    if x.rate > 0:
                        self.exchange(account=x.account, created_time_ns=x.date, rate=x.rate)
                    if x.value > 0:
                        self.track(unscaled_value=x.value, desc=x.desc, account=x.account, created_time_ns=x.date)
                    elif x.value < 0:
                        self.subtract(unscaled_value=-x.value, desc=x.desc, account=x.account, created_time_ns=x.date)
                    return x.hashed
                len_rows = len(rows)
                # If records are found at the same time with different accounts in the same amount
                # (one positive and the other negative), this indicates it is a transfer.
                if len_rows > 2 or len_rows == 1:
                    i = 0
                    for row in rows:
                        row.date += i
                        i += 1
                        hashed = process(row)
                        assert hashed not in cache
                        cache.append(hashed)
                        statistics.created += 1
                    continue
                x1 = rows[0]
                x2 = rows[1]
                if x1.account == x2.account:
                    continue
                    # raise Exception(f'invalid transfer')
                # not transfer - same time - normal ops
                if abs(x1.value) != abs(x2.value) and x1.date == x2.date:
                    rows[1].date += 1
                    for row in rows:
                        hashed = process(row)
                        assert hashed not in cache
                        cache.append(hashed)
                        statistics.created += 1
                    continue
                if x1.rate > 0:
                    self.exchange(x1.account, created_time_ns=x1.date, rate=x1.rate)
                if x2.rate > 0:
                    self.exchange(x2.account, created_time_ns=x2.date, rate=x2.rate)
                x1.value = self.unscale(
                    x1.value,
                    decimal_places=scale_decimal_places,
                ) if scale_decimal_places > 0 else x1.value
                x2.value = self.unscale(
                    x2.value,
                    decimal_places=scale_decimal_places,
                ) if scale_decimal_places > 0 else x2.value
                # just transfer
                values = {
                    x1.value: x1.account,
                    x2.value: x2.account,
                }
                if debug:
                    print('values', values)
                if len(values) <= 1:
                    continue
                self.transfer(
                    unscaled_amount=abs(x1.value),
                    from_account=values[min(values.keys())],
                    to_account=values[max(values.keys())],
                    desc=x1.desc,
                    created_time_ns=x1.date,
                )
            except Exception as e:
                for row in rows:
                    row.error = str(e)
                break
        if not self.memory_mode():
            with open(self.import_csv_cache_path(), 'w', encoding='utf-8') as stream:
                stream.write(json.dumps(cache))
        if no_lock:
            assert lock is not None
            self.free(lock)
        report = ImportReport(
            statistics=statistics,
            bad=[
                item
                for sublist in data.values()
                for item in sublist
                if item.error
            ],
        )
        if debug:
            debug_path = f'{self.import_csv_cache_path()}.debug.json'
            with open(debug_path, 'w', encoding='utf-8') as file:
                json.dump(report, file, indent=4, cls=JSONEncoder)
                print(f'generated debug report @ `{debug_path}`...')
        return report

    ########
    # TESTS #
    #######

    @staticmethod
    def human_readable_size(size: float, decimal_places: int = 2) -> str:
        """
        Converts a size in bytes to a human-readable format (e.g., KB, MB, GB).

        This function iterates through progressively larger units of information
        (B, KB, MB, GB, etc.) and divides the input size until it fits within a
        range that can be expressed with a reasonable number before the unit.

        Parameters:
        - size (float): The size in bytes to convert.
        - decimal_places (int, optional): The number of decimal places to display
            in the result. Defaults to 2.

        Returns:
        - str: A string representation of the size in a human-readable format,
            rounded to the specified number of decimal places. For example:
                - '1.50 KB' (1536 bytes)
                - '23.00 MB' (24117248 bytes)
                - '1.23 GB' (1325899906 bytes)
        """
        if type(size) not in (float, int):
            raise TypeError('size must be a float or integer')
        if type(decimal_places) != int:
            raise TypeError('decimal_places must be an integer')
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return f'{size:.{decimal_places}f} {unit}'

    @staticmethod
    def get_dict_size(obj: dict, seen: Optional[set] = None) -> float:
        """
        Recursively calculates the approximate memory size of a dictionary and its contents in bytes.

        This function traverses the dictionary structure, accounting for the size of keys, values,
        and any nested objects. It handles various data types commonly found in dictionaries
        (e.g., lists, tuples, sets, numbers, strings) and prevents infinite recursion in case
        of circular references.

        Parameters:
        - obj (dict): The dictionary whose size is to be calculated.
        - seen (set, optional): A set used internally to track visited objects
                             and avoid circular references. Defaults to None.

        Returns:
         - float: An approximate size of the dictionary and its contents in bytes.

        Notes:
        - This function is a method of the `ZakatTracker` class and is likely used to
          estimate the memory footprint of data structures relevant to Zakat calculations.
        - The size calculation is approximate as it relies on `sys.getsizeof()`, which might
          not account for all memory overhead depending on the Python implementation.
        - Circular references are handled to prevent infinite recursion.
        - Basic numeric types (int, float, complex) are assumed to have fixed sizes.
        - String sizes are estimated based on character length and encoding.
        """
        size = 0
        if seen is None:
            seen = set()

        obj_id = id(obj)
        if obj_id in seen:
            return 0

        seen.add(obj_id)
        size += sys.getsizeof(obj)

        if isinstance(obj, dict):
            for k, v in obj.items():
                size += ZakatTracker.get_dict_size(k, seen)
                size += ZakatTracker.get_dict_size(v, seen)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for item in obj:
                size += ZakatTracker.get_dict_size(item, seen)
        elif isinstance(obj, (int, float, complex)):  # Handle numbers
            pass  # Basic numbers have a fixed size, so nothing to add here
        elif isinstance(obj, str):  # Handle strings
            size += len(obj) * sys.getsizeof(str().encode())  # Size per character in bytes
        return size

    @staticmethod
    def day_to_time(day: int, month: int = 6, year: int = 2024) -> Timestamp:  # افتراض أن الشهر هو يونيو والسنة 2024
        """
        Convert a specific day, month, and year into a timestamp.

        Parameters:
        - day (int): The day of the month.
        - month (int, optional): The month of the year. Default is 6 (June).
        - year (int, optional): The year. Default is 2024.

        Returns:
        - Timestamp: The timestamp representing the given day, month, and year.

        Note:
        - This method assumes the default month and year if not provided.
        """
        return Time.time(datetime.datetime(year, month, day))

    @staticmethod
    def generate_random_date(start_date: datetime.datetime, end_date: datetime.datetime) -> datetime.datetime:
        """
        Generate a random date between two given dates.

        Parameters:
        - start_date (datetime.datetime): The start date from which to generate a random date.
        - end_date (datetime.datetime): The end date until which to generate a random date.

        Returns:
        - datetime.datetime: A random date between the start_date and end_date.
        """
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        return start_date + datetime.timedelta(days=random_number_of_days)

    @staticmethod
    def generate_random_csv_file(path: str = 'data.csv',
                                 count: int = 1_000,
                                 with_rate: bool = False,
                                 delimiter: str = ',',
                                 debug: bool = False) -> int:
        """
        Generate a random CSV file with specified parameters.
        The function generates a CSV file at the specified path with the given count of rows.
        Each row contains a randomly generated account, description, value, and date.
        The value is randomly generated between 1000 and 100000,
        and the date is randomly generated between 1950-01-01 and 2023-12-31.
        If the row number is not divisible by 13, the value is multiplied by -1.

        Parameters:
        - path (str, optional): The path where the CSV file will be saved. Default is 'data.csv'.
        - count (int, optional): The number of rows to generate in the CSV file. Default is 1000.
        - with_rate (bool, optional): If True, a random rate between 1.2% and 12% is added. Default is False.
        - delimiter (str, optional): The delimiter character to use in the CSV file. Defaults to ','.
        - debug (bool, optional): A flag indicating whether to print debug information.

        Returns:
        - int: number of generated records.
        """
        if debug:
            print('generate_random_csv_file', f'debug={debug}')
        i = 0
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=delimiter)
            writer.writerow(ZakatTracker.get_transaction_csv_headers())
            for i in range(count):
                account = f'acc-{random.randint(1, count)}'
                desc = f'Some text {random.randint(1, count)}'
                value = random.randint(1000, 100000)
                date = ZakatTracker.generate_random_date(
                    datetime.datetime(1000, 1, 1),
                    datetime.datetime(2023, 12, 31),
                ).strftime('%Y-%m-%d %H:%M:%S.%f' if i % 2 == 0 else '%Y-%m-%d %H:%M:%S')
                if not i % 13 == 0:
                    value *= -1
                row = [account, desc, value, date]
                if with_rate:
                    rate = random.randint(1, 100) * 0.12
                    if debug:
                        print('before-append', row)
                    row.append(rate)
                    if debug:
                        print('after-append', row)
                if i % 2 == 1:
                    row += (Time.time(),)
                writer.writerow(row)
                i = i + 1
        return i

    @staticmethod
    def create_random_list(max_sum: int, min_value: int = 0, max_value: int = 10):
        """
        Creates a list of random integers whose sum does not exceed the specified maximum.

        Parameters:
        - max_sum (int): The maximum allowed sum of the list elements.
        - min_value (int, optional): The minimum possible value for an element (inclusive).
        - max_value (int, optional): The maximum possible value for an element (inclusive).

        Returns:
        - A list of random integers.
        """
        result = []
        current_sum = 0

        while current_sum < max_sum:
            # Calculate the remaining space for the next element
            remaining_sum = max_sum - current_sum
            # Determine the maximum possible value for the next element
            next_max_value = min(remaining_sum, max_value)
            # Generate a random element within the allowed range
            next_element = random.randint(min_value, next_max_value)
            result.append(next_element)
            current_sum += next_element

        return result

    def backup(self, folder_path: str, output_directory: str = "compressed", debug: bool = False) -> Optional[Backup]:
        """
        Compresses a folder into a .tar.lzma archive.

        The archive is named following a specific format:
        'zakatdb_v<version>_<YYYYMMDD_HHMMSS>_<sha1hash>.tar.lzma'.  This format
        is crucial for the `restore` function, so avoid renaming the files.

        Parameters:
        - folder_path (str): The path to the folder to be compressed.
        - output_directory (str, optional): The directory to save the compressed file.
                                        Defaults to "compressed".
        - debug (bool, optional): Whether to print debug information. Default is False.

        Returns:
        - Optional[Backup]: A Backup object containing the path to the created archive
                            and its SHA1 hash on success, None on failure.
        """
        try:
            os.makedirs(output_directory, exist_ok=True)
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create a temporary tar archive in memory to calculate the hash
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tar.add(folder_path, arcname=os.path.basename(folder_path))
            tar_buffer.seek(0)
            folder_hash = hashlib.sha1(tar_buffer.read()).hexdigest()
            output_filename = f"zakatdb_v{self.Version()}_{now}_{folder_hash}.tar.lzma"
            output_path = os.path.join(output_directory, output_filename)

            # Compress the folder to the final .tar.lzma file
            with lzma.open(output_path, "wb") as lzma_file:
                tar_buffer.seek(0)  # Reset the buffer
                with tarfile.open(fileobj=lzma_file, mode="w") as tar:
                    tar.add(folder_path, arcname=os.path.basename(folder_path))

            if debug:
                print(f"Folder '{folder_path}' has been compressed to '{output_path}'")
            return Backup(
                path=output_path,
                hash=folder_hash,
            )
        except Exception as e:
            print(f"Error during compression: {e}")
            return None

    def restore(self, tar_lzma_path: str, output_folder_path: str = "uncompressed", debug: bool = False) -> bool:
        """
        Uncompresses a .tar.lzma archive and verifies its integrity using the SHA1 hash.

        The SHA1 hash is extracted from the archive's filename, which must follow
        the format: 'zakatdb_v<version>_<YYYYMMDD_HHMMSS>_<sha1hash>.tar.lzma'.
        This format is essential for successful restoration.

        Parameters:
        - tar_lzma_path (str): The path to the .tar.lzma file.
        - output_folder_path (str, optional): The directory to extract the contents to.
                                            Defaults to "uncompressed".
        - debug (bool, optional): Whether to print debug information. Default is False.
        
        Returns:
        - bool: True if the restoration was successful and the hash matches, False otherwise.
        """
        try:
            output_folder_path = pathlib.Path(output_folder_path).resolve()
            os.makedirs(output_folder_path, exist_ok=True)
            filename = os.path.basename(tar_lzma_path)
            match = re.match(r"zakatdb_v([^_]+)_(\d{8}_\d{6})_([a-f0-9]{40})\.tar\.lzma", filename)
            if not match:
                if debug:
                    print(f"Error: Invalid filename format: '{filename}'")
                return False

            expected_hash_from_filename = match.group(3)

            with lzma.open(tar_lzma_path, "rb") as lzma_file:
                tar_buffer = io.BytesIO(lzma_file.read())  # Read the entire decompressed tar into memory
                with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
                    tar.extractall(output_folder_path)
                    tar_buffer.seek(0)  # Reset buffer to calculate hash
                    extracted_hash = hashlib.sha1(tar_buffer.read()).hexdigest()

            new_path = os.path.join(output_folder_path, get_first_directory_inside(output_folder_path))
            assert os.path.exists(os.path.join(new_path, f"db.{self.ext()}")), f"Restored db.{self.ext()} not found."
            if extracted_hash == expected_hash_from_filename:
                if debug:
                    print(f"'{filename}' has been successfully uncompressed to '{output_folder_path}' and hash verified from filename.")
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                old_path = os.path.dirname(self.path())
                tmp_path = os.path.join(os.path.dirname(old_path), "tmp_restore", now)
                if debug:
                    print('[xxx] - old_path:', old_path)
                    print('[xxx] - tmp_path:', tmp_path)
                    print('[xxx] - new_path:', new_path)
                try:
                    shutil.move(old_path, tmp_path)
                    shutil.move(new_path, old_path)
                    assert self.load()
                    shutil.rmtree(tmp_path)
                    return True
                except Exception as e:
                    print(f"Error applying the restored files: {e}")
                    shutil.move(tmp_path, old_path)
                    return False
            else:
                if debug:
                    print(f"Warning: Hash mismatch after uncompressing '{filename}'. Expected from filename: {expected_hash_from_filename}, Got: {extracted_hash}")
                # Optionally remove the extracted folder if the hash doesn't match
                # shutil.rmtree(output_folder_path, ignore_errors=True)
                return False

        except Exception as e:
            print(f"Error during uncompression or hash check: {e}")
            return False

    def _test_core(self, restore: bool = False, debug: bool = False):

        random.seed(1234567890)

        # sanity check - core

        assert sorted([6, 0, 9, 3], reverse=False) == [0, 3, 6, 9]
        assert sorted([6, 0, 9, 3], reverse=True) == [9, 6, 3, 0]
        assert sorted(
            {6: '6', 0: '0', 9: '9', 3: '3'}.items(),
            reverse=False,
        ) == [(0, '0'), (3, '3'), (6, '6'), (9, '9')]
        assert sorted(
            {6: '6', 0: '0', 9: '9', 3: '3'}.items(),
            reverse=True,
        ) == [(9, '9'), (6, '6'), (3, '3'), (0, '0')]
        assert sorted(
            {'6': 6, '0': 0, '9': 9, '3': 3}.items(),
            reverse=False,
        ) == [('0', 0), ('3', 3), ('6', 6), ('9', 9)]
        assert sorted(
            {'6': 6, '0': 0, '9': 9, '3': 3}.items(),
            reverse=True,
        ) == [('9', 9), ('6', 6), ('3', 3), ('0', 0)]

        Timestamp.test()
        AccountID.test(debug)
        Time.test(debug)

        # test to prevents setting non-existent attributes

        for cls in [
            StrictDataclass,
            BoxZakat,
            Box,
            Log,
            Account,
            Exchange,
            History,
            BoxPlan,
            ZakatSummary,
            ZakatReport,
            Vault,
            AccountPaymentPart,
            PaymentParts,
            SubtractAge,
            SubtractAges,
            SubtractReport,
            TransferTime,
            TransferTimes,
            TransferRecord,
            ImportStatistics,
            CSVRecord,
            ImportReport,
            SizeInfo,
            FileInfo,
            FileStats,
            TimeSummary,
            Transaction,
            DailyRecords,
            Timeline,
        ]:
            failed = False
            try:
                x = cls()
                x.x = 123
            except:
                failed = True
            assert failed

        # sanity check - random forward time

        xlist = []
        limit = 1000
        for _ in range(limit):
            y = Time.time()
            z = '-'
            if y not in xlist:
                xlist.append(y)
            else:
                z = 'x'
            if debug:
                print(z, y)
        xx = len(xlist)
        if debug:
            print('count', xx, ' - unique: ', (xx / limit) * 100, '%')
        assert limit == xx

        # test ZakatTracker.split_at_last_symbol

        test_cases = [
            ("This is a string @ with a symbol.", '@', ("This is a string ", " with a symbol.")),
            ("No symbol here.", '$', ("No symbol here.", "")),
            ("Multiple $ symbols $ in the string.", '$', ("Multiple $ symbols ", " in the string.")),
            ("Here is a symbol%", '%', ("Here is a symbol", "")),
            ("@only a symbol", '@', ("", "only a symbol")),
            ("", '#', ("", "")),
            ("test/test/test.txt", '/', ("test/test", "test.txt")),
            ("abc#def#ghi", "#", ("abc#def", "ghi")),
            ("abc", "#", ("abc", "")),
            ("//https://test", '//', ("//https:", "test")),
        ]
        
        for data, symbol, expected in test_cases:
            result = ZakatTracker.split_at_last_symbol(data, symbol)
            assert result == expected, f"Test failed for data='{data}', symbol='{symbol}'. Expected {expected}, got {result}"

        # human_readable_size

        assert ZakatTracker.human_readable_size(0) == '0.00 B'
        assert ZakatTracker.human_readable_size(512) == '512.00 B'
        assert ZakatTracker.human_readable_size(1023) == '1023.00 B'

        assert ZakatTracker.human_readable_size(1024) == '1.00 KB'
        assert ZakatTracker.human_readable_size(2048) == '2.00 KB'
        assert ZakatTracker.human_readable_size(5120) == '5.00 KB'

        assert ZakatTracker.human_readable_size(1024 ** 2) == '1.00 MB'
        assert ZakatTracker.human_readable_size(2.5 * 1024 ** 2) == '2.50 MB'

        assert ZakatTracker.human_readable_size(1024 ** 3) == '1.00 GB'
        assert ZakatTracker.human_readable_size(1024 ** 4) == '1.00 TB'
        assert ZakatTracker.human_readable_size(1024 ** 5) == '1.00 PB'

        assert ZakatTracker.human_readable_size(1536, decimal_places=0) == '2 KB'
        assert ZakatTracker.human_readable_size(2.5 * 1024 ** 2, decimal_places=1) == '2.5 MB'
        assert ZakatTracker.human_readable_size(1234567890, decimal_places=3) == '1.150 GB'

        try:
            # noinspection PyTypeChecker
            ZakatTracker.human_readable_size('not a number')
            assert False, 'Expected TypeError for invalid input'
        except TypeError:
            pass

        try:
            # noinspection PyTypeChecker
            ZakatTracker.human_readable_size(1024, decimal_places='not an int')
            assert False, 'Expected TypeError for invalid decimal_places'
        except TypeError:
            pass

        # get_dict_size
        assert ZakatTracker.get_dict_size({}) == sys.getsizeof({}), 'Empty dictionary size mismatch'
        assert ZakatTracker.get_dict_size({'a': 1, 'b': 2.5, 'c': True}) != sys.getsizeof({}), 'Not Empty dictionary'

        # number scale
        error = 0
        total = 0
        for sign in ['', '-']:
            for max_i, max_j, decimal_places in [
                (101, 101, 2),  # fiat currency minimum unit took 2 decimal places
                (1, 1_000, 8),  # cryptocurrency like Satoshi in Bitcoin took 8 decimal places
                (1, 1_000, 18)  # cryptocurrency like Wei in Ethereum took 18 decimal places
            ]:
                for return_type in (
                        float,
                        decimal.Decimal,
                ):
                    for i in range(max_i):
                        for j in range(max_j):
                            total += 1
                            num_str = f'{sign}{i}.{j:0{decimal_places}d}'
                            num = return_type(num_str)
                            scaled = self.scale(num, decimal_places=decimal_places)
                            unscaled = self.unscale(scaled, return_type=return_type, decimal_places=decimal_places)
                            if debug:
                                print(
                                    f'return_type: {return_type}, num_str: {num_str} - num: {num} - scaled: {scaled} - unscaled: {unscaled}')
                            if unscaled != num:
                                if debug:
                                    print('***** SCALE ERROR *****')
                                error += 1
        if debug:
            print(f'total: {total}, error({error}): {100 * error / total}%')
        assert error == 0

        # test lock

        assert self.nolock()
        assert self.__history() is True
        lock = self.lock()
        assert lock is not None
        assert lock > 0
        failed = False
        try:
            self.lock()
        except:
            failed = True
        assert failed
        assert self.free(lock)
        assert not self.free(lock)

        wallet_account_id = self.create_account('wallet')

        table = {
            AccountID('1'): [
                (0, 10, 1000, 1000, 1000, 1, 1),
                (0, 20, 3000, 3000, 3000, 2, 2),
                (0, 30, 6000, 6000, 6000, 3, 3),
                (1, 15, 4500, 4500, 4500, 3, 4),
                (1, 50, -500, -500, -500, 4, 5),
                (1, 100, -10500, -10500, -10500, 5, 6),
            ],
            wallet_account_id: [
                (1, 90, -9000, -9000, -9000, 1, 1),
                (0, 100, 1000, 1000, 1000, 2, 2),
                (1, 190, -18000, -18000, -18000, 3, 3),
                (0, 1000, 82000, 82000, 82000, 4, 4),
            ],
        }
        for x in table:
            for y in table[x]:
                lock = self.lock()
                if y[0] == 0:
                    ref = self.track(
                        unscaled_value=y[1],
                        desc='test-add',
                        account=x,
                        created_time_ns=Time.time(),
                        debug=debug,
                    )
                else:
                    report = self.subtract(
                        unscaled_value=y[1],
                        desc='test-sub',
                        account=x,
                        created_time_ns=Time.time(),
                    )
                    ref = report.log_ref
                    if debug:
                        print('_sub', z, Time.time())
                assert ref != 0
                assert len(self.__vault.account[x].log[ref].file) == 0
                for i in range(3):
                    file_ref = self.add_file(x, ref, 'file_' + str(i))
                    assert file_ref != 0
                    if debug:
                        print('ref', ref, 'file', file_ref)
                    assert len(self.__vault.account[x].log[ref].file) == i + 1
                    assert file_ref in self.__vault.account[x].log[ref].file
                file_ref = self.add_file(x, ref, 'file_' + str(3))
                assert self.remove_file(x, ref, file_ref)
                timeline = self.timeline(debug=debug)
                if debug:
                    print('timeline', timeline)
                assert timeline.daily
                assert timeline.weekly
                assert timeline.monthly
                assert timeline.yearly
                z = self.balance(x)
                if debug:
                    print('debug-0', z, y)
                assert z == y[2]
                z = self.balance(x, False)
                if debug:
                    print('debug-1', z, y[3])
                assert z == y[3]
                o = self.__vault.account[x].log
                z = 0
                for i in o:
                    z += o[i].value
                if debug:
                    print('debug-2', z, type(z))
                    print('debug-2', y[4], type(y[4]))
                assert z == y[4]
                if debug:
                    print('debug-2 - PASSED')
                assert self.box_size(x) == y[5]
                assert self.log_size(x) == y[6]
                assert not self.nolock()
                assert lock is not None
                self.free(lock)
                assert self.nolock()
            assert self.boxes(x) != {}
            assert self.logs(x) != {}

            assert not self.hide(x)
            assert self.hide(x, False) is False
            assert self.hide(x) is False
            assert self.hide(x, True)
            assert self.hide(x)

            assert self.zakatable(x)
            assert self.zakatable(x, False) is False
            assert self.zakatable(x) is False
            assert self.zakatable(x, True)
            assert self.zakatable(x)

        if restore is True:
            # invalid restore point
            for lock in [0, time.time_ns(), Time.time()]:
                failed = False
                try:
                    self.recall(dry=True, lock=lock)
                except:
                    failed = True
                assert failed
            count = len(self.__vault.history)
            if debug:
                print('history-count', count)
            assert count == 12
            # try mode
            for _ in range(count):
                assert self.recall(dry=True, debug=debug)
            count = len(self.__vault.history)
            if debug:
                print('history-count', count)
            assert count == 12
            _accounts = list(table.keys())
            accounts_limit = len(_accounts) + 1
            for i in range(-1, -accounts_limit, -1):
                account = _accounts[i]
                if debug:
                    print(account, len(table[account]))
                transaction_limit = len(table[account]) + 1
                for j in range(-1, -transaction_limit, -1):
                    row = table[account][j]
                    if debug:
                        print(row, self.balance(account), self.balance(account, False))
                    assert self.balance(account) == self.balance(account, False)
                    assert self.balance(account) == row[2]
                    assert self.recall(dry=False, debug=debug)
            assert self.recall(dry=False, debug=debug)
            assert self.recall(dry=False, debug=debug)
            assert not self.recall(dry=False, debug=debug)
            count = len(self.__vault.history)
            if debug:
                print('history-count', count)
            assert count == 0
            self.reset()

    def _test_storage(self, account_id: Optional[AccountID] = None, debug: bool = False):
        old_vault = dataclasses.replace(self.__vault)
        old_vault_deep = copy.deepcopy(self.__vault)
        old_vault_dict = dataclasses.asdict(self.__vault)
        _path = self.path(f'./zakat_test_db/test.{self.ext()}')
        if os.path.exists(_path):
            os.remove(_path)
        for hashed in [False, True]:
            self.save(hash_required=hashed)
            assert os.path.getsize(_path) > 0
            self.reset()
            assert self.recall(dry=False, debug=debug) is False
            for hash_required in [False, True]:
                if debug:
                    print(f'[storage] save({hashed}) and load({hash_required}) = {hashed and hash_required}')
                self.load(hash_required=hashed and hash_required)
                if debug:
                    print('[debug]', type(self.__vault))
                assert self.__vault.account is not None
                assert old_vault == self.__vault
                assert old_vault_deep == self.__vault
                assert old_vault_dict == dataclasses.asdict(self.__vault)
                if account_id is not None:
                    # corrupt the data
                    log_ref = None
                    tmp_file_ref = Time.time()
                    for k in self.__vault.account[account_id].log:
                        log_ref = k
                        self.__vault.account[account_id].log[k].file[tmp_file_ref] = 'HACKED'
                        break
                    assert old_vault != self.__vault
                    assert old_vault_deep != self.__vault
                    assert old_vault_dict != dataclasses.asdict(self.__vault)
                    # fix the data
                    del self.__vault.account[account_id].log[log_ref].file[tmp_file_ref]
                    assert old_vault == self.__vault
                    assert old_vault_deep == self.__vault
                    assert old_vault_dict == dataclasses.asdict(self.__vault)
            if hashed:
                continue
            failed = False
            try:
                hash_required = True
                if debug:
                    print(f'x [storage] save({hashed}) and load({hash_required}) = {hashed and hash_required}')
                self.load(hash_required=True)
            except:
                failed = True
            assert failed

        compressed_dir = "test_compressed"
        extracted_dir = "test_extracted"

        old_vault = dataclasses.replace(self.__vault)
        old_vault_deep = copy.deepcopy(self.__vault)
        old_vault_dict = dataclasses.asdict(self.__vault)

        # Test backup
        backup = self.backup(os.path.dirname(self.path()), compressed_dir, debug=debug)
        assert backup.path is not None, "Backup should create a file."
        assert backup.hash is not None, "Backup should return a hash."
        assert os.path.exists(backup.path), f"Backup file not found at {backup.path}"
        assert backup.path.startswith(os.path.join(compressed_dir, f"zakatdb_v{self.Version()}")), "Backup filename should start with zakatdb_v<version>"
        assert backup.hash in backup.path, "Backup filename should contain the hash."

        # Test restore
        restore_successful = self.restore(backup.path, extracted_dir, debug=debug)
        assert restore_successful, "Restore should be successful when hash matches."

        assert old_vault == self.__vault
        assert old_vault_deep == self.__vault
        assert old_vault_dict == dataclasses.asdict(self.__vault)

        # Test restore with incorrect filename format
        invalid_backup_path = os.path.join(compressed_dir, "invalid_name.tar.lzma")
        with open(invalid_backup_path, "w") as f:
            f.write("")  # Create an empty file
        restore_failed_format = self.restore(invalid_backup_path, "temp_extract", debug=debug)
        assert not restore_failed_format, "Restore should fail with incorrect filename format."
        if os.path.exists("temp_extract"):
            shutil.rmtree("temp_extract")

        assert old_vault == self.__vault
        assert old_vault_deep == self.__vault
        assert old_vault_dict == dataclasses.asdict(self.__vault)

        # Clean up test files and directories
        if not debug:
            if os.path.exists(compressed_dir):
                shutil.rmtree(compressed_dir)
            if os.path.exists(extracted_dir):
                shutil.rmtree(extracted_dir)

    def test(self, debug: bool = False) -> bool:
        if debug:
            print('test', f'debug={debug}')
        try:

            self._test_core(True, debug)
            self._test_core(False, debug)

            # test_names
            self.reset()
            x = "test_names"
            failed = False
            try:
                assert self.name(x) == ''
            except:
                failed = True
            assert failed
            assert self.names() == {}
            failed = False
            try:
                assert self.name(x, 'qwe') == ''
            except:
                failed = True
            assert failed
            account_id0 = self.create_account(x)
            assert isinstance(account_id0, AccountID)
            assert int(account_id0) > 0
            assert self.name(account_id0) == x
            assert self.name(account_id0, 'qwe') == 'qwe'
            if debug:
                print(self.names(keyword='qwe'))
            assert self.names(keyword='asd') == {}
            assert self.names(keyword='qwe') == {'qwe': account_id0}

            # test_create_account
            account_name = "test_account"
            assert self.names(keyword=account_name) == {}
            account_id = self.create_account(account_name)
            assert isinstance(account_id, AccountID)
            assert int(account_id) > 0
            assert account_id in self.__vault.account
            assert self.name(account_id) == account_name
            assert self.names(keyword=account_name) == {account_name: account_id}

            failed = False
            try:
                self.create_account(account_name)
            except:
                failed = True
            assert failed

            # bad are names is forbidden

            for bad_name in [
                None,
                '',
                Time.time(),
                -Time.time(),
                f'{Time.time()}',
                f'{-Time.time()}',
                0.0,
                '0.0',
                ' ',
            ]:
                failed = False
                try:
                    self.create_account(bad_name)
                except:
                    failed = True
                assert failed

            # rename account
            assert self.name(account_id) == account_name
            assert self.name(account_id, 'asd') == 'asd'
            assert self.name(account_id) == 'asd'
            # use old and not used name
            account_id2 = self.create_account(account_name)
            assert int(account_id2) > 0
            assert account_id != account_id2
            assert self.name(account_id2) == account_name
            assert self.names(keyword=account_name) == {account_name: account_id2}

            assert self.__history()
            count = len(self.__vault.history)
            if debug:
                print('history-count', count)
            assert count == 8

            assert self.recall(dry=False, debug=debug)
            assert self.name(account_id2) == ''
            assert self.account_exists(account_id2)
            assert self.recall(dry=False, debug=debug)
            assert not self.account_exists(account_id2)
            assert self.recall(dry=False, debug=debug)
            assert self.name(account_id) == account_name
            assert self.recall(dry=False, debug=debug)
            assert self.account_exists(account_id)
            assert self.recall(dry=False, debug=debug)
            assert not self.account_exists(account_id)
            assert self.names(keyword='qwe') == {'qwe': account_id0}
            assert self.recall(dry=False, debug=debug)
            assert self.names(keyword='qwe') == {}
            assert self.name(account_id0) == x
            assert self.recall(dry=False, debug=debug)
            assert self.name(account_id0) == ''
            assert self.account_exists(account_id0)
            assert self.recall(dry=False, debug=debug)
            assert not self.account_exists(account_id0)
            assert not self.recall(dry=False, debug=debug)

            # Not allowed for duplicate transactions in the same account and time

            created = Time.time()
            same_account_id = self.create_account('same')
            self.track(100, 'test-1', same_account_id, True, created)
            failed = False
            try:
                self.track(50, 'test-1', same_account_id, True, created)
            except:
                failed = True
            assert failed is True

            self.reset()

            # Same account transfer
            for x in [1, 'a', True, 1.8, None]:
                failed = False
                try:
                    self.transfer(1, x, x, 'same-account', debug=debug)
                except:
                    failed = True
                assert failed is True

            # Always preserve box age during transfer

            series: list[tuple[int, int]] = [
                (30, 4),
                (60, 3),
                (90, 2),
            ]
            case = {
                3000: {
                    'series': series,
                    'rest': 15000,
                },
                6000: {
                    'series': series,
                    'rest': 12000,
                },
                9000: {
                    'series': series,
                    'rest': 9000,
                },
                18000: {
                    'series': series,
                    'rest': 0,
                },
                27000: {
                    'series': series,
                    'rest': -9000,
                },
                36000: {
                    'series': series,
                    'rest': -18000,
                },
            }

            selected_time = Time.time() - ZakatTracker.TimeCycle()
            ages_account_id = self.create_account('ages')
            future_account_id = self.create_account('future')

            for total in case:
                if debug:
                    print('--------------------------------------------------------')
                    print(f'case[{total}]', case[total])
                for x in case[total]['series']:
                    self.track(
                        unscaled_value=x[0],
                        desc=f'test-{x} ages',
                        account=ages_account_id,
                        created_time_ns=selected_time * x[1],
                    )

                unscaled_total = self.unscale(total)
                if debug:
                    print('unscaled_total', unscaled_total)
                refs = self.transfer(
                    unscaled_amount=unscaled_total,
                    from_account=ages_account_id,
                    to_account=future_account_id,
                    desc='Zakat Movement',
                    debug=debug,
                )

                if debug:
                    print('refs', refs)

                ages_cache_balance = self.balance(ages_account_id)
                ages_fresh_balance = self.balance(ages_account_id, False)
                rest = case[total]['rest']
                if debug:
                    print('source', ages_cache_balance, ages_fresh_balance, rest)
                assert ages_cache_balance == rest
                assert ages_fresh_balance == rest

                future_cache_balance = self.balance(future_account_id)
                future_fresh_balance = self.balance(future_account_id, False)
                if debug:
                    print('target', future_cache_balance, future_fresh_balance, total)
                    print('refs', refs)
                assert future_cache_balance == total
                assert future_fresh_balance == total

                # TODO: check boxes times for `ages` should equal box times in `future`
                for ref in self.__vault.account[ages_account_id].box:
                    ages_capital = self.__vault.account[ages_account_id].box[ref].capital
                    ages_rest = self.__vault.account[ages_account_id].box[ref].rest
                    future_capital = 0
                    if ref in self.__vault.account[future_account_id].box:
                        future_capital = self.__vault.account[future_account_id].box[ref].capital
                    future_rest = 0
                    if ref in self.__vault.account[future_account_id].box:
                        future_rest = self.__vault.account[future_account_id].box[ref].rest
                    if ages_capital != 0 and future_capital != 0 and future_rest != 0:
                        if debug:
                            print('================================================================')
                            print('ages', ages_capital, ages_rest)
                            print('future', future_capital, future_rest)
                        if ages_rest == 0:
                            assert ages_capital == future_capital
                        elif ages_rest < 0:
                            assert -ages_capital == future_capital
                        elif ages_rest > 0:
                            assert ages_capital == ages_rest + future_capital
                self.reset()
                assert len(self.__vault.history) == 0

            assert self.__history()
            assert self.__history(False) is False
            assert self.__history() is False
            assert self.__history(True)
            assert self.__history()
            if debug:
                print('####################################################################')

            wallet_account_id = self.create_account('wallet')
            safe_account_id = self.create_account('safe')
            bank_account_id = self.create_account('bank')
            transaction = [
                (
                    20, wallet_account_id, AccountID(1), -2000, -2000, -2000, 1, 1,
                    2000, 2000, 2000, 1, 1,
                ),
                (
                    750, wallet_account_id, safe_account_id, -77000, -77000, -77000, 2, 2,
                    75000, 75000, 75000, 1, 1,
                ),
                (
                    600, safe_account_id, bank_account_id, 15000, 15000, 15000, 1, 2,
                    60000, 60000, 60000, 1, 1,
                ),
            ]
            for z in transaction:
                lock = self.lock()
                x = z[1]
                y = z[2]
                self.transfer(
                    unscaled_amount=z[0],
                    from_account=x,
                    to_account=y,
                    desc='test-transfer',
                    debug=debug,
                )
                zz = self.balance(x)
                if debug:
                    print(zz, z)
                assert zz == z[3]
                xx = self.accounts()[x]
                assert xx.balance == z[3]
                assert self.balance(x, False) == z[4]
                assert xx.balance == z[4]

                s = 0
                log = self.__vault.account[x].log
                for i in log:
                    s += log[i].value
                if debug:
                    print('s', s, 'z[5]', z[5])
                assert s == z[5]

                assert self.box_size(x) == z[6]
                assert self.log_size(x) == z[7]

                yy = self.accounts()[y]
                assert self.balance(y) == z[8]
                assert yy.balance == z[8]
                assert self.balance(y, False) == z[9]
                assert yy.balance == z[9]

                s = 0
                log = self.__vault.account[y].log
                for i in log:
                    s += log[i].value
                assert s == z[10]

                assert self.box_size(y) == z[11]
                assert self.log_size(y) == z[12]
                assert lock is not None
                assert self.free(lock)

            assert self.nolock()
            history_count = len(self.__vault.history)
            transaction_count = len(transaction)
            if debug:
                print('history-count', history_count, transaction_count)
            assert history_count == transaction_count * 3
            assert not self.free(Time.time())
            assert self.free(self.lock())
            assert self.nolock()
            assert len(self.__vault.history) == transaction_count * 3

            # recall

            assert self.nolock()
            for i in range(transaction_count * 3, 0, -1):
                assert len(self.__vault.history) == i
                assert self.recall(dry=False, debug=debug) is True
            assert len(self.__vault.history) == 0
            assert self.recall(dry=False, debug=debug) is False
            assert len(self.__vault.history) == 0

            # exchange

            cash_account_id = self.create_account('cash')
            self.exchange(cash_account_id, 25, 3.75, '2024-06-25')
            self.exchange(cash_account_id, 22, 3.73, '2024-06-22')
            self.exchange(cash_account_id, 15, 3.69, '2024-06-15')
            self.exchange(cash_account_id, 10, 3.66)

            assert self.nolock()

            bank_account_id = self.create_account('bank')
            for i in range(1, 30):
                exchange = self.exchange(cash_account_id, i)
                rate, description, created = exchange.rate, exchange.description, exchange.time
                if debug:
                    print(i, rate, description, created)
                assert created
                if i < 10:
                    assert rate == 1
                    assert description is None
                elif i == 10:
                    assert rate == 3.66
                    assert description is None
                elif i < 15:
                    assert rate == 3.66
                    assert description is None
                elif i == 15:
                    assert rate == 3.69
                    assert description is not None
                elif i < 22:
                    assert rate == 3.69
                    assert description is not None
                elif i == 22:
                    assert rate == 3.73
                    assert description is not None
                elif i >= 25:
                    assert rate == 3.75
                    assert description is not None
                exchange = self.exchange(bank_account_id, i)
                rate, description, created = exchange.rate, exchange.description, exchange.time
                if debug:
                    print(i, rate, description, created)
                assert created
                assert rate == 1
                assert description is None

            assert len(self.__vault.exchange) == 1
            assert len(self.exchanges()) == 1
            self.__vault.exchange.clear()
            assert len(self.__vault.exchange) == 0
            assert len(self.exchanges()) == 0
            self.reset()

            # حفظ أسعار الصرف باستخدام التواريخ بالنانو ثانية
            cash_account_id = self.create_account('cash')
            self.exchange(cash_account_id, ZakatTracker.day_to_time(25), 3.75, '2024-06-25')
            self.exchange(cash_account_id, ZakatTracker.day_to_time(22), 3.73, '2024-06-22')
            self.exchange(cash_account_id, ZakatTracker.day_to_time(15), 3.69, '2024-06-15')
            self.exchange(cash_account_id, ZakatTracker.day_to_time(10), 3.66)

            assert self.nolock()

            test_account_id = self.create_account('test')
            for i in [x * 0.12 for x in range(-15, 21)]:
                if i <= 0:
                    assert self.exchange(test_account_id, Time.time(), i, f'range({i})') == Exchange()
                else:
                    assert self.exchange(test_account_id, Time.time(), i, f'range({i})') is not Exchange()

            assert self.nolock()

           # اختبار النتائج باستخدام التواريخ بالنانو ثانية
            bank_account_id = self.create_account('bank')
            for i in range(1, 31):
                timestamp_ns = ZakatTracker.day_to_time(i)
                exchange = self.exchange(cash_account_id, timestamp_ns)
                rate, description, created = exchange.rate, exchange.description, exchange.time
                if debug:
                    print(i, rate, description, created)
                assert created
                if i < 10:
                    assert rate == 1
                    assert description is None
                elif i == 10:
                    assert rate == 3.66
                    assert description is None
                elif i < 15:
                    assert rate == 3.66
                    assert description is None
                elif i == 15:
                    assert rate == 3.69
                    assert description is not None
                elif i < 22:
                    assert rate == 3.69
                    assert description is not None
                elif i == 22:
                    assert rate == 3.73
                    assert description is not None
                elif i >= 25:
                    assert rate == 3.75
                    assert description is not None
                exchange = self.exchange(bank_account_id, i)
                rate, description, created = exchange.rate, exchange.description, exchange.time
                if debug:
                    print(i, rate, description, created)
                assert created
                assert rate == 1
                assert description is None

            assert self.nolock()
            if debug:
                print(self.__vault.history, len(self.__vault.history))
            for _ in range(len(self.__vault.history)):
                assert self.recall(dry=False, debug=debug)
            assert not self.recall(dry=False, debug=debug)

            self.reset()

            # test transfer between accounts with different exchange rate

            a_SAR = self.create_account('Bank (SAR)')
            b_USD = self.create_account('Bank (USD)')
            c_SAR = self.create_account('Safe (SAR)')
            # 0: track, 1: check-exchange, 2: do-exchange, 3: transfer
            for case in [
                (0, a_SAR, 'SAR Gift', 1000, 100000),
                (1, a_SAR, 1),
                (0, b_USD, 'USD Gift', 500, 50000),
                (1, b_USD, 1),
                (2, b_USD, 3.75),
                (1, b_USD, 3.75),
                (3, 100, b_USD, a_SAR, '100 USD -> SAR', 40000, 137500),
                (0, c_SAR, 'Salary', 750, 75000),
                (3, 375, c_SAR, b_USD, '375 SAR -> USD', 37500, 50000),
                (3, 3.75, a_SAR, b_USD, '3.75 SAR -> USD', 137125, 50100),
            ]:
                if debug:
                    print('case', case)
                match (case[0]):
                    case 0:  # track
                        _, account, desc, x, balance = case
                        self.track(unscaled_value=x, desc=desc, account=account, debug=debug)

                        cached_value = self.balance(account, cached=True)
                        fresh_value = self.balance(account, cached=False)
                        if debug:
                            print('account', account, 'cached_value', cached_value, 'fresh_value', fresh_value)
                        assert cached_value == balance
                        assert fresh_value == balance
                    case 1:  # check-exchange
                        _, account, expected_rate = case
                        t_exchange = self.exchange(account, created_time_ns=Time.time(), debug=debug)
                        if debug:
                            print('t-exchange', t_exchange)
                        assert t_exchange.rate == expected_rate
                    case 2:  # do-exchange
                        _, account, rate = case
                        self.exchange(account, rate=rate, debug=debug)
                        b_exchange = self.exchange(account, created_time_ns=Time.time(), debug=debug)
                        if debug:
                            print('b-exchange', b_exchange)
                        assert b_exchange.rate == rate
                    case 3:  # transfer
                        _, x, a, b, desc, a_balance, b_balance = case
                        self.transfer(x, a, b, desc, debug=debug)

                        cached_value = self.balance(a, cached=True)
                        fresh_value = self.balance(a, cached=False)
                        if debug:
                            print(
                                'account', a,
                                'cached_value', cached_value,
                                'fresh_value', fresh_value,
                                'a_balance', a_balance,
                            )
                        assert cached_value == a_balance
                        assert fresh_value == a_balance

                        cached_value = self.balance(b, cached=True)
                        fresh_value = self.balance(b, cached=False)
                        if debug:
                            print('account', b, 'cached_value', cached_value, 'fresh_value', fresh_value)
                        assert cached_value == b_balance
                        assert fresh_value == b_balance

            # Transfer all in many chunks randomly from B to A
            a_SAR_balance = 137125
            b_USD_balance = 50100
            b_USD_exchange = self.exchange(b_USD)
            amounts = ZakatTracker.create_random_list(b_USD_balance, max_value=1000)
            if debug:
                print('amounts', amounts)
            i = 0
            for x in amounts:
                if debug:
                    print(f'{i} - transfer-with-exchange({x})')
                self.transfer(
                    unscaled_amount=self.unscale(x),
                    from_account=b_USD,
                    to_account=a_SAR,
                    desc=f'{x} USD -> SAR',
                    debug=debug,
                )

                b_USD_balance -= x
                cached_value = self.balance(b_USD, cached=True)
                fresh_value = self.balance(b_USD, cached=False)
                if debug:
                    print('account', b_USD, 'cached_value', cached_value, 'fresh_value', fresh_value, 'excepted',
                          b_USD_balance)
                assert cached_value == b_USD_balance
                assert fresh_value == b_USD_balance

                a_SAR_balance += int(x * b_USD_exchange.rate)
                cached_value = self.balance(a_SAR, cached=True)
                fresh_value = self.balance(a_SAR, cached=False)
                if debug:
                    print('account', a_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'expected',
                          a_SAR_balance, 'rate', b_USD_exchange.rate)
                assert cached_value == a_SAR_balance
                assert fresh_value == a_SAR_balance
                i += 1

            # Transfer all in many chunks randomly from C to A
            c_SAR_balance = 37500
            amounts = ZakatTracker.create_random_list(c_SAR_balance, max_value=1000)
            if debug:
                print('amounts', amounts)
            i = 0
            for x in amounts:
                if debug:
                    print(f'{i} - transfer-with-exchange({x})')
                self.transfer(
                    unscaled_amount=self.unscale(x),
                    from_account=c_SAR,
                    to_account=a_SAR,
                    desc=f'{x} SAR -> a_SAR',
                    debug=debug,
                )

                c_SAR_balance -= x
                cached_value = self.balance(c_SAR, cached=True)
                fresh_value = self.balance(c_SAR, cached=False)
                if debug:
                    print('account', c_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'excepted',
                          c_SAR_balance)
                assert cached_value == c_SAR_balance
                assert fresh_value == c_SAR_balance

                a_SAR_balance += x
                cached_value = self.balance(a_SAR, cached=True)
                fresh_value = self.balance(a_SAR, cached=False)
                if debug:
                    print('account', a_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'expected',
                          a_SAR_balance)
                assert cached_value == a_SAR_balance
                assert fresh_value == a_SAR_balance
                i += 1

            assert self.save(f'accounts-transfer-with-exchange-rates.{self.ext()}')

            # check & zakat with exchange rates for many cycles

            lock = None
            safe_account_id = self.create_account('safe')
            cave_account_id = self.create_account('cave')
            for rate, values in {
                1: {
                    'in': [1000, 2000, 10000],
                    'exchanged': [100000, 200000, 1000000],
                    'out': [2500, 5000, 73140],
                },
                3.75: {
                    'in': [200, 1000, 5000],
                    'exchanged': [75000, 375000, 1875000],
                    'out': [1875, 9375, 137138],
                },
            }.items():
                a, b, c = values['in']
                m, n, o = values['exchanged']
                x, y, z = values['out']
                if debug:
                    print('rate', rate, 'values', values)
                for case in [
                    (a, safe_account_id, Time.time() - ZakatTracker.TimeCycle(), [
                        {safe_account_id: {0: {'below_nisab': x}}},
                    ], False, m),
                    (b, safe_account_id, Time.time() - ZakatTracker.TimeCycle(), [
                        {safe_account_id: {0: {'count': 1, 'total': y}}},
                    ], True, n),
                    (c, cave_account_id, Time.time() - (ZakatTracker.TimeCycle() * 3), [
                        {cave_account_id: {0: {'count': 3, 'total': z}}},
                    ], True, o),
                ]:
                    if debug:
                        print(f'############# check(rate: {rate}) #############')
                        print('case', case)
                    self.reset()
                    self.exchange(account=case[1], created_time_ns=case[2], rate=rate)
                    self.track(
                        unscaled_value=case[0],
                        desc='test-check',
                        account=case[1],
                        created_time_ns=case[2],
                    )
                    assert self.snapshot()

                    # assert self.nolock()
                    # history_size = len(self.__vault.history)
                    # print('history_size', history_size)
                    # assert history_size == 2
                    lock = self.lock()
                    assert lock
                    assert not self.nolock()
                    assert self.__vault.cache.zakat is None
                    report = self.check(2.17, None, debug)
                    if debug:
                        print('[report]', report)
                    assert case[4] == report.valid
                    assert case[5] == report.summary.total_wealth
                    assert case[5] == report.summary.total_zakatable_amount
                    if report.valid:
                        assert self.__vault.cache.zakat is not None
                        assert report.plan
                        assert self.zakat(report, debug=debug)
                        assert self.__vault.cache.zakat is None
                        if debug:
                            pp().pprint(self.__vault)
                        self._test_storage(debug=debug)

                        for x in report.plan:
                            assert case[1] == x
                            if report.plan[x][0].below_nisab:
                                if debug:
                                    print('[assert]', report.plan[x][0].total, case[3][0][x][0]['below_nisab'])
                                assert report.plan[x][0].total == case[3][0][x][0]['below_nisab']
                            else:
                                if debug:
                                    print('[assert]', int(report.summary.total_zakat_due), case[3][0][x][0]['total'])
                                    print('[assert]', int(report.plan[x][0].total), case[3][0][x][0]['total'])
                                    print('[assert]', report.plan[x][0].count ,case[3][0][x][0]['count'])
                                assert int(report.summary.total_zakat_due) == case[3][0][x][0]['total']
                                assert int(report.plan[x][0].total) == case[3][0][x][0]['total']
                                assert report.plan[x][0].count == case[3][0][x][0]['count']
                    else:
                        assert self.__vault.cache.zakat is None
                        result = self.zakat(report, debug=debug)
                        if debug:
                            print('zakat-result', result, case[4])
                        assert result == case[4]
                        report = self.check(2.17, None, debug)
                        assert report.valid is False
            self._test_storage(account_id=cave_account_id, debug=debug)

            # recall after zakat

            history_size = len(self.__vault.history)
            if debug:
                print('history_size', history_size)
            assert history_size == 3
            assert not self.nolock()
            assert self.recall(dry=False, debug=debug) is False
            self.free(lock)
            assert self.nolock()

            for i in range(3, 0, -1):
                history_size = len(self.__vault.history)
                if debug:
                    print('history_size', history_size)
                assert history_size == i
                assert self.recall(dry=False, debug=debug) is True

            assert self.nolock()
            assert self.recall(dry=False, debug=debug) is False

            history_size = len(self.__vault.history)
            if debug:
                print('history_size', history_size)
            assert history_size == 0

            account_size = len(self.__vault.account)
            if debug:
                print('account_size', account_size)
            assert account_size == 0

            report_size = len(self.__vault.report)
            if debug:
                print('report_size', report_size)
            assert report_size == 0

            assert self.nolock()

            # csv

            csv_count = 1000

            for with_rate, path in {
                False: 'test-import_csv-no-exchange',
                True: 'test-import_csv-with-exchange',
            }.items():

                if debug:
                    print('test_import_csv', with_rate, path)

                csv_path = path + '.csv'
                if os.path.exists(csv_path):
                    os.remove(csv_path)
                c = self.generate_random_csv_file(
                    path=csv_path,
                    count=csv_count,
                    with_rate=with_rate,
                    debug=debug,
                )
                if debug:
                    print('generate_random_csv_file', c)
                assert c == csv_count
                assert os.path.getsize(csv_path) > 0
                cache_path = self.import_csv_cache_path()
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                self.reset()
                lock = self.lock()
                import_report = self.import_csv(csv_path, debug=debug)
                bad_count = len(import_report.bad)
                if debug:
                    print(f'csv-imported: {import_report.statistics} = count({csv_count})')
                    print('bad', import_report.bad)
                assert import_report.statistics.created + import_report.statistics.found + bad_count == csv_count
                assert import_report.statistics.created == csv_count
                assert bad_count == 0
                assert bad_count == import_report.statistics.bad
                tmp_size = os.path.getsize(cache_path)
                assert tmp_size > 0

                import_report_2 = self.import_csv(csv_path, debug=debug)
                bad_2_count = len(import_report_2.bad)
                if debug:
                    print(f'csv-imported: {import_report_2}')
                    print('bad', import_report_2.bad)
                assert tmp_size == os.path.getsize(cache_path)
                assert import_report_2.statistics.created + import_report_2.statistics.found + bad_2_count == csv_count
                assert import_report.statistics.created == import_report_2.statistics.found
                assert bad_count == bad_2_count
                assert import_report_2.statistics.found == csv_count
                assert bad_2_count == 0
                assert bad_2_count == import_report_2.statistics.bad
                assert import_report_2.statistics.created == 0

                # payment parts

                positive_parts = self.build_payment_parts(100, positive_only=True)
                assert self.check_payment_parts(positive_parts) != 0
                assert self.check_payment_parts(positive_parts) != 0
                all_parts = self.build_payment_parts(300, positive_only=False)
                assert self.check_payment_parts(all_parts) != 0
                assert self.check_payment_parts(all_parts) != 0
                if debug:
                    pp().pprint(positive_parts)
                    pp().pprint(all_parts)
                # dynamic discount
                suite = []
                count = 3
                for exceed in [False, True]:
                    case = []
                    for part in [positive_parts, all_parts]:
                        #part = parts.copy()
                        demand = part.demand
                        if debug:
                            print(demand, part.total)
                        i = 0
                        z = demand / count
                        cp = PaymentParts(
                            demand=demand,
                            exceed=exceed,
                            total=part.total,
                        )
                        j = ''
                        for x, y in part.account.items():
                            x_exchange = self.exchange(x)
                            zz = self.exchange_calc(z, 1, x_exchange.rate)
                            if exceed and zz <= demand:
                                i += 1
                                y.part = zz
                                if debug:
                                    print(exceed, y)
                                cp.account[x] = y
                                case.append(y)
                            elif not exceed and y.balance >= zz:
                                i += 1
                                y.part = zz
                                if debug:
                                    print(exceed, y)
                                cp.account[x] = y
                                case.append(y)
                            j = x
                            if i >= count:
                                break
                        if debug:
                            print('[debug]', j)
                            print('[debug]', cp.account[j])
                        if cp.account[j] != AccountPaymentPart(0.0, 0.0, 0.0):
                            suite.append(cp)
                if debug:
                    print('suite', len(suite))
                for case in suite:
                    if debug:
                        print('case', case)
                    result = self.check_payment_parts(case)
                    if debug:
                        print('check_payment_parts', result, f'exceed: {exceed}')
                    assert result == 0

                    assert self.__vault.cache.zakat is None
                    report = self.check(2.17, None, debug)
                    if debug:
                        print('valid', report.valid)
                    zakat_result = self.zakat(report, parts=case, debug=debug)
                    if debug:
                        print('zakat-result', zakat_result)
                    assert report.valid == zakat_result
                    # test verified zakat report is required
                    if zakat_result:
                        assert self.__vault.cache.zakat is None
                        failed = False
                        try:
                            self.zakat(report, parts=case, debug=debug)
                        except:
                            failed = True
                        assert failed

                assert self.free(lock)

            assert self.save(path + f'.{self.ext()}')
            assert self.save(f'1000-transactions-test.{self.ext()}')
            return True
        except Exception as e:
            if self.__debug_output:
                pp().pprint(self.__vault)
                print('============================================================================')
                pp().pprint(self.__debug_output)
            assert self.save(f'test-snapshot.{self.ext()}')
            raise e


def test(path: Optional[str] = None, debug: bool = False):
    """
    Executes a test suite for the ZakatTracker.

    This function initializes a ZakatTracker instance, optionally using a specified
    database path or a temporary directory. It then runs the test suite and, if debug
    mode is enabled, prints detailed test results and execution time.

    Parameters:
    - path (str, optional): The path to the ZakatTracker database. If None, a
                            temporary directory is created. Defaults to None.
    - debug (bool, optional): Enables debug mode, which prints detailed test
                            results and execution time. Defaults to False.

    Returns:
    None. The function asserts the result of the ZakatTracker's test suite.

    Raises:
    - AssertionError: If the ZakatTracker's test suite fails.

    Examples:
    - `test()` Runs tests using a temporary database.
    - `test(debug=True)` Runs the test suite in debug mode with a temporary directory.
    - `test(path="/path/to/my/db")` Runs tests using a specified database path.
    - `test(path="/path/to/my/db", debug=False)` Runs test suite with specified path.
    """
    no_path = path is None
    if no_path:
        path = tempfile.mkdtemp()
        print(f"Random database path {path}")
    if os.path.exists(path):
        shutil.rmtree(path)
    assert ZakatTracker(':memory:').memory_mode()
    ledger = ZakatTracker(
        db_path=path,
        history_mode=True,
    )
    start = time.time_ns()
    assert not ledger.memory_mode()
    assert ledger.test(debug=debug)
    if no_path and os.path.exists(path):
        shutil.rmtree(path)
    if debug:
        print('#########################')
        print('######## TEST DONE ########')
        print('#########################')
        print(Time.duration_from_nanoseconds(time.time_ns() - start))
        print('#########################')


def main():
    test(path='./zakat_test_db', debug=True)


if __name__ == '__main__':
    main()
