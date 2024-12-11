"""
 _____     _         _     _____               _
|__  /__ _| | ____ _| |_  |_   _| __ __ _  ___| | _____ _ __
  / // _` | |/ / _` | __|   | || '__/ _` |/ __| |/ / _ \ '__|
 / /| (_| |   < (_| | |_    | || | | (_| | (__|   <  __/ |
/____\__,_|_|\_\__,_|\__|   |_||_|  \__,_|\___|_|\_\___|_|

"رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)" -- سورة الأعراف
... Never Trust, Always Verify ...

This module provides a ZakatTracker class for tracking and calculating Zakat.

The ZakatTracker class allows users to record financial transactions, and calculate Zakat due based on the Nisab
(the minimum threshold for Zakat) and
Haul (after completing one year since every transaction received in the same account).
We use the current silver price and manage account balances.
It supports importing transactions from CSV files, exporting data to JSON format, and saving/loading the tracker state.

Key Features:

*   Tracking of positive and negative transactions
*   Calculation of Zakat based on Nisab, Haul and silver price
*   Import of transactions from CSV files
*   Export of data to JSON format
*   Persistence of tracker state using camel files

The module also includes a few helper functions and classes:

*   `JSONEncoder`: A custom JSON encoder for serializing enum values.

The ZakatTracker class is designed to be flexible & extensible, allowing users to customize it to their specific needs.

Example usage:

```python
from zakat_tracker import ZakatTracker

tracker = ZakatTracker()
tracker.track(10000, "Initial deposit")
tracker.sub(500, "Expense")
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
from time import sleep, time_ns
from pprint import PrettyPrinter as pp
from math import floor, ceil
from enum import Enum, auto
from decimal import Decimal
from typing import Dict, Any
from pathlib import Path
from camelx import Camel, CamelRegistry
import shutil
from abc import ABC, abstractmethod
import pony.orm as pony
import calendar


class WeekDay(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


# TODO: في حالة استيراد بيانات يجب متابعتها في سجل التاريخ أيضا، حتى إذا تم التراجع يمكن إضافتها مرة أخرى في كلا
#  النموذجين لاحقا


class Vault(Enum):
    ALL = auto()
    ACCOUNT = auto()
    NAME = auto()
    REPORT = auto()


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, Account):
            return obj.to_dict()
        elif obj.__class__.__name__ == "QueryResult":
            x = []
            for y in x:
                x.append(y.to_dict())
            return x
        return super().default(obj)


camel_registry = CamelRegistry()

camel = Camel([camel_registry])


class Model(ABC):

    @staticmethod
    def Version() -> str:
        """
        Returns the current version of the software.

        This function returns a string representing the current version of the software,
        including major, minor, and patch version numbers in the format "X.Y.Z".

        Returns:
        str: The current version of the software.
        """
        return '0.2.95'

    @abstractmethod
    def path(self, path: str = None) -> str:
        """
        Set or get the path to the database file.

        If no path is provided, the current path is returned.
        If a path is provided, it is set as the new path.
        The function also creates the necessary directories if the provided path is a file.

        Parameters:
        path (str, Optional): The new path to the database file. If not provided, the current path is returned.

        Returns:
        str: The current or new path to the database file.
        """

    @abstractmethod
    def sub(self, unscaled_value: float | int | Decimal, desc: str = '', account: int = 1, created: str = None,
            debug: bool = False) \
            -> tuple[
                   str,
                   list[
                       tuple[str, int],
                   ],
               ] | tuple:
        """
        Subtracts a specified value from an account's balance.

        Parameters:
        unscaled_value (float | int | Decimal): The amount to be subtracted.
        desc (str, Optional): A description for the transaction. Defaults to an empty string.
        account (int, Optional): The account number from which the value will be subtracted. Defaults to '1'.
        created (str, Optional): The datetime of the transaction in iso8601. If not provided, the current datetime will be used.
        debug (bool, Optional): A flag indicating whether to print debug information. Defaults to False.

        Returns:
        tuple: A tuple containing the datetime of the transaction in iso8601 and a list of tuples representing the age of each transaction.

        If the amount to subtract is greater than the account's balance,
        the remaining amount will be transferred to a new transaction with a negative value.

        Raises:
        ValueError: The box transaction happened again in the same time.
        ValueError: The log transaction('xxx') happened again in the same time.
        ValueError: The created must be a str, <class 'xxx'> was provided.
        """

    @abstractmethod
    def track(self, unscaled_value: float | int | Decimal = 0, desc: str = '', account: int = 1, logging: bool = True,
              created: str = None,
              debug: bool = False) -> str | None:
        """
        This function tracks a transaction for a specific account.

        Parameters:
        unscaled_value (float | int | Decimal): The value of the transaction. Default is 0.
        desc (str, Optional): The description of the transaction. Default is an empty string.
        account (int, Optional): The account for which the transaction is being tracked. Default is '1'.
        logging (bool, Optional): Whether to log the transaction. Default is True.
        created (str, Optional): The datetime of the transaction in iso8601. If not provided, it will be generated. Default is None.
        debug (bool, Optional): Whether to print debug information. Default is False.

        Returns:
        str | None: The datetime of the transaction in iso8601, or None.

        This function creates a new account if it doesn't exist, logs the transaction if logging is True, and updates the account's balance and box.

        Raises:
        ValueError: The log transaction('xxx') happened again in the same time.
        ValueError: The box transaction happened again in the same time.
        ValueError: The created must be a str, <class 'xxx'> was provided.
        """

    @abstractmethod
    def add_file(self, account: int, ref: str, path: str) -> str | None:
        """
        Adds a file reference to a specific transaction log entry in the vault.

        Parameters:
        account (int): The account number associated with the transaction log.
        ref (str): The reference to the transaction log entry in iso8601.
        path (str): The path of the file to be added.

        Returns:
        str | None: The reference of the added file in iso8601. If the account or transaction log entry does not exist, returns None.
        """

    @abstractmethod
    def remove_file(self, account: int, ref: str, file_ref: str) -> bool:
        """
        Removes a file reference from a specific transaction log entry in the vault.

        Parameters:
        account (int): The account number associated with the transaction log.
        ref (str): The reference to the transaction log entry in iso8601.
        file_ref (str): The reference of the file to be removed in iso8601.

        Returns:
        bool: True if the file reference is successfully removed, False otherwise.
        """

    @abstractmethod
    def hide(self, account_id: int, status: bool = None) -> bool:
        """
        Check or set the hide status of a specific account.

        Parameters:
        account_id (int): The account number.
        status (bool, optional): The new hide status. If not provided, the function will return the current status.

        Returns:
        bool: The current or updated hide status of the account.

        Raises:
        None

        Example:
        >>> tracker = ZakatTracker()
        >>> ref = tracker.db.track(51, 'desc', 1) # 'account1'
        >>> tracker.db.hide(1)  # Get the hide status of 'account1', which is False by default
        False
        >>> tracker.db.hide(1, True)  # Set the hide status of 'account1' to True
        True
        >>> tracker.db.hide(1)  # Get the hide status of 'account1'
        True
        >>> tracker.db.hide(1, False)
        False
        """

    @abstractmethod
    def zakatable(self, account_id: int, status: bool = None) -> bool:
        """
        Check or set the zakatable status of a specific account.

        Parameters:
        account_id (int): The account number.
        status (bool, optional): The new zakatable status. If not provided, the function will return the current status.

        Returns:
        bool: The current or updated zakatable status of the account.

        Raises:
        None

        Example:
        >>> tracker = ZakatTracker()
        >>> ref = tracker.db.track(51, 'desc', 1) # 'account1'
        >>> tracker.db.zakatable(1)  # Set the zakatable status of 'account1' to True
        True
        >>> tracker.db.zakatable(1, True)  # Set the zakatable status of 'account1' to True
        True
        >>> tracker.db.zakatable(1)  # Get the zakatable status of 'account1' by default
        True
        >>> tracker.db.zakatable(1, False)
        False
        """

    @abstractmethod
    def name(self, account_id: int) -> str | None:
        """
        Retrieves the name associated with a given account number.

        Parameters:
        account_id (int): The account number to look up.

        Returns:
        str | None: The name associated with the account, or None if not found.
        """

    @abstractmethod
    def accounts(self) -> dict:
        """
        Returns a dictionary containing account numbers as keys and their respective balances as values.

        Parameters:
        None

        Returns:
        dict: A dictionary where keys are account numbers and values are their respective balances.
        """

    @abstractmethod
    def set_exchange(self, account: int, created: str = None, rate: float = None, description: str = None,
                     debug: bool = False) -> bool:
        """
        This method is used to record exchange rates for a specific account.

        Parameters:
        - account (int): The account number for which the exchange rate is being recorded or retrieved.
        - created (datetime, str): The datetime of the exchange rate in iso8601. If not provided, the current datetime will be used.
        - rate (float, Optional): The exchange rate to be recorded. If not provided, the method will retrieve the latest exchange rate.
        - description (str, Optional): A description of the exchange rate.
        - debug (bool, Optional): Whether to print debug information. Default is False.

        Returns:
        bool: True if exchange is created, False otherwise.
        """

    @abstractmethod
    def exchange(self, account: int, created: str = None, debug: bool = False) -> dict:
        """
        This method is used to retrieve exchange rates for a specific account.

        Parameters:
        - account (int): The account number for which the exchange rate is being recorded or retrieved.
        - created (str, Optional): The datetime of the exchange rate in iso8601. If not provided, the current datetime will be used.
        - debug (bool, Optional): Whether to print debug information. Default is False.

        Returns:
        - dict: A dictionary containing the latest exchange rate and its description. If no exchange rate is found,
        it returns a dictionary with default values for the rate and description.
        """

    @abstractmethod
    def exchanges(self, account: int) -> dict | None:
        """
        Retrieves the exchange information associated with a given account.

        Parameters:
        account (int): The account ID to query.

        Returns:
        dict | None: A dictionary containing the exchange information if the account exists, otherwise None.
        """

    @abstractmethod
    def account(self, name: str = None, ref: int = None) -> tuple[int, str] | None:
        """
        This function manages accounts, supporting creation, retrieval, and updating.

        Parameters:
        name (str, optional): The name of the account. If provided and `ref` is not provided,
            a new account with this name will be created if it doesn't already exist. Defaults to None.
        ref (int, optional): The reference ID of an existing account. If provided and `name` is not provided,
            the account with this ID will be retrieved.  Defaults to None.


        Returns:
        tuple[int, str] | None: A tuple containing the account ID and name if successful,
            otherwise None.

        Raises:
        (Implementation specific exceptions, if any)

        This function performs the following actions based on the provided arguments:

        1. **Create Account (name provided, no reference):**
            - Checks if an account with the provided name exists.
            - If not found, creates a new account with the given name and commits the change to the database.
            - Returns a tuple containing the newly created account's ID and name.

        2. **Retrieve Account (reference provided, no name):**
            - Attempts to find an account with the provided reference.
            - If found, returns a tuple containing the account's ID and name.
            - If not found, returns None.

        3. **Update Account Name (both name and reference provided):**
            - Attempts to find an account with the provided reference.
            - If found:
                - Checks if the existing name matches the provided name.
                - If names differ, updates the account name with the provided name and commits the change.
            - Returns a tuple containing the account's ID and updated name (if applicable).
            - If not found with the reference, creates a new account with the provided ID and name and
              returns the new account information.
        """

    @abstractmethod
    def transfer(self, unscaled_amount: float | int | Decimal, from_account: int, to_account: int, desc: str = '',
                 created: str = None,
                 debug: bool = False) -> list[str]:
        """
        Transfers a specified value from one account to another.

        Parameters:
        unscaled_amount (float | int | Decimal): The amount to be transferred.
        from_account (int): The account number from which the value will be transferred.
        to_account (int): The account number to which the value will be transferred.
        desc (str, optional): A description for the transaction. Defaults to an empty string.
        created (str, optional): The datetime of the transaction in iso8601. If not provided, the current datetime will be used.
        debug (bool, Optional): A flag indicating whether to print debug information. Defaults to False.

        Returns:
        list[str]: A list of datetime in iso8601 corresponding to the transactions made during the transfer.

        Raises:
        ValueError: Transfer to the same account is forbidden.
        ValueError: The box transaction happened again in the same time.
        ValueError: The log transaction('xxx') happened again in the same time.
        ValueError: The created must be a str, <class 'xxx'> was provided.
        """

    @abstractmethod
    def account_exists(self, account: int) -> bool:
        """
        Check if the given account exists in the vault.

        Parameters:
        account (int): The account number to check.

        Returns:
        bool: True if the account exists, False otherwise.
        """

    @abstractmethod
    def files(self) -> list[dict[str, str | int]]:
        """
        Retrieves information about files associated with this class.

        This class method provides a standardized way to gather details about
        files used by the class for storage, snapshots, and CSV imports.

        Returns:
        list[dict[str, str | int]]: A list of dictionaries, each containing information
            about a specific file:

            * type (str): The type of file ('database', 'snapshot', 'import_csv').
            * path (str): The full file path.
            * exists (bool): Whether the file exists on the filesystem.
            * size (int): The file size in bytes (0 if the file doesn't exist).
            * human_readable_size (str): A human-friendly representation of the file size (e.g., '10 KB', '2.5 MB').

        Example:
        ```
        file_info = MyClass.files()
        for info in file_info:
            print(f"Type: {info['type']}, Exists: {info['exists']}, Size: {info['human_readable_size']}")
        ```
        """

    @abstractmethod
    def stats(self, ignore_ram: bool = True) -> dict[str, tuple[int, str]]:
        """
        Calculates and returns statistics about the object's data storage.

        This method determines the size of the database file on disk and the
        size of the data currently held in RAM (likely within a dictionary).
        Both sizes are reported in bytes and in a human-readable format
        (e.g., KB, MB).

        Parameters:
        ignore_ram (bool, Optional): Whether to ignore the RAM size. Default is True

        Returns:
        dict[str, tuple]: A dictionary containing the following statistics:

            * 'database': A tuple with two elements:
                - The database file size in bytes (int).
                - The database file size in human-readable format (str).
            * 'ram': A tuple with two elements:
                - The RAM usage (dictionary size) in bytes (int).
                - The RAM usage in human-readable format (str).

        Example:
        >>> stats = zakat_object.stats()
        >>> print(stats['database'])
        (256000, '250.0 KB')
        >>> print(stats['ram'])
        (12345, '12.1 KB')
        """

    @abstractmethod
    def logs(self, account_id: int) -> dict:
        """
        Retrieve the logs (transactions) associated with a specific account.

        Parameters:
        account_id (int): The account number for which to retrieve the logs.

        Returns:
        dict: A dictionary containing the logs associated with the given account.
        If the account does not exist, an empty dictionary is returned.
        """

    @abstractmethod
    def boxes(self, account_id: int) -> dict:
        """
        Retrieve the boxes (transactions) associated with a specific account.

        Parameters:
        account_id (int): The account number for which to retrieve the boxes.

        Returns:
        dict: A dictionary containing the boxes associated with the given account.
        If the account does not exist, an empty dictionary is returned.
        """

    @abstractmethod
    def balance(self, account_id: int = 1, cached: bool = True) -> int:
        """
        Calculate and return the balance of a specific account.

        Parameters:
        account_id (int, Optional): The account number. Default is '1'.
        cached (bool, Optional): If True, use the cached balance. If False, calculate the balance from the box. Default is True.

        Returns:
        int: The balance of the account.

        Note:
        If cached is True, the function returns the cached balance.
        If cached is False, the function calculates the balance from the box by summing up the 'rest' values of all box items.
        """

    @abstractmethod
    def box_size(self, account_id: int) -> int:
        """
        Calculate the size of the box for a specific account.

        Parameters:
        account_id (int): The account number for which the box size needs to be calculated.

        Returns:
        int: The size of the box for the given account. If the account does not exist, -1 is returned.
        """

    @abstractmethod
    def log_size(self, account_id: int) -> int:
        """
        Get the size of the log for a specific account.

        Parameters:
        account_id (int): The account number for which the log size needs to be calculated.

        Returns:
        int: The size of the log for the given account. If the account does not exist, -1 is returned.
        """

    @abstractmethod
    def save(self, path: str = None) -> bool:
        """
        Saves the ZakatTracker's current state to a camel file.

        This method serializes the internal data (`_vault`).

        Parameters:
        path (str, optional): File path for saving. Defaults to a predefined location.

        Returns:
        bool: True if the save operation is successful, False otherwise.
        """

    @abstractmethod
    def load(self, path: str = None) -> bool:
        """
        Load the current state of the ZakatTracker object from a camel file.

        Parameters:
        path (str, Optional): The path where the camel file is located. If not provided, it will use the default path.

        Returns:
        bool: True if the load operation is successful, False otherwise.
        """

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the internal data structure to its initial state.

        Parameters:
        None

        Returns:
        None
        """

    @abstractmethod
    def check(self,
              silver_gram_price: float,
              unscaled_nisab: float | int | Decimal = None,
              debug: bool = False,
              now: str = None,
              cycle: float = None,
              ) -> tuple[
        bool,
        list[int],
        dict[int, dict[int, dict[str, Any]]],
    ]:
        """
        Check the eligibility for Zakat based on the given parameters.

        Parameters:
        silver_gram_price (float): The price of a gram of silver.
        unscaled_nisab (float | int | Decimal, Optional): The minimum amount of wealth required for Zakat. If not provided,
                        it will be calculated based on the silver_gram_price.
        debug (bool, Optional): Flag to enable debug mode.
        now (str, Optional): The current datetime in iso8601. If not provided, it will be calculated using ZakatTracker.time().
        cycle (float, Optional): The time cycle for Zakat. If not provided, it will be calculated using ZakatTracker.TimeCycle().

        Returns:
        tuple: A tuple containing a boolean indicating the eligibility for Zakat, a list of brief statistics,
        and a dictionary containing the Zakat plan.
        """

    @abstractmethod
    def zakat(
            self,
            report: tuple,
            parts: dict[str, dict[str, dict[str, float]] | bool | int | float] = None,
            debug: bool = False,
    ) -> bool:
        """
        Perform Zakat calculation based on the given report and optional parts.

        Parameters:
        report (tuple): A tuple containing the validity of the report, the report data, and the zakat plan.
        parts (dict, Optional): A dictionary containing the payment parts for the zakat.
        debug (bool, Optional): A flag indicating whether to print debug information.

        Returns:
        bool: True if the zakat calculation is successful, False otherwise.
        """

    @abstractmethod
    def file_exists(self) -> bool:
        """
        Determines whether the file associated with this object exists.

        Returns:
        bool: True if the file exists, False otherwise.
        """

    @abstractmethod
    def import_csv_cache_path(self):
        """
        Generates the cache file path for imported CSV data.

        This function constructs the file path where cached data from CSV imports
        will be stored. The cache file is a camel file (.camel extension) appended
        to the base path of the object.

        Returns:
        str: The full path to the import CSV cache file.

        Example:
            >>> obj = ZakatTracker(model=DictModel('/data/reports'))
            >>> obj.db.import_csv_cache_path()
            '/data/reports.import_csv.camel'
        """

    @abstractmethod
    def daily_logs(self, weekday: WeekDay = WeekDay.Friday, debug: bool = False):
        """
        Retrieve the daily logs (transactions) from all accounts.

        The function groups the logs by day, month, and year, and calculates the total value for each group.
        It returns a dictionary where the keys are the timestamps of the daily groups,
        and the values are dictionaries containing the total value and the logs for that group.

        Parameters:
        weekday (WeekDay, Optional): Select the weekday is collected for the week data. Default is WeekDay.Friday.
        debug (bool, Optional): Whether to print debug information. Default is False.

        Returns:
        dict: A dictionary containing the daily logs.

        Example:
        >>> tracker = ZakatTracker()
        >>> tracker.db.sub(51, 'desc', 1) # account1
        >>> ref = tracker.db.track(100, 'desc', 2) # account2
        >>> tracker.db.add_file(2, ref, 'file_0')
        >>> tracker.db.add_file(2, ref, 'file_1')
        >>> tracker.db.add_file(2, ref, 'file_2')
        >>> tracker.db.daily_logs()
        {
            'daily': {
                '2024-06-30': {
                    'positive': 100,
                    'negative': 51,
                    'total': 99,
                    'rows': [
                        {
                            'account': 'account1',
                            'desc': 'desc',
                            'file': {},
                            'ref': None,
                            'value': -51,
                            'time': 1690977015000000000,
                            'transfer': False,
                        },
                        {
                            'account': 'account2',
                            'desc': 'desc',
                            'file': {
                                1722919011626770944: 'file_0',
                                1722919011626812928: 'file_1',
                                1722919011626846976: 'file_2',
                            },
                            'ref': None,
                            'value': 100,
                            'time': 1690977015000000000,
                            'transfer': False,
                        },
                    ],
                },
            },
            'weekly': {
                datetime: {
                    'positive': 100,
                    'negative': 51,
                    'total': 99,
                },
            },
            'monthly': {
                '2024-06': {
                    'positive': 100,
                    'negative': 51,
                    'total': 99,
                },
            },
            'yearly': {
                2024: {
                    'positive': 100,
                    'negative': 51,
                    'total': 99,
                },
            },
        }
        """

    @abstractmethod
    def export_json(self, path: str = "data.json") -> bool:
        """
        Exports the current state of the ZakatTracker object to a JSON file.

        Parameters:
        path (str, Optional): The path where the JSON file will be saved. Default is "data.json".

        Returns:
        bool: True if the export is successful, False otherwise.

        Raises:
        No specific exceptions are raised by this method.
        """

    @abstractmethod
    def vault(self, section: Vault = Vault.ALL) -> dict:
        """
        Returns a copy of the internal vault in dictionary format.

        Parameters:
        section (Vault, Optional): The specific section of the vault to retrieve data from. Defaults to Vault.ALL

        This method is used to retrieve the current state of the ZakatTracker object.
        It provides a snapshot of the internal data structure, allowing for further
        processing or analysis.

        Returns:
        dict: A copy of the internal vault in dictionary format.
        """

    @abstractmethod
    def snapshot(self) -> bool:
        """
        This function creates a snapshot of the current database state.

        The function calculates the hash of the current database file and checks if a snapshot with the same
        hash already exists.
        If a snapshot with the same hash exists, the function returns True without creating a new snapshot.
        If a snapshot with the same hash does not exist, the function creates a new snapshot by saving
        the current database state.
        in a new camel file with a unique timestamp as the file name. The function also updates the snapshot cache file
        with the new snapshot's hash and timestamp.

        Parameters:
        None

        Returns:
        bool: True if a snapshot with the same hash already exists or if the snapshot is successfully created.
              False if the snapshot creation fails.
        """

    @abstractmethod
    def ext(self) -> str | None:
        """
        Returns the file extension of the current object.

        Returns:
        str | None: The file extension as a string like ('camel', 'sqlite', ..., etc.),
                    or None if the extension is not available.
        """

    @abstractmethod
    def log(self, value: float, desc: str = '', account_id: int = 1, created: str = None, ref: int = None,
            debug: bool = False) -> str:
        """
        Log a transaction into the account's log.

        Parameters:
        value (float): The value of the transaction.
        desc (str, Optional): The description of the transaction.
        account_id (int, Optional): The account to log the transaction into. Default is 1.
        created (str, Optional): The datetime of the transaction in iso8601. If not provided, it will be generated.
        ref (int, Optional): The reference of the object.
        debug (bool, Optional): Whether to print debug information. Default is False.

        Returns:
        int: The timestamp of the logged transaction.

        This method updates the account's balance, count, and log with the transaction details.

        Raises:
        ValueError: The log transaction('xxx') happened again in the same time.
        ValueError: The created must be a str, <class 'xxx'> was provided.
        """

    @abstractmethod
    def ref_exists(self, account_id: int, ref_type: str, ref: str) -> bool:
        """
        Check if a specific reference (transaction) exists in the vault for a given account and reference type.

        Parameters:
        account_id (int): The account number for which to check the existence of the reference.
        ref_type (str): The type of reference (e.g., 'box', 'log', etc.).
        ref (str): The reference (transaction) datetime in iso8601 to check for existence.

        Returns:
        bool: True if the reference exists for the given account and reference type, False otherwise.
        """

    @abstractmethod
    def box_exists(self, account_id: int, ref: str) -> bool:
        """
        Check if a specific box (transaction) exists in the vault for a given account and reference.

        Parameters:
        - account_id (int): The account number for which to check the existence of the box.
        - ref (str): The reference (transaction) datetime in iso8601 to check for existence.

        Returns:
        - bool: True if the box exists for the given account and reference, False otherwise.
        """

    @abstractmethod
    def log_exists(self, account_id: int, ref: str) -> bool:
        """
        Checks if a specific transaction log entry exists for a given account.

        Parameters:
        account_id (int): The account number associated with the transaction log.
        ref (str): The reference to the transaction log entry in iso8601.

        Returns:
        bool: True if the transaction log entry exists, False otherwise.
        """

    @abstractmethod
    def snapshots(self, hide_missing: bool = True, verified_hash_only: bool = False) \
            -> dict[int, tuple[str, str, bool]]:
        """
        Retrieve a dictionary of snapshots, with their respective hashes, paths, and existence status.

        Parameters:
        - hide_missing (bool, Optional): If True, only include snapshots that exist in the dictionary. Default is True.
        - verified_hash_only (bool, Optional): If True, only include snapshots with a valid hash. Default is False.

        Returns:
        - dict[int, tuple[str, str, bool]]: A dictionary where the keys are the timestamps of the snapshots,
        and the values are tuples containing the snapshot's hash, path, and existence status.
        """

    @staticmethod
    @abstractmethod
    def test(debug: bool = False) -> bool:
        """
        Performs a test operation for the model if required.

        Parameters:
        debug (bool, optional): If True, enables debug mode. Defaults to False.

        Returns:
        bool: The result of the test operation.
        """


class Helper:
    """
    A collection of helper functions for various tasks.

    This class provides a set of static methods for common operations including:

    - High-resolution timestamping
    - Zakat calculations (Islamic obligatory alms-giving)
    - Currency exchange calculations
    - Lunar year calculations
    - Payment validation
    - Memory size estimation
    - Numeric scaling and unscaling
    - Date/time conversions
    - Human-readable size formatting
    - File hashing
    - Time duration formatting
    - Checks if the operating system is Windows

    These functions are designed to be reusable and efficient for various applications.
    """

    last_time = None
    time_diff_ms = None

    @staticmethod
    def minimum_time_diff_ms() -> tuple[float, int]:
        """
        Calculates the minimum time difference between two consecutive calls to
        `Helper._time()` in milliseconds.

        This method is used internally to ensure consistent time measurements
        even when system calls like `datetime.datetime.now()` might return the
        same value due to clock resolution limitations.

        Returns:
        tuple[float, int]:
            - The minimum time difference in milliseconds.
            - The number of iterations required to measure the difference.
        """
        diff, i = Helper.minimum_time_diff_ns()
        return diff / 1_000_000, i

    @staticmethod
    def minimum_time_diff_ns() -> tuple[int, int]:
        """
        Calculates the minimum time difference between two consecutive calls to
        `Helper._time()` in nanoseconds.

        This method is used internally to determine the minimum granularity of
        time measurements within the system.

        Returns:
        tuple[int, int]:
            - The minimum time difference in nanoseconds.
            - The number of iterations required to measure the difference.
        """
        i = 0
        x = y = Helper._time()
        while x == y:
            y = Helper._time()
            i += 1
        _y = datetime.datetime.fromisoformat(y).timestamp() * (10 ** 9)
        _x = datetime.datetime.fromisoformat(x).timestamp() * (10 ** 9)
        return _y - _x, i

    @staticmethod
    def time(now: datetime = None) -> str:
        new_time = Helper._time(now)
        if Helper.last_time is None:
            Helper.last_time = new_time
            return new_time
        while new_time == Helper.last_time:
            if Helper.time_diff_ms is None:
                diff, _ = Helper.minimum_time_diff_ms()
                Helper.time_diff_ms = ceil(diff)
            sleep(Helper.time_diff_ms / 1_000)
            new_time = Helper._time()
        Helper.last_time = new_time
        return new_time

    @staticmethod
    def _time(now: datetime = None) -> str:
        if now is None:
            now = datetime.datetime.now()
        return now.isoformat()

    @staticmethod
    def time_to_datetime(time_s: str) -> datetime:
        return datetime.datetime.fromisoformat(time_s)

    @staticmethod
    def datetime_to_milliseconds(dt: datetime) -> int:
        """
        Converts a datetime object to milliseconds since the Unix epoch.

        Parameters:
        dt: The datetime object to convert.

        Returns:
        The number of milliseconds since the Unix epoch.
        """
        return int(dt.timestamp() * 1_000)

    @staticmethod
    def milliseconds_to_datetime(timestamp_ms: int) -> datetime:
        """
        Converts a timestamp in milliseconds to a datetime object.

        Parameters:
        timestamp_ms: An integer representing the timestamp in milliseconds.

        Returns:
        The function converts the millisecond timestamp to seconds by dividing by 1000 and then
        uses the `datetime.datetime.fromtimestamp` method to create a datetime object.
        """
        return datetime.datetime.fromtimestamp(timestamp_ms // 1_000)

    @staticmethod
    def time_to_milliseconds(time_s: str) -> int:
        """
        Converts a time string to a timestamp in milliseconds.

        Parameters:
        time_s: A string representing the time in a format supported by `datetime.datetime.strptime`.

        Returns:
        The function first converts the time string to a datetime object using the `Helper.time_to_datetime` method.
        Then, it converts the datetime object to milliseconds using the `Helper.datetime_to_milliseconds` method.
        """
        return Helper.datetime_to_milliseconds(Helper.time_to_datetime(time_s))

    @staticmethod
    def iso8601_to_int(iso_format: str, strict: bool = True, debug: bool = False) -> int:
        """
        Converts an ISO 8601 formatted string or a valid integer to a compact integer representation.

        Parameters:
        iso_format: The datetime string in ISO 8601 format (e.g., "2023-11-10T15:23:56.123456") or
                    a valid integer representation of a datetime.
        strict: (bool, Optional) A boolean flag controlling parsing behavior. Defaults to True.
            - If True, only accepts valid ISO 8601 formatted strings.
            - If False, attempts to convert integers directly and also allows basic string parsing for digits-only strings.
        debug (bool, Optional): Flag to enable debug mode.

        Returns:
        An integer representing the datetime information from the ISO 8601 string or the original integer if strict is False and input is already an integer.

        Raises:
        ValueError: If the input string is not in a valid ISO 8601 format (in strict mode) or if the input
                  is an invalid integer string (in non-strict mode).

        This function converts a datetime string in ISO 8601 format to a compact integer representation.
        The integer is constructed by packing the year, month, day, hour, minute, second, and microsecond
        components of the datetime object into a single integer using a positional encoding scheme.
        Each component is scaled by a factor of 10 raised to a power that reflects its position in the
        date and time representation.

        **Note:** This representation does not include timezone information.

        **Strict vs. Non-Strict Mode:**

        - In strict mode (default), the function only accepts valid ISO 8601 formatted strings.
        - In non-strict mode, the function also attempts to convert integers directly and allows basic string
        parsing for strings that consist only of digits. This can be useful for handling potential inconsistencies
        in input data formats. However, use caution with non-strict mode as it might lead to unexpected
        behavior if the input data is not well-controlled.

        **Example Usage:**

        ```python
            iso_str = "2023-11-10T15:23:56.123456"
            int_representation = Myclass.iso8601_to_int(iso_str)
            print(int_representation)

            # In non-strict mode, this would also work:
            int_value = 20231110152356
            int_representation = Myclass.iso8601_to_int(int_value, strict=False)
            print(int_representation)
        ```
        """
        if debug:
            print(f'iso8601_to_int(iso_format={iso_format}: {iso_format.__class__.__name__}, strict={strict})')
        if not strict:
            if type(iso_format) is int:
                return int(iso_format)
            if type(iso_format) is str:
                if iso_format.isdigit():
                    return int(iso_format)
        dt = datetime.datetime.fromisoformat(iso_format) if type(iso_format) is str else iso_format
        return ((dt.year * 10 ** 16) +
                (dt.month * 10 ** 14) +
                (dt.day * 10 ** 12) +
                (dt.hour * 10 ** 10) +
                (dt.minute * 10 ** 8) +
                (dt.second * 10 ** 6) +
                dt.microsecond)

    @staticmethod
    def int_to_iso8601(timestamp: int, extra_ms: int = None) -> str:
        """
        Converts an integer timestamp to an ISO 8601 formatted string.

        Parameters:
        timestamp: An integer representing a timestamp in the format YYYYMMDDHHMMSSuuuuuu.
        extra_ms: An optional integer representing additional milliseconds to add to the timestamp.

        Returns:
        A string representing the timestamp in ISO 8601 format (e.g., '2023-11-19T12:34:56.789012').

        This function first extracts the year, month, day, hour, minute, second, and microsecond components from the integer timestamp.
        If an `extra_ms` value is provided, it's added to the microseconds, and any resulting overflow is propagated to
        the higher time units (seconds, minutes, hours, days, months, and years).
        The function then constructs an ISO 8601 formatted string using the adjusted time components and returns it.
        """
        microseconds = timestamp % 10 ** 6
        seconds = (timestamp // 10 ** 6) % 10 ** 2
        minutes = (timestamp // 10 ** 8) - ((timestamp // 10 ** 10) * 10 ** 2)
        hours = (timestamp // 10 ** 10) - ((timestamp // 10 ** 12) * 10 ** 2)
        day = (timestamp // 10 ** 12) - ((timestamp // 10 ** 14) * 10 ** 2)
        month = (timestamp // 10 ** 14) - ((timestamp // 10 ** 16) * 10 ** 2)
        year = timestamp // 10 ** 16

        if extra_ms is not None:
            microseconds += extra_ms
            if microseconds >= 1_000_000:
                seconds += microseconds // 1_000_000
                microseconds %= 1_000_000

            if seconds >= 60:
                minutes += seconds // 60
                seconds %= 60

            if minutes >= 60:
                hours += minutes // 60
                minutes %= 60

            if hours >= 24:
                day += hours // 24
                hours %= 24

                # Handle day overflow, considering month length
                max_days_in_month = calendar.monthrange(year, month)[1]
                if day > max_days_in_month:
                    month += 1
                    day = 1
                    if month > 12:
                        year += 1
                        month = 1

        return datetime.datetime.fromisoformat(
            f"{year:04d}-{month:02d}-{day:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}.{microseconds:06d}",
        ).isoformat()

    @staticmethod
    def is_windows() -> bool:
        """
        Checks if the operating system is Windows.

        This static method uses two checks to determine if the platform is Windows:

        1. Checks if `sys.platform` is equal to 'win32'.
        2. Checks if `os.name` is equal to 'nt'.

        Returns:
        bool: True if the platform is Windows, False otherwise.
        """
        return sys.platform == 'win32' or os.name == 'nt'

    @staticmethod
    def ZakatCut(x: float) -> float:
        """
        Calculates the Zakat amount due on an asset.

        This function calculates the zakat amount due on a given asset value over one lunar year.
        Zakat is an Islamic obligatory alms-giving, calculated as a fixed percentage of an individual's wealth
        that exceeds a certain threshold (Nisab).

        Parameters:
        x: The total value of the asset on which Zakat is to be calculated.

        Returns:
        The amount of Zakat due on the asset, calculated as 2.5% of the asset's value.
        """
        return 0.025 * x  # Zakat Cut in one Lunar Year

    @staticmethod
    def exchange_calc(x: float, x_rate: float, y_rate: float) -> float:
        """
        This function calculates the exchanged amount of a currency.

        Args:
            x (float): The original amount of the currency.
            x_rate (float): The exchange rate of the original currency.
            y_rate (float): The exchange rate of the target currency.

        Returns:
            float: The exchanged amount of the target currency.
        """
        return (x * x_rate) / y_rate

    @staticmethod
    def TimeCycle(days: int = 355) -> int:
        """
        Calculates the approximate duration of a lunar year in milliseconds.

        This function calculates the approximate duration of a lunar year based on the given number of days.
        It converts the given number of days into milliseconds for use in high-precision timing applications.

        Parameters:
        days (int, Optional): The number of days in a lunar year. Defaults to 355,
              which is an approximation of the average length of a lunar year.

        Returns:
        The approximate duration of a lunar year in milliseconds.
        """
        return int(60 * 60 * 24 * days * 1e3)  # Lunar Year in milliseconds

    @staticmethod
    def Nisab(gram_price: float, gram_quantity: float = 595) -> float:
        """
        Calculate the total value of Nisab(a unit of weight in Islamic jurisprudence) based on the given price per gram.

        This function calculates the Nisab value, which is the minimum threshold of wealth,
        that makes an individual liable for paying Zakat.
        The Nisab value is determined by the equivalent value of a specific amount
        of gold or silver (currently 595 grams in silver) in the local currency.

        Parameters:
        - gram_price (float): The price per gram of Nisab.
        - gram_quantity (float, Optional): The quantity of grams in a Nisab. Default is 595 grams of silver.

        Returns:
        - float: The total value of Nisab based on the given price per gram.
        """
        return gram_price * gram_quantity

    @staticmethod
    def check_payment_parts(
            parts: dict[str, dict[str, dict[str, float]] | bool | int | float],
            debug: bool = False,
    ) -> int:
        """
        Checks the validity of payment parts.

        Parameters:
        parts (dict): A dictionary containing payment parts information.
        debug (bool, Optional): Flag to enable debug mode.

        Returns:
        int: Returns 0 if the payment parts are valid, otherwise returns the error code.

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
        for i in ['demand', 'account', 'total', 'exceed']:
            if i not in parts:
                return 1
        exceed = parts['exceed']
        for x in parts['account']:
            for j in ['balance', 'rate', 'part']:
                if j not in parts['account'][x]:
                    return 2
                if parts['account'][x]['part'] < 0:
                    return 3
                if not exceed and parts['account'][x]['balance'] <= 0:
                    return 4
        demand = parts['demand']
        z = 0
        for _, y in parts['account'].items():
            if not exceed and y['part'] > y['balance']:
                return 5
            z += Helper.exchange_calc(y['part'], y['rate'], 1)
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

    @staticmethod
    def get_dict_size(obj: dict, seen: set = None) -> float:
        """
        Recursively calculates the approximate memory size of a dictionary and its contents in bytes.

        This function traverses the dictionary structure, accounting for the size of keys, values,
        and any nested objects. It handles various data types commonly found in dictionaries
        (e.g., lists, tuples, sets, numbers, strings) and prevents infinite recursion in case
        of circular references.

        Parameters:
        obj (dict): The dictionary whose size is to be calculated.
        seen (set, optional): A set used internally to track visited objects
                             and avoid circular references. Defaults to None.

        Returns:
            float: An approximate size of the dictionary and its contents in bytes.

        Note:
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
                size += Helper.get_dict_size(k, seen)
                size += Helper.get_dict_size(v, seen)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for item in obj:
                size += Helper.get_dict_size(item, seen)
        elif isinstance(obj, (int, float, complex)):  # Handle numbers
            pass  # Basic numbers have a fixed size, so nothing to add here
        elif isinstance(obj, str):  # Handle strings
            size += len(obj) * sys.getsizeof(str().encode())  # Size per character in bytes
        return size

    @staticmethod
    def scale(x: float | int | Decimal, decimal_places: int = 2) -> int:
        """
        Scales a numerical value by a specified power of 10, returning an integer.

        This function is designed to handle various numeric types (`float`, `int`, or `Decimal`) and
        facilitate precise scaling operations, particularly useful in financial or scientific calculations.

        Parameters:
        x (float | int | Decimal): The numeric value to scale. Can be a floating-point number, integer, or decimal.
        decimal_places (int, Optional): The exponent for the scaling factor (10**y).
            Defaults to 2, meaning the input is scaled by a factor of 100 (e.g., converts 1.23 to 123).

        Returns:
        The scaled value, rounded to the nearest integer.

        Raises:
        TypeError: If the input `x` is not a valid numeric type.

        Examples:
        >>> Helper.scale(3.14159)
        314
        >>> Helper.scale(1234, decimal_places=3)
        1234000
        >>> Helper.scale(Decimal("0.005"), decimal_places=4)
        50
        """
        if not isinstance(x, (float, int, Decimal)):
            raise TypeError("Input 'x' must be a float, int, or Decimal.")
        return int(Decimal(f"{x:.{decimal_places}f}") * (10 ** decimal_places))

    @staticmethod
    def unscale(x: int, return_type: type = float, decimal_places: int = 2) -> float | Decimal:
        """
        Unscales an integer by a power of 10.

        Parameters:
        x (int): The integer to unscale.
        return_type (type, Optional): The desired type for the returned value. Can be float, int, or Decimal. Defaults to float.
        decimal_places (int, Optional): The power of 10 to use. Defaults to 2.

        Returns:
        The unscaled number, converted to the specified return_type.

        Raises:
        TypeError: If the return_type is not float or Decimal.
        """
        if return_type not in (float, Decimal):
            raise TypeError(f'Invalid return_type({return_type}). Supported types are float, int, and Decimal.')
        return round(return_type(x / (10 ** decimal_places)), decimal_places)

    @staticmethod
    def human_readable_size(size: float, decimal_places: int = 2) -> str:
        """
        Converts a size in bytes to a human-readable format (e.g., KB, MB, GB).

        This function iterates through progressively larger units of information
        (B, KB, MB, GB, etc.) and divides the input size until it fits within a
        range that can be expressed with a reasonable number before the unit.

        Parameters:
        size (float): The size in bytes to convert.
        decimal_places (int, optional): The number of decimal places to display
            in the result. Defaults to 2.

        Returns:
        str: A string representation of the size in a human-readable format,
            rounded to the specified number of decimal places. For example:
                - "1.50 KB" (1536 bytes)
                - "23.00 MB" (24117248 bytes)
                - "1.23 GB" (1325899906 bytes)
        """
        if type(size) not in (float, int):
            raise TypeError("size must be a float or integer")
        if type(decimal_places) is not int:
            raise TypeError("decimal_places must be an integer")
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"

    @staticmethod
    def file_hash(file_path: str, algorithm: str = "blake2b") -> str:
        """
        Calculates the hash of a file using the specified algorithm.

        Parameters:
        file_path (str): The path to the file.
        algorithm (str, optional): The hashing algorithm to use. Defaults to "blake2b".

        Returns:
        str: The hexadecimal representation of the file's hash.
        """
        hash_obj = hashlib.new(algorithm)  # Create the hash object
        with open(file_path, "rb") as f:  # Open file in binary mode for reading
            for chunk in iter(lambda: f.read(4096), b""):  # Read file in chunks
                hash_obj.update(chunk)
        return hash_obj.hexdigest()  # Return the hash as a hexadecimal string

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
        **"Millennium:Century:Years:Days:Hours:Minutes:Seconds:MilliSeconds:MicroSeconds:NanoSeconds"**
        Example Output: ('039:0001:047:325:05:02:03:456:789:012', ' 39 Millennia,    1 Century,  47 Years,  325 Days,
        5 Hours,  2 Minutes,  3 Seconds,  456 MilliSeconds,  789 MicroSeconds,  12 NanoSeconds')
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
        time_lapsed = \
            f"{n:03.0f}:{c:04.0f}:{y:03.0f}:{d:03.0f}:{h:02.0f}:{m:02.0f}:{s:02.0f}::{ms:03.0f}::{us:03.0f}::{ns:03.0f}"
        spoken_time_part = []
        if n > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{n: 3d} {millennia}")
        if c > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{c: 4d} {century}")
        if y > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{y: 3d} {years}")
        if d > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{d: 4d} {days}")
        if h > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{h: 2d} {hours}")
        if m > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{m: 2d} {minutes}")
        if s > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{s: 2d} {seconds}")
        if ms > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{ms: 3d} {milli_seconds}")
        if us > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{us: 3d} {micro_seconds}")
        if ns > 0 or show_zeros_in_spoken_time:
            spoken_time_part.append(f"{ns: 3d} {nano_seconds}")
        return time_lapsed, spoken_time_separator.join(spoken_time_part)

    @staticmethod
    def day_to_time(day: int, month: int = 6, year: int = 2024) -> str:  # افتراض أن الشهر هو يونيو والسنة 2024
        """
        Convert a specific day, month, and year into a timestamp.

        Parameters:
        day (int): The day of the month.
        month (int, Optional): The month of the year. Default is 6 (June).
        year (int, Optional): The year. Default is 2024.

        Returns:
        int: The timestamp representing the given day, month, and year.

        Note:
        This method assumes the default month and year if not provided.
        """
        return Helper.time(datetime.datetime(year, month, day))

    @staticmethod
    def test(debug: bool = False):

        # sanity check - forward time difference

        time_diff_ns, time_diff_ns_count = Helper.minimum_time_diff_ns()
        time_diff_ms, time_diff_ms_count = Helper.minimum_time_diff_ms()
        if debug:
            print(f'is_windows = {Helper.is_windows()}')
            print(f'time_diff_ns = {time_diff_ns}, count = {time_diff_ns_count}')
            print(f'time_diff_ms = {time_diff_ms}, count = {time_diff_ms_count}')
        limit = 18 if Helper.is_windows() else 1  # for windows >= 18ms, other >= 1
        assert limit >= time_diff_ms > 0

        # sanity check - random forward time

        xlist = []
        limit = 1000
        for i in range(limit):
            y = Helper.time()
            z = '-'
            if y not in xlist:
                xlist.append(y)
            else:
                z = 'x'
            if debug:
                print(z, y, f'[{i}/{limit}]')
        xx = len(xlist)
        if debug:
            print('count', xx, ' - unique: ', (xx / limit) * 100, '%')
        assert limit == xx

        # sanity check - convert date since 1AD to 9999AD

        month = 12
        day = 27
        hour = 18
        minute = 30
        second = 45
        microsecond = 306090
        for unix_timestamp in [True, False]:
            for year in range(1, 9999):
                s = Helper.time(datetime.datetime.strptime(
                    f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}",
                    "%Y-%m-%d %H:%M:%S.%f",
                ))
                if debug:
                    print(s)
                if Helper.is_windows() and year == 1:
                    if debug:
                        print(f'[SKIPPED] year({year})')
                    continue
                d = Helper.time_to_datetime(s)
                ms = Helper.datetime_to_milliseconds(d)
                dd = Helper.milliseconds_to_datetime(ms)
                int_val = Helper.iso8601_to_int(dd.isoformat() if unix_timestamp else d.isoformat())
                iso_val = Helper.int_to_iso8601(int_val)
                date = Helper.time_to_datetime(iso_val)
                if debug:
                    print(date,
                          f'year({date.year} = {year}), month({date.month} = {month}), day({date.day} = {day}), hour({date.hour} = {hour}), minute({date.minute} = {minute}), second({date.second} = {second}), microsecond({date.microsecond} = {microsecond})')
                assert date.year == year
                assert date.month == month
                assert date.day == day
                assert date.hour == hour
                assert date.minute == minute
                assert date.second == second
                # datetime_to_milliseconds & milliseconds_to_datetime not support microsecond
                if not unix_timestamp:
                    assert date.microsecond == microsecond

        # sanity check - datetime to int

        for usecase, expected in {
            # microsecond
            datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0): datetime.datetime(
                year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=1),
            # second
            datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=0,
                              microsecond=999999): datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=1,
                                                                     microsecond=0),
            # minute
            datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=59,
                              microsecond=999999): datetime.datetime(year=1, month=1, day=1, hour=0, minute=1, second=0,
                                                                     microsecond=0),
            # hour
            datetime.datetime(year=1, month=1, day=1, hour=0, minute=59, second=59,
                              microsecond=999999): datetime.datetime(year=1, month=1, day=1, hour=1, minute=0, second=0,
                                                                     microsecond=0),
            # day
            datetime.datetime(year=1, month=1, day=1, hour=23, minute=59, second=59,
                              microsecond=999999): datetime.datetime(year=1, month=1, day=2, hour=0, minute=0, second=0,
                                                                     microsecond=0),
            # month
            datetime.datetime(year=1, month=1, day=31, hour=23, minute=59, second=59,
                              microsecond=999999): datetime.datetime(year=1, month=2, day=1, hour=0, minute=0, second=0,
                                                                     microsecond=0),
            # year
            datetime.datetime(year=1, month=12, day=31, hour=23, minute=59, second=59,
                              microsecond=999999): datetime.datetime(year=2, month=1, day=1, hour=0, minute=0, second=0,
                                                                     microsecond=0),
        }.items():

            if debug:
                print('usecase', usecase)
                print('expected', expected)

            usecase_datetime = datetime.datetime.fromisoformat(
                Helper.int_to_iso8601(Helper.iso8601_to_int(usecase.isoformat())))
            assert usecase_datetime.year == usecase.year
            assert usecase_datetime.month == usecase.month
            assert usecase_datetime.day == usecase.day
            assert usecase_datetime.hour == usecase.hour
            assert usecase_datetime.minute == usecase.minute
            assert usecase_datetime.second == usecase.second
            assert usecase_datetime.microsecond == usecase.microsecond

            expected_datetime = datetime.datetime.fromisoformat(
                Helper.int_to_iso8601(Helper.iso8601_to_int(expected.isoformat())))
            assert expected_datetime.year == expected.year
            assert expected_datetime.month == expected.month
            assert expected_datetime.day == expected.day
            assert expected_datetime.hour == expected.hour
            assert expected_datetime.minute == expected.minute
            assert expected_datetime.second == expected.second
            assert expected_datetime.microsecond == expected.microsecond

            result = datetime.datetime.fromisoformat(
                Helper.int_to_iso8601(Helper.iso8601_to_int(usecase.isoformat()), extra_ms=1))
            if debug:
                print('result', result)
                print('===========================================')
            assert result.year == expected.year
            assert result.month == expected.month
            assert result.day == expected.day
            assert result.hour == expected.hour
            assert result.minute == expected.minute
            assert result.second == expected.second
            assert result.microsecond == expected.microsecond

        # human_readable_size

        assert Helper.human_readable_size(0) == "0.00 B"
        assert Helper.human_readable_size(512) == "512.00 B"
        assert Helper.human_readable_size(1023) == "1023.00 B"

        assert Helper.human_readable_size(1024) == "1.00 KB"
        assert Helper.human_readable_size(2048) == "2.00 KB"
        assert Helper.human_readable_size(5120) == "5.00 KB"

        assert Helper.human_readable_size(1024 ** 2) == "1.00 MB"
        assert Helper.human_readable_size(2.5 * 1024 ** 2) == "2.50 MB"

        assert Helper.human_readable_size(1024 ** 3) == "1.00 GB"
        assert Helper.human_readable_size(1024 ** 4) == "1.00 TB"
        assert Helper.human_readable_size(1024 ** 5) == "1.00 PB"

        assert Helper.human_readable_size(1536, decimal_places=0) == "2 KB"
        assert Helper.human_readable_size(2.5 * 1024 ** 2, decimal_places=1) == "2.5 MB"
        assert Helper.human_readable_size(1234567890, decimal_places=3) == "1.150 GB"

        try:
            # noinspection PyTypeChecker
            Helper.human_readable_size("not a number")
            assert False, "Expected TypeError for invalid input"
        except TypeError:
            pass

        try:
            # noinspection PyTypeChecker
            Helper.human_readable_size(1024, decimal_places="not an int")
            assert False, "Expected TypeError for invalid decimal_places"
        except TypeError:
            pass

        # get_dict_size
        assert Helper.get_dict_size({}) == sys.getsizeof({}), "Empty dictionary size mismatch"
        assert Helper.get_dict_size({"a": 1, "b": 2.5, "c": True}) != sys.getsizeof({}), "Not Empty dictionary"

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
                        Decimal,
                ):
                    for i in range(max_i):
                        for j in range(max_j):
                            total += 1
                            num_str = f'{sign}{i}.{j:0{decimal_places}d}'
                            num = return_type(num_str)
                            scaled = Helper.scale(num, decimal_places=decimal_places)
                            unscaled = Helper.unscale(scaled, return_type=return_type, decimal_places=decimal_places)
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


class DictModel(Model):
    """
    A dictionary-based model.

    This class provides a convenient way to represent data as a dictionary.
    It may offer additional features like validation, serialization, or deserialization.
    """

    def __init__(self, db_path: str = "./zakat_db/zakat.camel"):
        """
        Initialize DictModel with database path.

        Parameters:
        db_path (str): The path to the database file. Default is "zakat.camel".

        Returns:
        None
        """
        self._base_path = None
        self._vault_path = None
        self._vault = None
        self.reset()
        self.path(db_path)
        self.provider = 'dict'

    def path(self, path: str = None) -> str:
        if path is None:
            return self._vault_path
        self._vault_path = Path(path).resolve()
        base_path = Path(path).resolve()
        if base_path.is_file() or base_path.suffix:
            base_path = base_path.parent
        base_path.mkdir(parents=True, exist_ok=True)
        self._base_path = base_path
        return str(self._vault_path)

    def file_exists(self) -> bool:
        return True

    def reset(self) -> None:
        self._vault = {
            'account': {},
            'exchange': {},
            'report': {},
        }

    def ext(self) -> str | None:
        return 'camel'

    def base_path(self, *args) -> str:
        """
        Generate a base path by joining the provided arguments with the existing base path.

        Parameters:
        *args (str): Variable length argument list of strings to be joined with the base path.

        Returns:
        str: The generated base path. If no arguments are provided, the existing base path is returned.
        """
        if not args:
            return str(self._base_path)
        filtered_args = []
        ignored_filename = None
        for arg in args:
            if Path(arg).suffix:
                ignored_filename = arg
            else:
                filtered_args.append(arg)
        base_path = Path(self._base_path)
        full_path = base_path.joinpath(*filtered_args)
        full_path.mkdir(parents=True, exist_ok=True)
        if ignored_filename is not None:
            return full_path.resolve() / ignored_filename  # Join with the ignored filename
        return str(full_path.resolve())

    def vault(self, section: Vault = Vault.ALL) -> dict:
        match section:
            case Vault.ACCOUNT:
                return self._vault['account'].copy()
            case Vault.NAME:
                return self._vault['name'].copy()
            case Vault.REPORT:
                return self._vault['report'].copy()
        return self._vault.copy()

    @staticmethod
    def stats_init() -> dict[str, tuple[int, str]]:
        """
        Initialize and return a dictionary containing initial statistics for the ZakatTracker instance.

        The dictionary contains two keys: 'database' and 'ram'. Each key maps to a tuple containing two elements:
        - The initial size of the respective statistic in bytes (int).
        - The initial size of the respective statistic in a human-readable format (str).

        Returns:
        dict[str, tuple]: A dictionary with initial statistics for the ZakatTracker instance.
        """
        return {
            'database': (0, '0'),
            'ram': (0, '0'),
        }

    def stats(self, ignore_ram: bool = True) -> dict[str, tuple[int, str]]:
        ram_size = 0.0 if ignore_ram else Helper.get_dict_size(self.vault(Vault.ALL))
        file_size = os.path.getsize(self.path())
        return {
            'database': (file_size, Helper.human_readable_size(file_size)),
            'ram': (ram_size, Helper.human_readable_size(ram_size)),
        }

    def files(self) -> list[dict[str, str | int]]:
        result = []
        for file_type, path in {
            'database': self.path(),
            'snapshot': self.snapshot_cache_path(),
            'import_csv': self.import_csv_cache_path(),
        }.items():
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            human_readable_size = Helper.human_readable_size(size) if exists else 0
            result.append({
                'type': file_type,
                'path': path,
                'exists': exists,
                'size': size,
                'human_readable_size': human_readable_size,
            })
        return result

    def account_exists(self, account: int) -> bool:
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        return account in self._vault['account']

    def box_size(self, account_id: int) -> int:
        if self.account_exists(account_id):
            return len(self._vault['account'][account_id]['box'])
        return -1

    def log_size(self, account_id: int) -> int:
        if self.account_exists(account_id):
            return len(self._vault['account'][account_id]['log'])
        return -1

    def snapshot_cache_path(self):
        """
        Generate the path for the cache file used to store snapshots.

        The cache file is a camel file that stores the timestamps of the snapshots.
        The file name is derived from the main database file name by replacing the ".camel" extension
        with ".snapshots.camel".

        Returns:
        str: The path to the cache file.
        """
        path = str(self.path())
        ext = self.ext()
        ext_len = len(ext)
        if path.endswith(f'.{ext}'):
            path = path[:-ext_len - 1]
        _, filename = os.path.split(path + f'.snapshots.{ext}')
        return self.base_path(filename)

    def snapshot(self) -> bool:
        current_hash = Helper.file_hash(self.path())
        cache: dict[str, int] = {}  # hash: time_ns
        try:
            with open(self.snapshot_cache_path(), 'r') as stream:
                cache = camel.load(stream.read())
        except:
            pass
        if current_hash in cache:
            return True
        time = time_ns()
        cache[current_hash] = time
        if not self.save(self.base_path('snapshots', f'{time}.{self.ext()}')):
            return False
        with open(self.snapshot_cache_path(), 'w') as stream:
            stream.write(camel.dump(cache))
        return True

    def ref_exists(self, account_id: int, ref_type: str, ref: str) -> bool:
        if not isinstance(account_id, int):
            raise ValueError(f'The account_id must be an integer, {type(account_id)} was provided.')
        if account_id in self._vault['account']:
            return ref in self._vault['account'][account_id][ref_type]
        return False

    def box_exists(self, account_id: int, ref: str) -> bool:
        return self.ref_exists(account_id, 'box', ref)

    def snapshots(self, hide_missing: bool = True, verified_hash_only: bool = False) \
            -> dict[int, tuple[str, str, bool]]:
        cache: dict[str, int] = {}  # hash: time_ns
        try:
            with open(self.snapshot_cache_path(), 'r') as stream:
                cache = camel.load(stream.read())
        except:
            pass
        if not cache:
            return {}
        result: dict[int, tuple[str, str, bool]] = {}  # time_ns: (hash, path, exists)
        for file_hash, ref in cache.items():
            path = self.base_path('snapshots', f'{ref}.{self.ext()}')
            exists = os.path.exists(path)
            valid_hash = Helper.file_hash(path) == file_hash if verified_hash_only else True
            if (verified_hash_only and not valid_hash) or (verified_hash_only and not exists):
                continue
            if exists or not hide_missing:
                result[ref] = (file_hash, path, exists)
        return result

    def log_exists(self, account_id: int, ref: str) -> bool:
        return self.ref_exists(account_id, 'log', ref)

    def log(self, value: float, desc: str = '', account_id: int = 1, created: str = None, ref: int = None,
            debug: bool = False) -> str:
        if debug:
            print('_log', f'debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        try:
            self._vault['account'][account_id]['balance'] += value
        except TypeError:
            self._vault['account'][account_id]['balance'] += Decimal(value)
        self._vault['account'][account_id]['count'] += 1
        if debug:
            print('create-log', created)
        if self.log_exists(account_id, created):
            raise ValueError(f"The log transaction('{desc}') happened again in the same time({created}).")
        if debug:
            print('created-log', created)
        self._vault['account'][account_id]['log'][created] = {
            'value': value,
            'desc': desc,
            'ref': ref,
            'file': {},
        }
        return created

    def exchanges(self, account: int) -> dict | None:
        if self.account_exists(account):
            return self._vault['account'][account]['exchange'].copy()
        return None

    def accounts(self) -> dict:
        result = {}
        for i in self._vault['account']:
            result[i] = self._vault['account'][i]['balance']
        return result

    def boxes(self, account_id: int) -> dict:
        if self.account_exists(account_id):
            return self._vault['account'][account_id]['box']
        return {}

    def logs(self, account_id: int) -> dict:
        if self.account_exists(account_id):
            return self._vault['account'][account_id]['log']
        return {}

    @staticmethod
    def daily_logs_init() -> dict[str, dict]:
        """
        Initialize a dictionary to store daily, weekly, monthly, and yearly logs.

        Returns:
        dict: A dictionary with keys 'daily', 'weekly', 'monthly', and 'yearly', each containing an empty dictionary.
            Later each key maps to another dictionary, which will store the logs for the corresponding time period.
        """
        return {
            'daily': {},
            'weekly': {},
            'monthly': {},
            'yearly': {},
        }

    def daily_logs(self, weekday: WeekDay = WeekDay.Friday, debug: bool = False):
        logs = {}
        for account in self.accounts():
            for k, v in self.logs(account).items():
                v['time'] = k
                v['account'] = account
                if k not in logs:
                    logs[k] = []
                logs[k].append(v)
        if debug:
            print('logs', logs)
        y = self.daily_logs_init()
        for i in sorted(logs, reverse=True):
            dt = Helper.time_to_datetime(i)
            daily = f'{dt.year}-{dt.month:02d}-{dt.day:02d}'
            weekly = dt - datetime.timedelta(days=weekday.value)
            monthly = f'{dt.year}-{dt.month:02d}'
            yearly = dt.year
            # daily
            if daily not in y['daily']:
                y['daily'][daily] = {
                    'positive': 0,
                    'negative': 0,
                    'total': 0,
                    'rows': [],
                }
            transfer = len(logs[i]) > 1
            if debug:
                print('logs[i]', logs[i])
            for z in logs[i]:
                if debug:
                    print('z', z)
                # daily
                value = z['value']
                if value > 0:
                    y['daily'][daily]['positive'] += value
                else:
                    y['daily'][daily]['negative'] += -value
                y['daily'][daily]['total'] += value
                z['transfer'] = transfer
                y['daily'][daily]['rows'].append(z)
                # weekly
                if weekly not in y['weekly']:
                    y['weekly'][weekly] = {
                        'positive': 0,
                        'negative': 0,
                        'total': 0,
                    }
                if value > 0:
                    y['weekly'][weekly]['positive'] += value
                else:
                    y['weekly'][weekly]['negative'] += -value
                y['weekly'][weekly]['total'] += value
                # monthly
                if monthly not in y['monthly']:
                    y['monthly'][monthly] = {
                        'positive': 0,
                        'negative': 0,
                        'total': 0,
                    }
                if value > 0:
                    y['monthly'][monthly]['positive'] += value
                else:
                    y['monthly'][monthly]['negative'] += -value
                y['monthly'][monthly]['total'] += value
                # yearly
                if yearly not in y['yearly']:
                    y['yearly'][yearly] = {
                        'positive': 0,
                        'negative': 0,
                        'total': 0,
                    }
                if value > 0:
                    y['yearly'][yearly]['positive'] += value
                else:
                    y['yearly'][yearly]['negative'] += -value
                y['yearly'][yearly]['total'] += value
        if debug:
            print('y', y)
        return y

    def track(self, unscaled_value: float | int | Decimal = 0, desc: str = '', account: int = 1, logging: bool = True,
              created: str = None,
              debug: bool = False) -> str | None:
        if debug:
            print('track', f'unscaled_value={unscaled_value}, debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        if not self.account_exists(account):
            if debug:
                print(f"account {account} created")
            self._vault['account'][account] = {
                'balance': 0,
                'box': {},
                'count': 0,
                'exchange': {},
                'log': {},
                'hide': False,
                'zakatable': True,
            }
        if unscaled_value == 0:
            return None
        value = Helper.scale(unscaled_value)
        if logging:
            self.log(value=value, desc=desc, account_id=account, created=created, ref=None, debug=debug)
        if debug:
            print('creating-box', created)
        if self.box_exists(account, created):
            raise ValueError(f"The box transaction happened again in the same time({created}).")
        self._vault['account'][account]['box'][created] = {
            'capital': value,
            'count': 0,
            'last': 0,
            'rest': value,
            'total': 0,
        }
        if debug:
            print('created-box', created)
        return created

    def set_exchange(self, account: int, created: str = None, rate: float = None, description: str = None,
                     debug: bool = False) -> bool:
        if debug:
            print('exchange', f'debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if rate <= 0:
            return False
        if not self.account_exists(account):
            self.track(account=account, debug=debug)
        self._vault['account'][account]['exchange'][created] = {"rate": rate, "description": description}
        if debug:
            print("exchange-created-1",
                  f'account: {account}, created: {created}, rate:{rate}, description:{description}')
        return True

    def exchange(self, account: int, created: str = None, debug: bool = False) -> dict:
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if created is None:
            created = Helper.time()
        if self.account_exists(account):
            valid_rates = [
                (ts, r)
                for ts, r in self._vault['account'][account]['exchange'].items()
                if Helper.iso8601_to_int(ts, strict=False, debug=debug) <=
                   Helper.iso8601_to_int(created, strict=False, debug=debug)
            ]
            if valid_rates:
                latest_rate = max(valid_rates, key=lambda x: x[0])
                if debug:
                    print("exchange-read-1", f'account={account}, created={created}, latest_rate={latest_rate}')
                result = latest_rate[1]
                result['time'] = latest_rate[0]
                return result  # إرجاع قاموس يحتوي على المعدل والوصف
        if debug:
            print("exchange-read-0", f'account: {account}, created: {created}')
        return {"time": created, "rate": 1, "description": None}  # إرجاع القيمة الافتراضية مع وصف فارغ

    def add_file(self, account: int, ref: str, path: str) -> str | None:
        if self.account_exists(account):
            if ref in self._vault['account'][account]['log']:
                file_ref = Helper.time()
                self._vault['account'][account]['log'][ref]['file'][file_ref] = path
                return file_ref
        return None

    def remove_file(self, account: int, ref: str, file_ref: str) -> bool:
        if self.account_exists(account):
            if ref in self._vault['account'][account]['log']:
                if file_ref in self._vault['account'][account]['log'][ref]['file']:
                    del self._vault['account'][account]['log'][ref]['file'][file_ref]
                    return True
        return False

    def balance(self, account_id: int = 1, cached: bool = True) -> int:
        if not isinstance(account_id, int):
            raise ValueError(f'The account must be an integer, {type(account_id)} was provided.')
        if cached:
            return self._vault['account'][account_id]['balance']
        x = 0
        return [x := x + y['rest'] for y in self._vault['account'][account_id]['box'].values()][-1]

    def hide(self, account_id: int, status: bool = None) -> bool:
        if self.account_exists(account_id):
            if status is None:
                return self._vault['account'][account_id]['hide']
            self._vault['account'][account_id]['hide'] = status
            return status
        return False

    def zakatable(self, account_id: int, status: bool = None) -> bool:
        if self.account_exists(account_id):
            if status is None:
                return self._vault['account'][account_id]['zakatable']
            self._vault['account'][account_id]['zakatable'] = status
            return status
        return False

    def name(self, account_id: int) -> str | None:
        if account_id in self._vault['account']:
            if 'name' in self._vault['account'][account_id]:
                return self._vault['account'][account_id]['name']
        return None

    def account(self, name: str = None, ref: int = None) -> tuple[int, str] | None:
        if not name and not ref:
            return None
        if 'name' not in self._vault:
            self._vault['name'] = {
                'last_account': 0,
                'account': {},
            }

        def set_name(_account: int, _name: str):
            if not self.account_exists(_account):
                self.track(account=_account)
            self._vault['account'][_account]['name'] = _name
            self._vault['name']['account'][_name] = _account
            self._vault['name']['account'][_account] = _name

        if ref and not name:
            if ref not in self._vault['name']['account']:
                return None

        if name and ref:
            if name in self._vault['name']['account']:
                raise Exception('Name is already used')
            if ref in self._vault['name']['account']:
                old_name = self._vault['name']['account'][ref]
                del self._vault['name']['account'][ref]
                if old_name in self._vault['name']['account']:
                    del self._vault['name']['account'][old_name]

            set_name(ref, name)
            return ref, name

        if name not in self._vault['name']['account']:
            account = self._vault['name']['last_account']
            account += 1
            self._vault['name']['last_account'] = account
            self._vault['name']['account'][name] = account
            self._vault['name']['account'][account] = name
            set_name(account, name)
        return self._vault['name']['account'][name], name

    def sub(self, unscaled_value: float | int | Decimal, desc: str = '', account: int = 1, created: str = None,
            debug: bool = False) \
            -> tuple[
                   str,
                   list[
                       tuple[str, int],
                   ],
               ] | tuple:
        if debug:
            print('sub', f'debug={debug}')
        if unscaled_value < 0:
            return tuple()
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if unscaled_value == 0:
            ref = self.track(unscaled_value, '', account)
            return ref, ref
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        self.track(0, '', account)
        value = Helper.scale(unscaled_value)
        self.log(value=-value, desc=desc, account_id=account, created=created, ref=None, debug=debug)
        ids = sorted(self._vault['account'][account]['box'].keys())
        limit = len(ids) + 1
        target = value
        if debug:
            print('ids', ids)
        ages = []
        for i in range(-1, -limit, -1):
            if target == 0:
                break
            j = ids[i]
            if debug:
                print('i', i, 'j', j)
            rest = self._vault['account'][account]['box'][j]['rest']
            if rest >= target:
                self._vault['account'][account]['box'][j]['rest'] -= target
                ages.append((j, target))
                target = 0
                break
            elif target > rest > 0:
                chunk = rest
                target -= chunk
                ages.append((j, chunk))
                self._vault['account'][account]['box'][j]['rest'] = 0
        if target > 0:
            self.track(
                unscaled_value=Helper.unscale(-target),
                desc=desc,
                account=account,
                logging=False,
                created=created,
            )
            ages.append((created, target))
        return created, ages

    def transfer(self, unscaled_amount: float | int | Decimal, from_account: int, to_account: int, desc: str = '',
                 created: str = None,
                 debug: bool = False) -> list[str]:
        if debug:
            print('transfer', f'debug={debug}')
        if from_account == to_account:
            raise ValueError(f'Transfer to the same account is forbidden. {to_account}')
        if unscaled_amount <= 0:
            return []
        if not isinstance(to_account, int):
            raise ValueError(f'The to_account must be an integer, {type(to_account)} was provided.')
        if not isinstance(from_account, int):
            raise ValueError(f'The from_account must be an integer, {type(from_account)} was provided.')
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        (_, ages) = self.sub(unscaled_amount, desc, from_account, created, debug=debug)
        times = []
        source_exchange = self.exchange(from_account, created, debug=debug)
        target_exchange = self.exchange(to_account, created, debug=debug)

        if debug:
            print('ages', ages)

        for age, value in ages:
            target_amount = int(Helper.exchange_calc(value, source_exchange['rate'], target_exchange['rate']))
            if debug:
                print('target_amount', target_amount)
            # Perform the transfer
            if self.box_exists(to_account, age):
                if debug:
                    print('box_exists', age)
                capital = self._vault['account'][to_account]['box'][age]['capital']
                rest = self._vault['account'][to_account]['box'][age]['rest']
                if debug:
                    print(
                        f"Transfer(loop) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).")
                if rest + target_amount > capital:
                    self._vault['account'][to_account]['box'][age]['capital'] += target_amount
                self._vault['account'][to_account]['box'][age]['rest'] += target_amount
                y = self.log(value=target_amount, desc=f'TRANSFER {from_account} -> {to_account}',
                             account_id=to_account,
                             created=None, ref=None, debug=debug)
                times.append((age, y))
                continue
            if debug:
                print(
                    f"Transfer(func) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).")
            y = self.track(
                unscaled_value=Helper.unscale(int(target_amount)),
                desc=desc,
                account=to_account,
                logging=True,
                created=age,
                debug=debug,
            )
            times.append(y)
        return times

    def check(self,
              silver_gram_price: float,
              unscaled_nisab: float | int | Decimal = None,
              debug: bool = False,
              now: str = None,
              cycle: float = None,
              ) -> tuple[
        bool,
        list[int],
        dict[int, dict[int, dict[str, Any]]],
    ]:
        if debug:
            print('check', f'debug={debug}')
        now_ms = Helper.time_to_milliseconds(Helper.time() if now is None else now)
        if cycle is None:
            cycle = Helper.TimeCycle()
        if unscaled_nisab is None:
            unscaled_nisab = Helper.Nisab(silver_gram_price)
        nisab = Helper.scale(unscaled_nisab)
        plan = {}
        below_nisab = 0
        brief = [0, 0, 0]
        valid = False
        for x in self._vault['account']:
            if debug:
                print(f'exchanges({x})', self.exchanges(x))
            if not self.zakatable(x):
                continue
            _box = self._vault['account'][x]['box']
            _log = self._vault['account'][x]['log']
            limit = len(_box) + 1
            ids = sorted(self._vault['account'][x]['box'].keys())
            for i in range(-1, -limit, -1):
                j = ids[i]
                rest = float(_box[j]['rest'])
                if rest <= 0:
                    continue
                exchange = self.exchange(x, debug=debug)
                rest = Helper.exchange_calc(rest, float(exchange['rate']), 1)
                brief[0] += rest
                index = limit + i - 1
                jj = j if type(j) is int else Helper.time_to_milliseconds(j)
                epoch = (now_ms - jj) / cycle
                if debug:
                    print(f"Epoch: {epoch}", _box[j])
                last = _box[j]['last'] if type(_box[j]['last']) is int else Helper.time_to_milliseconds(_box[j]['last'])
                if last > 0:
                    epoch = (now_ms - last) / cycle
                if debug:
                    print(f"Epoch: {epoch}")
                epoch = floor(epoch)
                if debug:
                    print(f"Epoch: {epoch}", type(epoch), epoch == 0, 1 - epoch, epoch)
                if epoch == 0:
                    continue
                if debug:
                    print("Epoch - PASSED")
                brief[1] += rest
                if rest >= nisab:
                    total = 0
                    for _ in range(epoch):
                        total += Helper.ZakatCut(float(rest) - float(total))
                    if total > 0:
                        if x not in plan:
                            plan[x] = {}
                        valid = True
                        brief[2] += total
                        plan[x][index] = {
                            'total': total,
                            'count': epoch,
                            'box_time': j,
                            'box_capital': _box[j]['capital'],
                            'box_rest': _box[j]['rest'],
                            'box_last': _box[j]['last'],
                            'box_total': _box[j]['total'],
                            'box_count': _box[j]['count'],
                            'box_log': _log[j]['desc'],
                            'exchange_rate': exchange['rate'],
                            'exchange_time': exchange['time'],
                            'exchange_desc': exchange['description'],
                        }
                else:
                    chunk = Helper.ZakatCut(float(rest))
                    if chunk > 0:
                        if x not in plan:
                            plan[x] = {}
                        if j not in plan[x].keys():
                            plan[x][index] = {}
                        below_nisab += rest
                        brief[2] += chunk
                        plan[x][index] = {
                            'below_nisab': chunk,
                            'total': chunk,
                            'count': epoch,
                            'box_time': j,
                            'box_capital': _box[j]['capital'],
                            'box_rest': _box[j]['rest'],
                            'box_last': _box[j]['last'],
                            'box_total': _box[j]['total'],
                            'box_count': _box[j]['count'],
                            'box_log': _log[j]['desc'],
                            'exchange_rate': exchange['rate'],
                            'exchange_time': exchange['time'],
                            'exchange_desc': exchange['description'],
                        }
        valid = valid or below_nisab >= nisab
        if debug:
            print(f"below_nisab({below_nisab}) >= nisab({nisab})")
        return valid, brief, plan

    def zakat(
            self,
            report: tuple,
            parts: dict[str, dict[str, dict[str, float]] | bool | int | float] = None,
            debug: bool = False,
    ) -> bool:
        if debug:
            print('zakat', f'debug={debug}')
        valid, _, plan = report
        if not valid:
            return valid
        parts_exist = parts is not None
        if parts_exist:
            if Helper.check_payment_parts(parts, debug=debug) != 0:
                return False
        if debug:
            print('######### zakat #######')
            print('parts_exist', parts_exist)
        report_time = Helper.time()
        self._vault['report'][report_time] = report
        created = Helper.time()
        for x in plan:
            target_exchange = self.exchange(x, debug=debug)
            if debug:
                print(plan[x])
                print('-------------')
                print(self._vault['account'][x]['box'])
            ids = sorted(self._vault['account'][x]['box'].keys())
            if debug:
                print('plan[x]', plan[x])
            for i in plan[x].keys():
                j = ids[i]
                if debug:
                    print('i', i, 'j', j)
                self._vault['account'][x]['box'][j]['last'] = created
                amount = Helper.exchange_calc(float(plan[x][i]['total']), 1, float(target_exchange['rate']))
                self._vault['account'][x]['box'][j]['total'] += amount
                self._vault['account'][x]['box'][j]['count'] += plan[x][i]['count']
                if not parts_exist:
                    try:
                        self._vault['account'][x]['box'][j]['rest'] -= amount
                    except TypeError:
                        self._vault['account'][x]['box'][j]['rest'] -= Decimal(amount)
                    self.log(-float(amount), desc='zakat-زكاة', account_id=x, created=None, ref=j, debug=debug)
        if parts_exist:
            for account, part in parts['account'].items():
                if part['part'] == 0:
                    continue
                if debug:
                    print('zakat-part', account, part['rate'])
                target_exchange = self.exchange(account, debug=debug)
                amount = Helper.exchange_calc(part['part'], part['rate'], target_exchange['rate'])
                self.sub(
                    unscaled_value=Helper.unscale(int(amount)),
                    desc='zakat-part-دفعة-زكاة',
                    account=account,
                    debug=debug,
                )
        return True

    def export_json(self, path: str = "data.json") -> bool:
        with open(path, "w") as file:
            json.dump(self._vault, file, indent=4, cls=JSONEncoder)
            return True

    def save(self, path: str = None) -> bool:
        if path is None:
            path = self.path()
        with open(f'{path}.tmp', 'w') as stream:
            # first save in tmp file
            stream.write(camel.dump(self._vault))
            # then move tmp file to original location
            shutil.move(f'{path}.tmp', path)
            return True

    def load(self, path: str = None) -> bool:
        if path is None:
            path = self.path()
        if os.path.exists(path):
            with open(path, 'r') as stream:
                self._vault = camel.load(stream.read())
                return True
        return False

    def import_csv_cache_path(self):
        path = str(self.path())
        ext = self.ext()
        ext_len = len(ext)
        if path.endswith(f'.{ext}'):
            path = path[:-ext_len - 1]
        _, filename = os.path.split(path + f'.import_csv.{ext}')
        return self.base_path(filename)

    @staticmethod
    def test(debug: bool = False) -> bool:
        return True


db = pony.Database()


class Account(db.Entity):
    _table_ = 'account'
    id = pony.PrimaryKey(int, auto=True)
    # When changed to Str the tests duration changed as following:
    # - macOS(intel) 15.1.1 increased from 5 seconds to 01:30 minutes.
    name = pony.Optional(pony.LongStr, unique=True)
    balance = pony.Optional(int, size=64, default=0)
    count = pony.Optional(int, size=64, default=0)
    hide = pony.Optional(bool, default=False)
    zakatable = pony.Optional(bool, default=True)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())
    updated_at = pony.Optional(datetime.datetime)
    box = pony.Set('Box', cascade_delete=False)
    log = pony.Set('Log', cascade_delete=False)
    exchange = pony.Set('Exchange', cascade_delete=False)


class Box(db.Entity):
    _table_ = 'box'
    id = pony.PrimaryKey(int, auto=True)
    account = pony.Required(Account, column='account_id')
    record_date = pony.Required(datetime.datetime, unique=True)
    capital = pony.Required(int, size=64)
    count = pony.Optional(int, size=64, default=0)
    last = pony.Optional(datetime.datetime)
    rest = pony.Required(int, size=64)
    total = pony.Optional(int, size=64, default=0)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())
    updated_at = pony.Optional(datetime.datetime)


class Log(db.Entity):
    _table_ = 'log'
    id = pony.PrimaryKey(int, auto=True)
    account = pony.Required(Account, column='account_id')
    record_date = pony.Required(datetime.datetime, unique=True)
    value = pony.Required(int, size=64)
    desc = pony.Required(pony.LongStr)
    ref = pony.Optional(int, size=64)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())
    file = pony.Set('File', cascade_delete=False)


class File(db.Entity):
    _table_ = 'file'
    id = pony.PrimaryKey(int, auto=True)
    log = pony.Required(Log, column='log_id')
    record_date = pony.Required(datetime.datetime, unique=True)
    path = pony.Required(pony.LongStr)
    name = pony.Optional(pony.LongStr)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())
    updated_at = pony.Optional(datetime.datetime)


class Exchange(db.Entity):
    _table_ = 'exchange'
    id = pony.PrimaryKey(int, auto=True)
    account = pony.Required(Account, column='account_id')
    record_date = pony.Required(datetime.datetime, unique=True)
    rate = pony.Required(Decimal)
    desc = pony.Optional(pony.LongStr)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())


class Report(db.Entity):
    _table_ = 'report'
    id = pony.PrimaryKey(int, auto=True)
    record_date = pony.Required(datetime.datetime, unique=True)
    details = pony.Required(pony.Json)
    created_at = pony.Required(datetime.datetime, default=lambda: datetime.datetime.now())


class SQLModel(Model):
    """
    A model that maps to a SQLite database tables.

    This class provides a convenient way to interact with SQLite data, encapsulating database operations.
    It may offer features like automatic mapping to database columns, validation, and query building.
    """

    def __init__(self, **db_params):
        """
        Initializes a new SQLModel instance.

        Parameters:
        provider (str, required): The database engine like: (sqlite, postgres, mysql, oracle & cockroach)
        filename (str, optional): The path to the SQLite database file, if database provider is sqlite.
        debug (bool, optional): Flag to enable debug mode. Default is False.

        Examples:
        SQLModel(provider='sqlite', filename=':sharedmemory:')
        SQLModel(provider='sqlite', filename='db.sqlite', create_db=True)
        SQLModel(provider='postgres', user='', password='', host='', database='')
        SQLModel(provider='mysql', host='', user='', passwd='', db='')
        SQLModel(provider='oracle', user='', password='', dsn='')
        SQLModel(provider='cockroach', user='', password='', host='', database='', sslmode='disable')
        SQLModel(provider='cockroach', user='', password='', host='', database='', sslmode='require',
                 port=26257, sslrootcert='certs/ca.crt', sslkey='certs/client.maxroach.key',
                 sslcert='certs/client.maxroach.crt')
        """

        self._base_path = None
        self._vault_path = None
        self._db_path = None
        self.debug = False
        self._file_exists = False
        self.raw_sql = True
        self.provider = str.lower(db_params['provider'])

        if self.provider == 'sqlite' and 'filename' in db_params:
            db_params['filename'] = str(self.path(db_params['filename']))
            self._db_path = db_params['filename']
            self._file_exists = True

        if 'debug' in db_params:
            if type(db_params['debug']) is not bool:
                raise ValueError('debug should be bool type')
            pony.set_sql_debug(db_params['debug'])
            self.debug = db_params['debug']
            del db_params['debug']

        db.bind(**db_params)
        db.generate_mapping(create_tables=True)

    def path(self, path: str = None) -> str:
        if path is None:
            return self._vault_path
        self._vault_path = Path(path).resolve()
        base_path = Path(path).resolve()
        if base_path.is_file() or base_path.suffix:
            base_path = base_path.parent
        base_path.mkdir(parents=True, exist_ok=True)
        self._base_path = base_path
        return str(self._vault_path)

    def file_exists(self) -> bool:
        return self._file_exists

    @pony.db_session
    def sub(self, unscaled_value: float | int | Decimal, desc: str = '', account: int = 1, created: str = None,
            debug: bool = False) \
            -> tuple[
                   str,
                   list[
                       tuple[str, int],
                   ],
               ] | tuple:
        return self._sub(unscaled_value, desc, account, created, debug)

    def _sub(self, unscaled_value: float | int | Decimal, desc: str = '', account: int = 1, created: str = None,
             debug: bool = False) \
            -> tuple[
                   str,
                   list[
                       tuple[str, int],
                   ],
               ] | tuple:
        if debug:
            print('sub', f'debug={debug}')
        if unscaled_value < 0:
            return tuple()
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if unscaled_value == 0:
            ref = self._track(unscaled_value, '', account)
            return ref, ref
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        self._track(0, '', account)
        value = Helper.scale(unscaled_value)
        self._log(value=-value, desc=desc, account_id=account, created=created, ref=None, debug=debug)
        target = value
        ages = []
        if self.raw_sql:
            boxes = db.execute(f'''
                SELECT      id, rest, record_date
                FROM        box
                WHERE       account_id = {account}
                ORDER BY    id DESC;
            ''').fetchall()
            if debug:
                print('boxes', boxes)
            for ref, rest, record_date in boxes:
                if debug:
                    print(f'ref={ref}, rest={rest}, record_date={record_date}')
                if target == 0:
                    break
                if rest >= target:
                    rest -= target
                    ages.append((record_date, target))
                    target = 0
                    db.execute(f'''
                        UPDATE  box
                        SET     rest = {rest}
                        WHERE   id = {ref};
                    ''')
                    break
                elif target > rest > 0:
                    chunk = rest
                    target -= chunk
                    ages.append((record_date, chunk))
                    rest = 0
                    db.execute(f'''
                        UPDATE  box
                        SET     rest = {rest}
                        WHERE   id = {ref};
                    ''')
        else:
            selected_account = Account.get(id=account)
            boxes = selected_account.box.select().order_by(pony.desc(Box.id))[:]
            if debug:
                print('boxes', boxes)
            for box in boxes:
                if target == 0:
                    break
                rest = box.rest
                if rest >= target:
                    box.rest -= target
                    ages.append((box.record_date, target))
                    target = 0
                    break
                elif target > rest > 0:
                    chunk = rest
                    target -= chunk
                    ages.append((box.record_date, chunk))
                    box.rest = 0
        if target > 0:
            self._track(
                unscaled_value=Helper.unscale(-target),
                desc=desc,
                account=account,
                logging=False,
                created=created,
            )
            ages.append((created, target))
        return created, ages

    @pony.db_session
    def track(self, unscaled_value: float | int | Decimal = 0, desc: str = '', account: int = 1, logging: bool = True,
              created: str = None, debug: bool = False) -> str | None:
        return self._track(unscaled_value, desc, account, logging, created, debug)

    def _track(self, unscaled_value: float | int | Decimal = 0, desc: str = '', account: int = 1, logging: bool = True,
               created: str = None, debug: bool = False) -> str | None:
        if debug:
            print('track', f'unscaled_value={unscaled_value}, debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        if not self._account_exists(account):
            if debug:
                print(f"account {account} created")
            if self.raw_sql:
                db.execute(f'''
                    INSERT INTO account (id, hide, zakatable, created_at)
                    VALUES({account}, 0, 1, "{str(datetime.datetime.now())}");
                ''')
            else:
                Account(
                    id=account,
                    hide=False,
                    zakatable=True,
                )
        if unscaled_value == 0:
            return None
        value = Helper.scale(unscaled_value)
        if logging:
            self._log(value=value, desc=desc, account_id=account, created=created, ref=None, debug=debug)
        if debug:
            print('creating-box', created)
        if self._box_exists(account, created):
            raise ValueError(f"The box transaction happened again in the same time({created}).")
        if self.raw_sql:
            db.execute(f'''
                INSERT INTO box (account_id, record_date, capital, count, last, rest, total, created_at)
                            VALUES(
                                {account},
                                "{created}",
                                {value},
                                0,
                                NULL,
                                {value},
                                0,
                                "{str(datetime.datetime.now())}"
                            );
            ''')
        else:
            Box(
                account=account,
                record_date=Helper.time_to_datetime(created),
                capital=value,
                count=0,
                last=None,
                rest=value,
                total=0,
            )
        if debug:
            print('created-box', created)
        return created

    @pony.db_session
    def add_file(self, account: int, ref: str, path: str) -> str | None:
        return self._add_file(account, ref, path)

    def _add_file(self, account: int, ref: str, path: str) -> str | None:
        if self._account_exists(account):
            file_ref = Helper.time()
            if self.raw_sql:
                log = db.execute(f'''
                        SELECT  id
                        FROM    log
                        WHERE   record_date = "{ref}";
                    ''').fetchone()
                print(f'log = {log}')
                if log:
                    db.execute(f'''
                        INSERT INTO file (log_id, record_date, path, name, created_at)
                                    VALUES(
                                        {log[0]},
                                        "{file_ref}",
                                        "{path}",
                                        "",
                                        "{str(datetime.datetime.now())}"
                                    );
                    ''')
                    return file_ref
            log = Log.get(record_date=ref)
            if log:
                File(
                    log=log.id,
                    record_date=file_ref,
                    path=path,
                )
                return file_ref
        return None

    @pony.db_session
    def remove_file(self, account: int, ref: str, file_ref: str) -> bool:
        return self._remove_file(account, ref, file_ref)

    def _remove_file(self, account: int, ref: str, file_ref: str) -> bool:
        if self._account_exists(account):
            if self._log_exists(account, ref):
                if self.raw_sql:
                    file = db.execute(f'''
                        SELECT  id
                        FROM    file
                        WHERE   record_date = "{file_ref}";
                    ''').fetchone()
                    if file:
                        db.execute(f'''
                            DELETE FROM file
                            WHERE   id = {file[0]};
                        ''')
                        return True
                    return False
                file = File.get(record_date=file_ref)
                if file:
                    file.delete()
                    return True
        return False

    @pony.db_session
    def hide(self, account_id: int, status: bool = None) -> bool:
        return self._hide(account_id, status)

    def _hide(self, account_id: int, status: bool = None) -> bool:
        account = Account.get(id=account_id)
        if account:
            if status is None:
                return account.hide
            account.hide = status
            return account.hide
        return False

    @pony.db_session
    def zakatable(self, account_id: int, status: bool = None) -> bool:
        return self._zakatable(account_id, status)

    def _zakatable(self, account_id: int, status: bool = None) -> bool:
        if self.raw_sql:
            if status is not None:
                db.execute(f'''
                    UPDATE  account
                    SET     zakatable = {1 if status else 0},
                            updated_at = "{str(datetime.datetime.now())}"
                    WHERE   id = {account_id};
                ''')
            account = db.execute(f'''
                SELECT  zakatable
                FROM    account
                WHERE   id = {account_id};
            ''').fetchone()
            if not account:
                return False
            return True if account[0] else False
        else:
            account = Account.get(id=account_id)
            if account:
                if status is None:
                    return account.zakatable
                account.zakatable = status
                return account.zakatable
        return False

    @pony.db_session
    def name(self, account_id: int) -> str | None:
        return self._name(account_id)

    def _name(self, account_id: int) -> str | None:
        account = Account.get(id=account_id)
        if account:
            return account.name
        return None

    @pony.db_session
    def accounts(self) -> dict:
        return self._accounts()

    def _accounts(self) -> dict:
        result = {}
        if self.raw_sql:
            x = db.execute(f'''
                SELECT  id, balance
                FROM    account
            ''')
            for ref, balance in x.fetchall():
                result[ref] = balance
        else:
            for account in Account.select()[:]:
                result[account.id] = account.balance
        return result

    @pony.db_session
    def set_exchange(self, account: int, created: str = None, rate: float = None, description: str = None,
                     debug: bool = False) -> bool:
        return self._set_exchange(account, created, rate, description, debug)

    def _set_exchange(self, account: int, created: str = None, rate: float = None, description: str = None,
                      debug: bool = False) -> bool:
        if debug:
            print('exchange', f'debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if rate <= 0:
            return False
        if not self._account_exists(account):
            self._track(account=account, debug=debug)
        if self.raw_sql:
            db.execute(f'''
                INSERT INTO exchange (account_id, record_date, rate, desc, created_at)
                            VALUES(
                                {account},
                                "{created}",
                                {rate},
                                "{description if description else ''}",
                                "{str(datetime.datetime.now())}"
                            );
            ''')
        else:
            Exchange(
                account=account,
                rate=rate,
                desc=description if description else '',
                record_date=Helper.time_to_datetime(created),
            )
        if debug:
            print("exchange-created-1",
                  f'account: {account}, created: {created}, rate:{rate}, description:{description}')
        return True

    @pony.db_session
    def exchange(self, account: int, created: str = None, debug: bool = False) -> dict:
        return self._exchange(account, created, debug)

    def _exchange(self, account: int, created: str = None, debug: bool = False) -> dict:
        if debug:
            print('exchange', f'debug={debug}')
        if not isinstance(account, int):
            raise ValueError(f'The account must be an integer, {type(account)} was provided.')
        if created is None:
            created = Helper.time()
        if self.raw_sql:
            exchange = db.execute(f'''
                SELECT      record_date, rate, desc
                FROM        exchange
                WHERE       account_id = {account}                          AND
                            datetime(record_date) <= datetime("{created}")
                ORDER BY    record_date DESC
                LIMIT       1;
            ''').fetchone()
            if debug:
                print('valid_rates', exchange, type(exchange), exchange)
            if exchange:
                return {
                    "time": exchange[0],
                    "rate": exchange[1],
                    "description": exchange[2] if exchange[2] else None,
                }
        else:
            exchange = Exchange.select(
                lambda e: e.account.id == account and e.record_date <= created
            ).order_by(pony.desc(Exchange.record_date)).first()
            if debug:
                print('valid_rates', exchange, type(exchange), exchange)
            if exchange:
                if debug:
                    print("exchange-read-1", f'account={account}, created={created}, latest_rate={exchange}')
                return {
                    "time": exchange.record_date,
                    "rate": exchange.rate,
                    "description": exchange.desc if exchange.desc else None,
                }
        if debug:
            print("exchange-read-0", f'account: {account}, created: {created}')
        return {"time": created, "rate": 1, "description": None}  # إرجاع القيمة الافتراضية مع وصف فارغ

    @pony.db_session()
    def exchanges(self, account: int) -> dict | None:
        return self._exchanges(account)

    def _exchanges(self, account: int) -> dict | None:
        if self._account_exists(account):
            result = {}
            for exchange in Exchange.select(lambda e: e.account.id == account)[:]:
                result[exchange.record_date] = exchange.to_dict()
            if result:
                return result
        return None

    @pony.db_session
    def account(self, name: str = None, ref: int = None) -> tuple[int, str] | None:
        return self._account(name, ref)

    def _account(self, name: str = None, ref: int = None) -> tuple[int, str] | None:
        if not name and not ref:
            return None
        if name and not ref:
            account = Account.get(name=name)
            if not account:
                account = Account(name=name)
                pony.commit()
            return account.id, account.name
        if ref and not name:
            account = Account.get(id=ref)
            if not account:
                return None
            return account.id, account.name
        if name and ref:
            account = Account.get(id=ref)
            if account:
                if account.name != name:
                    account.name = name
                return account.id, account.name
            account = Account(id=ref, name=name)
            return account.id, account.name

    @pony.db_session
    def transfer(self, unscaled_amount: float | int | Decimal, from_account: int, to_account: int, desc: str = '',
                 created: str = None,
                 debug: bool = False) -> list[str]:
        return self._transfer(unscaled_amount, from_account, to_account, desc, created, debug)

    def _transfer(self, unscaled_amount: float | int | Decimal, from_account: int, to_account: int, desc: str = '',
                  created: str = None,
                  debug: bool = False) -> list[str]:
        if debug:
            print('transfer', f'debug={debug}')
        if from_account == to_account:
            raise ValueError(f'Transfer to the same account is forbidden. {to_account}')
        if unscaled_amount <= 0:
            return []
        if not isinstance(to_account, int):
            raise ValueError(f'The to_account must be an integer, {type(to_account)} was provided.')
        if not isinstance(from_account, int):
            raise ValueError(f'The from_account must be an integer, {type(from_account)} was provided.')

        if created is None:
            created = Helper.time()
        (_, ages) = self._sub(unscaled_amount, desc, from_account, created, debug=debug)
        times = []
        source_exchange = self._exchange(from_account, created)
        target_exchange = self._exchange(to_account, created)

        if debug:
            print('ages', ages)

        for age, value in ages:
            target_amount = int(Helper.exchange_calc(value, source_exchange['rate'], target_exchange['rate']))
            if debug:
                print('target_amount', target_amount)
            # Perform the transfer
            new_age = Helper.int_to_iso8601(Helper.iso8601_to_int(age), extra_ms=1)
            if debug:
                print(f'old_age = {age}')
                print(f'new_age = {new_age}')
            if self.raw_sql:
                box = db.execute(f'''
                    SELECT  id, rest, capital
                    FROM    box
                    WHERE   account_id = {to_account}                   AND
                            datetime(record_date) = datetime("{age}")
                    LIMIT   1; 
                ''').fetchone()
                if debug:
                    print('box_exists', box)
                if box:
                    if debug:
                        print(
                            f"Transfer(loop) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).")
                    ref, rest, capital = box
                    if rest + target_amount > capital:
                        capital += target_amount
                    rest += target_amount
                    db.execute(f'''
                        UPDATE  box
                        SET     capital = {capital},
                                rest = {rest}
                        WHERE   id = {ref};
                    ''')
                    y = self._log(value=target_amount, desc=f'TRANSFER {from_account} -> {to_account}',
                                  account_id=to_account,
                                  created=None, ref=None, debug=debug)
                    times.append((age, y))
                    continue
            else:
                box = Box.get(account=to_account, record_date=age)
                if debug:
                    print('box_exists', box)
                if box:
                    if debug:
                        print(
                            f"Transfer(loop) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).")
                    if box.rest + target_amount > box.capital:
                        box.capital += target_amount
                    box.rest += target_amount
                    y = self._log(value=target_amount, desc=f'TRANSFER {from_account} -> {to_account}',
                                  account_id=to_account,
                                  created=None, ref=None, debug=debug)
                    times.append((age, y))
                    continue
            if debug:
                print(
                    f"Transfer(func) {value} from `{from_account}` to `{to_account}` (equivalent to {target_amount} `{to_account}`).")
            y = self._track(
                unscaled_value=Helper.unscale(int(target_amount)),
                desc=desc,
                account=to_account,
                logging=True,
                created=new_age,
                debug=debug,
            )
            times.append(y)
        return times

    @pony.db_session
    def account_exists(self, account: int) -> bool:
        return self._account_exists(account)

    def _account_exists(self, account: int) -> bool:
        if self.raw_sql:
            x = db.execute(f'''
                SELECT  COUNT(*) > 0
                FROM    account
                WHERE   id = {account};
            ''').fetchone()
            if not x:
                return False
            return True if x[0] else False
        return Account.exists(id=account)

    def files(self) -> list[dict[str, str | int]]:
        pass

    def stats(self, ignore_ram: bool = True) -> dict[str, tuple[int, str]]:
        pass

    @pony.db_session
    def logs(self, account_id: int) -> dict:
        return self._logs(account_id)

    def _logs(self, account_id: int) -> dict:
        account = Account.get(id=account_id)
        if account:
            return {l.record_date: l.to_dict() for l in account.log.select()[:]}
        return {}

    @pony.db_session
    def boxes(self, account_id: int) -> dict:
        return self._boxes(account_id)

    def _boxes(self, account_id: int) -> dict:
        account = Account.get(id=account_id)
        if account:
            return {b.record_date: b.to_dict() for b in account.box.select()[:]}
        return {}

    @pony.db_session
    def balance(self, account_id: int = 1, cached: bool = True) -> int:
        return self._balance(account_id, cached)

    def _balance(self, account_id: int = 1, cached: bool = True) -> int:
        if not isinstance(account_id, int):
            raise ValueError(f'The account must be an integer, {type(account_id)} was provided.')
        if cached:
            return Account.get(id=account_id).balance
        return pony.sum(b.rest for b in Box if b.account.id == account_id)

    @pony.db_session
    def box_size(self, account_id: int) -> int:
        return self._box_size(account_id)

    def _box_size(self, account_id: int) -> int:
        account = Account.get(id=account_id)
        if account:
            return len(account.box)
        return -1

    @pony.db_session
    def log_size(self, account_id: int) -> int:
        return self._log_size(account_id)

    def _log_size(self, account_id: int) -> int:
        account = Account.get(id=account_id)
        if account:
            return len(account.log)
        return -1

    def save(self, path: str = None) -> bool:
        if path is None:
            path = self.path()
        db.commit()
        if path != self._db_path and self._db_path:
            shutil.copy(self._db_path, path)
        return True

    def load(self, path: str = None) -> bool:
        return False
        if path is None:
            path = self.path()
        if os.path.exists(path):
            with open(path, 'r') as stream:
                self._vault = camel.load(stream.read())
                return True
        return False

    def reset(self) -> None:
        db.drop_all_tables(with_all_data=True)
        db.create_tables()

    @pony.db_session
    def check(self,
              silver_gram_price: float,
              unscaled_nisab: float | int | Decimal = None,
              debug: bool = False,
              now: str = None,
              cycle: float = None,
              ) -> tuple[
        bool,
        list[int],
        dict[int, dict[int, dict[str, Any]]],
    ]:
        return self._check(silver_gram_price, unscaled_nisab, debug, now, cycle)

    def _check(self,
               silver_gram_price: float,
               unscaled_nisab: float | int | Decimal = None,
               debug: bool = False,
               now: str = None,
               cycle: float = None,
               ) -> tuple[
        bool,
        list[int],
        dict[int, dict[int, dict[str, Any]]],
    ]:
        if debug:
            print('check', f'debug={debug}')
        now = Helper.time() if now is None else now
        if debug:
            print(f'now = [{now}]')
        now_ms = Helper.time_to_milliseconds(now)
        if not self.raw_sql:
            raise Exception('Not Implemented')
        if debug:
            print(f'now_ms = [{now_ms}]')
        if cycle is None:
            cycle = Helper.TimeCycle()
        if unscaled_nisab is None:
            unscaled_nisab = Helper.Nisab(silver_gram_price)
        nisab = Helper.scale(unscaled_nisab)
        plan = {}
        below_nisab = 0
        brief = [0, 0, 0]
        valid = False
        boxes = db.execute(f'''
            SELECT      b.id, b.rest, b.record_date, b.last, b.account_id, b.capital, b.total, b.count, l.desc
            From        box AS b
            LEFT JOIN   log AS l ON l.record_date = b.record_date 
            WHERE       b.rest > 0										AND
                        datetime(b.record_date) <= datetime("{now}")
            ORDER BY	b.record_date DESC;
        ''').fetchall()
        if debug:
            print(f'boxes = {boxes}')
        index = 0
        for ref, rest, record_date, last, account_id, capital, box_total, count, desc in boxes:
            if debug:
                print(
                    f'ref = {ref}, rest = {rest}, record_date = {record_date}, last = {last}, account_id = {account_id}, capital = {capital}, total = {box_total}, count = {count}, desc = {desc}')
            exchange = self.exchange(account_id, debug=debug)
            if debug:
                print(f'exchange <=> {exchange}')
            rest = Helper.exchange_calc(rest, float(exchange['rate']), 1)
            brief[0] += rest
            j = Helper.time_to_milliseconds(record_date)
            epoch = (now_ms - j) / cycle
            last_ms = Helper.time_to_milliseconds(last) if last else 0
            if last_ms > 0:
                epoch = (now_ms - last_ms) / cycle
            if debug:
                print(f"Epoch: {epoch}")
            epoch = floor(epoch)
            if debug:
                print(f"Epoch: {epoch}", type(epoch), epoch == 0, 1 - epoch, epoch)
            if epoch == 0:
                continue
            if debug:
                print("Epoch - PASSED")
            brief[1] += rest
            x = account_id
            if rest >= nisab:
                total = 0
                for _ in range(epoch):
                    total += Helper.ZakatCut(float(rest) - float(total))
                if total > 0:
                    if x not in plan:
                        plan[x] = {}
                    valid = True
                    brief[2] += total
                    plan[x][index] = {
                        'ref': ref,
                        'total': total,
                        'count': epoch,
                        'box_time': record_date,
                        'box_capital': capital,
                        'box_rest': rest,
                        'box_last': last,
                        'box_total': box_total,
                        'box_count': count,
                        'box_log': desc,
                        'exchange_rate': exchange['rate'],
                        'exchange_time': exchange['time'],
                        'exchange_desc': exchange['description'],
                    }
                    index += 1
                else:
                    chunk = Helper.ZakatCut(float(rest))
                    if chunk > 0:
                        if x not in plan:
                            plan[x] = {}
                        # if j not in plan[x].keys():
                        #     plan[x][index] = {}
                        below_nisab += rest
                        brief[2] += chunk
                        plan[x][index] = {
                            'ref': ref,
                            'below_nisab': chunk,
                            'total': chunk,
                            'count': epoch,
                            'box_time': record_date,
                            'box_capital': capital,
                            'box_rest': rest,
                            'box_last': last,
                            'box_total': box_total,
                            'box_count': count,
                            'box_log': desc,
                            'exchange_rate': exchange['rate'],
                            'exchange_time': exchange['time'],
                            'exchange_desc': exchange['description'],
                        }
                        index += 1
                    #
                #
            #
        valid = valid or below_nisab >= nisab
        if debug:
            print(f"below_nisab({below_nisab}) >= nisab({nisab})")
        return valid, brief, plan

    @pony.db_session
    def zakat(
            self,
            report: tuple, parts: dict[str, dict[str, dict[str, float]] | bool | int | float] = None,
            debug: bool = False,
    ) -> bool:
        return self._zakat(report, parts, debug)

    def _zakat(
            self,
            report: tuple, parts: dict[str, dict[str, dict[str, float]] | bool | int | float] = None,
            debug: bool = False,
    ) -> bool:
        if debug:
            print('zakat', f'debug={debug}')
        if not self.raw_sql:
            raise Exception('Not Implemented')
        valid, _, plan = report
        if not valid:
            return valid
        parts_exist = parts is not None
        if parts_exist:
            if Helper.check_payment_parts(parts, debug=debug) != 0:
                return False
        if debug:
            print('######### zakat #######')
            print('parts_exist', parts_exist)
        report_time = Helper.time()
        db.execute(f'''
            INSERT INTO report(record_date, details, created_at)
                        VALUES(
                            "{report_time}",
                            '{json.dumps(report)}',
                            "{str(datetime.datetime.now())}"
                        );
        ''')
        created = Helper.time()
        for x, boxes in plan.items():
            target_exchange = self.exchange(x, debug=debug)
            if debug:
                print(f'plan[{x}]', boxes)
                print('-------------')
            for index, box in boxes.items():
                if debug:
                    print('i', index, 'box', box)
                amount = Helper.exchange_calc(float(box['total']), 1, float(target_exchange['rate']))
                db.execute(f'''
                    UPDATE  box
                    SET     last = "{created}",
                            total = total + {amount},
                            count = count + {box['count']}
                    WHERE   id = {box['ref']};
                ''')
                if not parts_exist:
                    db.execute(f'''
                        UPDATE  box
                        SET     rest = rest - {box['box_rest']}
                        WHERE   id = {box['ref']};
                    ''')
                    self.log(-float(amount), desc='zakat-زكاة', account_id=x, created=None, ref=box['box_time'],
                             debug=debug)
        if parts_exist:
            for account, part in parts['account'].items():
                if part['part'] == 0:
                    continue
                if debug:
                    print('zakat-part', account, part['rate'])
                target_exchange = self.exchange(account, debug=debug)
                amount = Helper.exchange_calc(part['part'], part['rate'], target_exchange['rate'])
                self.sub(
                    unscaled_value=Helper.unscale(int(amount)),
                    desc='zakat-part-دفعة-زكاة',
                    account=account,
                    debug=debug,
                )
        return True

    def import_csv_cache_path(self):
        path = str(self.path())
        ext = self.ext()
        ext_len = len(ext)
        if path.endswith(f'.{ext}'):
            path = path[:-ext_len - 1]
        _, filename = os.path.split(f'{path}.import_csv.{ext}.camel')
        return f'{self._base_path}/{filename}'

    def daily_logs(self, weekday: WeekDay = WeekDay.Friday, debug: bool = False):
        return {
            'daily': True,
            'weekly': True,
            'monthly': True,
            'yearly': True,
        }

    def export_json(self, path: str = "data.json") -> bool:
        with open(path, "w") as file:
            json.dump(self.vault(), file, indent=4, cls=JSONEncoder)
            return True

    @pony.db_session()
    def vault(self, section: Vault = Vault.ALL) -> dict:
        account = {}
        name = {}
        report = {}
        all: bool = section == Vault.ALL

        if section == Vault.ACCOUNT or all:
            for k, v in {
                a.id: a.to_dict(with_lazy=True, with_collections=True, related_objects=True)
                for a in Account.select()[:]
            }.items():
                account[k] = v
                if v['box']:
                    box = {}
                    for b in v['box']:
                        box[b.record_date] = b.to_dict()
                    account[k]['box'] = box

                if v['log']:
                    log = {}
                    for l in v['log']:
                        log[l.record_date] = l.to_dict(with_lazy=True, with_collections=True, related_objects=True)
                    account[k]['log'] = log

                if v['exchange']:
                    exchange = {}
                    for e in v['exchange']:
                        exchange[e.record_date] = e.to_dict(with_lazy=True, with_collections=True, related_objects=True)
                    account[k]['exchange'] = exchange

        if section == Vault.NAME or all:
            for k, v in {
                a.id: a.to_dict(only=['id', 'name'])
                for a in Account.select()[:]
            }.items():
                name[k] = v['name']
                name[v['name']] = k

        if section == Vault.REPORT or all:
            report = Report.select()[:]

        if section == Vault.ACCOUNT:
            return account

        if section == Vault.NAME:
            return {
                'account': name,
            }

        return {
            'account': account,
            'name': name,
            'report': report,
        }

    def snapshot(self) -> bool:
        return True

    def ext(self) -> str | None:
        return 'sqlite' if self._file_exists else None

    @pony.db_session
    def log(self, value: float, desc: str = '', account_id: int = 1, created: str = None, ref: int = None,
            debug: bool = False) -> str:
        return self._log(value, desc, account_id, created, ref, debug)

    def _log(self, value: float, desc: str = '', account_id: int = 1, created: str = None, ref: int = None,
             debug: bool = False) -> str:
        if debug:
            print('_log', f'debug={debug}')
        if created is None:
            created = Helper.time()
        if not isinstance(created, str):
            raise ValueError(f'The created must be a str, {type(created)} was provided.')
        if self.raw_sql:
            db.execute(f'''
                UPDATE  account
                SET     balance = COALESCE(balance, 0) + {value},
                        count = COALESCE(count, 0) + 1,
                        updated_at = "{str(datetime.datetime.now())}"
                WHERE   id = {account_id};
            ''')
        else:
            account = Account.get(id=account_id)
            if account:
                try:
                    account.balance += value
                except TypeError:
                    account.balance += Decimal(value)
                account.count += 1
        if debug:
            print('create-log', created)
        if self._log_exists(account_id, created):
            raise ValueError(f"The log transaction('{desc}') happened again in the same time({created}).")
        if debug:
            print('created-log', created)
        if self.raw_sql:
            db.execute(f'''
                INSERT INTO log (account_id, record_date, value, desc, ref, created_at)
                            VALUES(
                                {account_id},
                                "{created}",
                                {value},
                                "{desc}",
                                {f'"{ref}"' if ref else 'NULL'},
                                "{str(datetime.datetime.now())}"
                            );
            ''')
        else:
            Log(
                account=account_id,
                record_date=Helper.time_to_datetime(created),
                value=value,
                desc=desc,
                ref=ref,
                file={},
            )
        return created

    def ref_exists(self, account_id: int, ref_type: str, ref: str) -> bool:
        if not isinstance(account_id, int):
            raise ValueError(f'The account_id must be an integer, {type(account_id)} was provided.')
        match ref_type:
            case 'box':
                if self.raw_sql:
                    box = db.execute(f'''
                        SELECT  COUNT(*)
                        FROM    box
                        WHERE   account_id = {account_id}   AND
                                record_date = "{ref}";
                    ''').fetchone()
                    if not box:
                        return False
                    return box[0] > 0
                return Box.exists(account=account_id, record_date=ref)
            case 'log':
                if self.raw_sql:
                    log = db.execute(f'''
                        SELECT  COUNT(*)
                        FROM    log
                        WHERE   account_id = {account_id}   AND
                                record_date = "{ref}";
                    ''').fetchone()
                    if not log:
                        return False
                    return log[0] > 0
                return Log.exists(account=account_id, record_date=ref)
        return False

    @pony.db_session
    def box_exists(self, account_id: int, ref: str) -> bool:
        return self._box_exists(account_id, ref)

    def _box_exists(self, account_id: int, ref: str) -> bool:
        return self.ref_exists(account_id=account_id, ref_type='box', ref=ref)

    @pony.db_session
    def log_exists(self, account_id: int, ref: str) -> bool:
        return self._log_exists(account_id, ref)

    def _log_exists(self, account_id: int, ref: str) -> bool:
        return self.ref_exists(account_id=account_id, ref_type='log', ref=ref)

    def snapshots(self, hide_missing: bool = True, verified_hash_only: bool = False) -> dict[
        int, tuple[str, str, bool]]:
        pass

    @staticmethod
    def test(debug: bool = False) -> bool:
        return True


class ZakatTracker:
    """
    A class for tracking and calculating Zakat.

    This class provides functionalities for recording transactions, calculating Zakat due,
    and managing account balances. It also offers features like importing transactions from
    CSV files, exporting data to JSON format, and saving/loading the tracker state.

    The `ZakatTracker` class is designed to handle both positive and negative transactions,
    allowing for flexible tracking of financial activities related to Zakat. It also supports
    the concept of a "Nisab" (minimum threshold for Zakat) and a "haul" (complete one year for Transaction)
    can calculate Zakat due based on the current silver price.

    The class uses a camel file as its database to persist the tracker state,
    ensuring data integrity across sessions.

    In addition, the `ZakatTracker` class includes various helper methods like
    `time`, `time_to_datetime`, `free`, `export_json`,
    and more. These methods provide additional functionalities and flexibility
    for interacting with and managing the Zakat tracker.

    Attributes:
        ZakatTracker.ZakatCut (function): A function to calculate the Zakat percentage.
        ZakatTracker.TimeCycle (function): A function to determine the time cycle for Zakat.
        ZakatTracker.Nisab (function): A function to calculate the Nisab based on the silver price.
        ZakatTracker.Version (function): The version of the ZakatTracker class.

    Data Structure:
        The ZakatTracker class utilizes a nested dictionary structure called "_vault" to store and manage data.

        _vault (dict):
            - account (dict):
                - {account_number} (dict):
                    - balance (int): The current balance of the account.
                    - box (dict): A dictionary storing transaction details.
                        - {timestamp} (dict):
                            - capital (int): The initial amount of the transaction.
                            - count (int): The number of times Zakat has been calculated for this transaction.
                            - last (int): The timestamp of the last Zakat calculation.
                            - rest (int): The remaining amount after Zakat deductions and withdrawal.
                            - total (int): The total Zakat deducted from this transaction.
                    - count (int): The total number of transactions for the account.
                    - exchange (dict):
                        - {timestamps} (dict):
                            - rate (float): Exchange rate when compared to local currency.
                            - description (str): The description of the exchange rate.
                    - log (dict): A dictionary storing transaction logs.
                        - {timestamp} (dict):
                            - value (int): The transaction amount (positive or negative).
                            - desc (str): The description of the transaction.
                            - ref (int): The box reference (positive or None).
                            - file (dict): A dictionary storing file references associated with the transaction.
                    - name (str): The current name of the account.
                    - hide (bool): Indicates whether the account is hidden or not.
                    - zakatable (bool): Indicates whether the account is subject to Zakat.
            - report (dict):
                - {timestamp} (tuple): A tuple storing Zakat report details.

    """

    def __init__(self, model: Model):
        """
        Initialize ZakatTracker with selected model.

        Parameters:
        model (Model): The model is used to handle the algorithm.

        Returns:
        None
        """
        self.db = model

    def build_payment_parts(
            self,
            scaled_demand: int,
            positive_only: bool = True,
            debug: bool = False,
    ) -> dict[str, dict[str, dict[str, float]] | bool | int | float]:
        """
        Build payment parts for the Zakat distribution.

        Parameters:
        scaled_demand (int): The total demand for payment in local currency.
        positive_only (bool): If True, only consider accounts with positive balance. Default is True.

        Returns:
        dict: A dictionary containing the payment parts for each account. The dictionary has the following structure:
        {
            'account': {
                account_id: {'balance': float, 'rate': float, 'part': float},
                ...
            },
            'exceed': bool,
            'demand': int,
            'total': float,
        }
        """
        total = 0
        parts = {
            'account': {},
            'exceed': False,
            'demand': int(round(scaled_demand)),
        }
        for x, y in self.db.accounts().items():
            if positive_only and y <= 0:
                continue
            total += float(y)
            exchange = self.db.exchange(account=x, debug=debug)
            parts['account'][x] = {'balance': y, 'rate': exchange['rate'], 'part': 0}
        parts['total'] = total
        return parts

    def import_csv(self, path: str = 'file.csv', scale_decimal_places: int = 0, debug: bool = False) -> tuple:
        """
        The function reads the CSV file, checks for duplicate transactions, and creates the transactions in the system.

        Parameters:
        path (str): The path to the CSV file. Default is 'file.csv'.
        scale_decimal_places (int): The number of decimal places to scale the value. Default is 0.
        debug (bool): A flag indicating whether to print debug information.

        Returns:
        tuple: A tuple containing the number of transactions created, the number of transactions found in the cache,
                and a dictionary of bad transactions.

        Notes:
            * Currency Pair Assumption: This function assumes that the exchange rates stored for each account
                                        are appropriate for the currency pairs involved in the conversions.
            * The exchange rate for each account is based on the last encountered transaction rate that is not equal
                to 1.0 or the previous rate for that account.
            * Those rates will be merged into the exchange rates main data, and later it will be used for all subsequent
              transactions of the same account within the whole imported and existing dataset when doing `check` and
              `zakat` operations.

        Example Usage:
            The CSV file should have the following format, rate is optional per transaction:
            account, desc, value, date, rate
            For example:
            safe-45, "Some text", 34872, 1988-06-30 00:00:00, 1
        """
        if debug:
            print('import_csv', f'debug={debug}')
        cache: list[int] = []
        try:
            with open(self.db.import_csv_cache_path(), 'r') as stream:
                cache = camel.load(stream.read())
        except:
            pass
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H%M%S",
            "%Y-%m-%d",
        ]
        created, found, bad = 0, 0, {}
        data: dict[int, list] = {}
        with open(path, newline='', encoding="utf-8") as f:
            i = 0
            for row in csv.reader(f, delimiter=','):
                i += 1
                hashed = hash(tuple(row))
                if hashed in cache:
                    found += 1
                    continue
                account = row[0]
                desc = row[1]
                value = float(row[2])
                rate = 1.0
                if row[4:5]:  # Empty list if index is out of range[]
                    rate = float(row[4])
                date: int = 0
                for time_format in date_formats:
                    try:
                        date = Helper.time(datetime.datetime.strptime(row[3], time_format))
                        break
                    except:
                        pass
                # TODO: not allowed for negative dates in the future after enhance time functions
                if date == 0 or date == '' or date is None:
                    bad[i] = row + ['invalid date']
                if value == 0 or value == '' or value is None:
                    bad[i] = row + ['invalid value']
                    continue
                if date not in data:
                    data[date] = []
                data[date].append((i, account, desc, value, date, rate, hashed))

        if debug:
            print('import_csv', len(data))

        if bad:
            return created, found, bad

        for date, rows in sorted(data.items()):
            try:
                len_rows = len(rows)
                if len_rows == 1:
                    (_, account, desc, unscaled_value, date, rate, hashed) = rows[0]
                    account_ref, _ = self.db.account(name=account)
                    value = Helper.unscale(
                        unscaled_value,
                        decimal_places=scale_decimal_places,
                    ) if scale_decimal_places > 0 else unscaled_value
                    if rate > 0:
                        self.db.set_exchange(account=account_ref, created=date, rate=rate)
                    if value > 0:
                        self.db.track(unscaled_value=value, desc=desc, account=account_ref, logging=True, created=date)
                    elif value < 0:
                        self.db.sub(unscaled_value=-value, desc=desc, account=account_ref, created=date)
                    created += 1
                    cache.append(hashed)
                    continue
                if debug:
                    print('-- Duplicated time detected', date, 'len', len_rows)
                    print(rows)
                    print('---------------------------------')
                # If records are found at the same time with different accounts in the same amount
                # (one positive and the other negative), this indicates it is a transfer.
                if len_rows != 2:
                    raise ValueError(f'more than two transactions({len_rows}) at the same time')
                (i, account1, desc1, unscaled_value1, date1, rate1, _) = rows[0]
                (j, account2, desc2, unscaled_value2, date2, rate2, _) = rows[1]
                if account1 == account2 or desc1 != desc2 or abs(unscaled_value1) != abs(
                        unscaled_value2) or date1 != date2:
                    raise ValueError('invalid transfer')
                account1_ref, _ = self.db.account(name=account1)
                account2_ref, _ = self.db.account(name=account2)
                if rate1 > 0:
                    self.db.set_exchange(account1_ref, created=date1, rate=rate1)
                if rate2 > 0:
                    self.db.set_exchange(account2_ref, created=date2, rate=rate2)
                value1 = Helper.unscale(
                    unscaled_value1,
                    decimal_places=scale_decimal_places,
                ) if scale_decimal_places > 0 else unscaled_value1
                value2 = Helper.unscale(
                    unscaled_value2,
                    decimal_places=scale_decimal_places,
                ) if scale_decimal_places > 0 else unscaled_value2
                values = {
                    value1: account1_ref,
                    value2: account2_ref,
                }
                self.db.transfer(
                    unscaled_amount=abs(value1),
                    from_account=values[min(values.keys())],
                    to_account=values[max(values.keys())],
                    desc=desc1,
                    created=date1,
                )
            except Exception as e:
                for (i, account, desc, value, row_date, rate, _) in rows:
                    bad[i] = (account, desc, value, row_date, rate, e)
                break
        with open(self.db.import_csv_cache_path(), 'w') as stream:
            stream.write(camel.dump(cache))
        return created, found, bad

    ########
    # TESTS #
    #######

    @staticmethod
    def generate_random_date(start_date: datetime.datetime, end_date: datetime.datetime) -> datetime.datetime:
        """
        Generate a random date between two given dates.

        Parameters:
        start_date (datetime.datetime): The start date from which to generate a random date.
        end_date (datetime.datetime): The end date until which to generate a random date.

        Returns:
        datetime.datetime: A random date between the start_date and end_date.
        """
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        return start_date + datetime.timedelta(days=random_number_of_days)

    @staticmethod
    def generate_random_csv_file(path: str = "data.csv", count: int = 1000, with_rate: bool = False,
                                 debug: bool = False) -> int:
        """
        Generate a random CSV file with specified parameters.

        Parameters:
        path (str): The path where the CSV file will be saved. Default is "data.csv".
        count (int): The number of rows to generate in the CSV file. Default is 1000.
        with_rate (bool): If True, a random rate between 1.2% and 12% is added. Default is False.
        debug (bool): A flag indicating whether to print debug information.

        Returns:
        None. The function generates a CSV file at the specified path with the given count of rows.
        Each row contains a randomly generated account, description, value, and date.
        The value is randomly generated between 1000 and 100000,
        and the date is randomly generated between 1950-01-01 and 2023-12-31.
        If the row number is not divisible by 13, the value is multiplied by -1.
        """
        if debug:
            print('generate_random_csv_file', f'debug={debug}')
        i = 0
        with open(path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for i in range(count):
                account = f"acc-{random.randint(1, 1000)}"
                desc = f"Some text {random.randint(1, 1000)}"
                value = random.randint(1000, 100000)
                date = ZakatTracker.generate_random_date(datetime.datetime(1000, 1, 1),
                                                         datetime.datetime(2023, 12, 31)).strftime("%Y-%m-%d %H:%M:%S")
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
                writer.writerow(row)
                i = i + 1
        return i

    @staticmethod
    def create_random_list(max_sum, min_value=0, max_value=10):
        """
        Creates a list of random integers whose sum does not exceed the specified maximum.

        Args:
            max_sum: The maximum allowed sum of the list elements.
            min_value: The minimum possible value for an element (inclusive).
            max_value: The maximum possible value for an element (inclusive).

        Returns:
            A list of random integers.
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

    def test(self, debug: bool = False) -> bool:
        if debug:
            print('test', f'debug={debug}')
            random.seed(1234567890)
        try:

            # account numbers & names
            for index, letter in enumerate('abcdefghijklmnopqrstuvwxyz'):
                ref, name = self.db.account(name=letter)
                if debug:
                    print(f'letter = "{letter}", name = "{name}"')
                assert letter == name
                if debug:
                    print(f'index = {index + 1}, ref = {ref}')
                assert index + 1 == ref
                assert index + 1 in self.db.vault(Vault.ACCOUNT)
                assert name == self.db.vault(Vault.ACCOUNT)[index + 1]['name']
            account_z_ref, account_z_name = self.db.account(name='z')
            assert account_z_ref == 26
            assert account_z_name == 'z'
            account_xz_ref, account_xz_name = self.db.account(name='xz')
            assert account_xz_ref == 27
            assert account_xz_name == 'xz'
            assert self.db.account(ref=123) is None
            use_same_account_name_failed = False
            try:
                self.db.account(name='z', ref=321)
            except:
                use_same_account_name_failed = True
            assert use_same_account_name_failed
            account_zzz_ref_new, account_zzz_name_new = self.db.account(name='zzz', ref=321)
            assert self.db.account_exists(account_zzz_ref_new)
            assert account_zzz_ref_new == 321
            assert account_zzz_name_new == 'zzz'
            assert account_z_ref in self.db.vault(Vault.NAME)['account']
            assert self.db.account_exists(account_z_ref)
            account_zz_ref, account_zz_name = self.db.account(name='zz', ref=321)
            assert self.db.account_exists(account_zz_ref)
            assert account_zz_ref == 321
            assert account_zz_name == 'zz'
            assert account_zzz_name_new not in self.db.vault(Vault.NAME)['account']
            account_xx_ref, account_xx_name = self.db.account(name='xx', ref=333)
            assert self.db.account_exists(account_xx_ref)
            assert account_xx_ref == 333
            assert account_xx_name == 'xx'
            assert self.db.account_exists(account_xx_ref)

            self.db.reset()

            table = {
                102: [
                    {
                        'ops': 'track',
                        'unscaled_value': 10,
                        'cached_balance': 1000,
                        'fresh_balance': 1000,
                        'log_value_sum': 1000,
                        'box_size': 1,
                        'log_size': 1,
                    },
                    {
                        'ops': 'track',
                        'unscaled_value': 20,
                        'cached_balance': 3000,
                        'fresh_balance': 3000,
                        'log_value_sum': 3000,
                        'box_size': 2,
                        'log_size': 2,
                    },
                    {
                        'ops': 'track',
                        'unscaled_value': 30,
                        'cached_balance': 6000,
                        'fresh_balance': 6000,
                        'log_value_sum': 6000,
                        'box_size': 3,
                        'log_size': 3,
                    },
                    {
                        'ops': 'sub',
                        'unscaled_value': 15,
                        'cached_balance': 4500,
                        'fresh_balance': 4500,
                        'log_value_sum': 4500,
                        'box_size': 3,
                        'log_size': 4,
                    },
                    {
                        'ops': 'sub',
                        'unscaled_value': 50,
                        'cached_balance': -500,
                        'fresh_balance': -500,
                        'log_value_sum': -500,
                        'box_size': 4,
                        'log_size': 5,
                    },
                    {
                        'ops': 'sub',
                        'unscaled_value': 100,
                        'cached_balance': -10500,
                        'fresh_balance': -10500,
                        'log_value_sum': -10500,
                        'box_size': 5,
                        'log_size': 6,
                    },
                ],
                201: [
                    {
                        'ops': 'sub',
                        'unscaled_value': 90,
                        'cached_balance': -9000,
                        'fresh_balance': -9000,
                        'log_value_sum': -9000,
                        'box_size': 1,
                        'log_size': 1,
                    },
                    {
                        'ops': 'track',
                        'unscaled_value': 100,
                        'cached_balance': 1000,
                        'fresh_balance': 1000,
                        'log_value_sum': 1000,
                        'box_size': 2,
                        'log_size': 2,
                    },
                    {
                        'ops': 'sub',
                        'unscaled_value': 190,
                        'cached_balance': -18000,
                        'fresh_balance': -18000,
                        'log_value_sum': -18000,
                        'box_size': 3,
                        'log_size': 3,
                    },
                    {
                        'ops': 'track',
                        'unscaled_value': 1000,
                        'cached_balance': 82000,
                        'fresh_balance': 82000,
                        'log_value_sum': 82000,
                        'box_size': 4,
                        'log_size': 4,
                    },
                ],
            }
            for x in table:
                for y in table[x]:
                    ref = None
                    if y['ops'] == 'track':
                        ref = self.db.track(
                            unscaled_value=y['unscaled_value'],
                            desc='test-add',
                            account=x,
                            logging=True,
                            created=Helper.time(),
                            debug=debug,
                        )
                    elif y['ops'] == 'sub':
                        (ref, z) = self.db.sub(
                            unscaled_value=y['unscaled_value'],
                            desc='test-sub',
                            account=x,
                            created=Helper.time(),
                            debug=debug,
                        )
                        if debug:
                            print('_sub', z, Helper.time())
                    assert ref is not None
                    assert len(self.db.vault(Vault.ACCOUNT)[x]['log'][ref]['file']) == 0
                    for i in range(3):
                        file_ref = self.db.add_file(x, ref, 'file_' + str(i))
                        sleep(0.0000001)
                        if debug:
                            print('ref', ref, 'file', file_ref)
                        assert file_ref is not None
                        assert len(self.db.vault(Vault.ACCOUNT)[x]['log'][ref]['file']) == i + 1
                    file_ref = self.db.add_file(x, ref, 'file_' + str(3))
                    assert self.db.remove_file(x, ref, file_ref)
                    daily_logs = self.db.daily_logs(debug=debug)
                    if debug:
                        print('daily_logs', daily_logs)
                    for k, v in daily_logs.items():
                        assert k
                        assert v
                    z = self.db.balance(x)
                    if debug:
                        print("debug-0", z, y)
                    assert z == y['cached_balance']
                    z = self.db.balance(x, False)
                    if debug:
                        print("debug-1", z, y['fresh_balance'])
                    assert z == y['fresh_balance']
                    o = self.db.vault(Vault.ACCOUNT)[x]['log']
                    z = 0
                    for i in o:
                        z += o[i]['value']
                    if debug:
                        print("debug-2", z, type(z))
                        print("debug-2", y['log_value_sum'], type(y['log_value_sum']))
                    assert z == y['log_value_sum']
                    if debug:
                        print('debug-2 - PASSED')
                    assert self.db.box_size(x) == y['box_size']
                    assert self.db.log_size(x) == y['log_size']
                assert self.db.boxes(x) != {}
                assert self.db.logs(x) != {}

                assert not self.db.hide(x)
                assert self.db.hide(x, False) is False
                assert self.db.hide(x) is False
                assert self.db.hide(x, True)
                assert self.db.hide(x)

                assert self.db.zakatable(x)
                assert self.db.zakatable(x, False) is False
                assert self.db.zakatable(x) is False
                assert self.db.zakatable(x, True)
                assert self.db.zakatable(x)

            self.db.reset()

            # Not allowed for duplicate transactions in the same account and time

            created = Helper.time()
            ref, _ = self.db.account(name='same')
            self.db.track(
                unscaled_value=100,
                desc='test-1',
                account=ref,
                logging=True,
                created=created,
            )
            failed = False
            try:
                self.db.track(
                    unscaled_value=50,
                    desc='test-1',
                    account=ref,
                    logging=True,
                    created=created,
                )
            except:
                failed = True
            assert failed is True

            self.db.reset()

            # exchange

            account_cash_ref, _ = self.db.account(name='cash')
            account_bank_ref, _ = self.db.account(name='bank')

            self.db.set_exchange(account_cash_ref, created=25, rate=3.75, description="2024-06-25", debug=debug)
            self.db.set_exchange(account_cash_ref, created=22, rate=3.73, description="2024-06-22", debug=debug)
            self.db.set_exchange(account_cash_ref, created=15, rate=3.69, description="2024-06-15", debug=debug)
            self.db.set_exchange(account_cash_ref, created=10, rate=3.66, debug=debug)

            for i in range(1, 30):
                exchange = self.db.exchange(account_cash_ref, created=i, debug=debug)
                rate, description, created = exchange['rate'], exchange['description'], exchange['time']
                if debug:
                    print(f'i={i}, rate={rate}, description={description}, created={created}')
                assert rate
                assert created
                if i < 10:
                    assert rate == 1
                elif i == 10:
                    assert float(rate) == 3.66
                    assert description is None
                elif i < 15:
                    assert float(rate) == 3.66
                    assert description is None
                elif i == 15:
                    assert float(rate) == 3.69
                    assert description is not None
                elif i < 22:
                    assert float(rate) == 3.69
                    assert description is not None
                elif i == 22:
                    assert float(rate) == 3.73
                    assert description is not None
                elif i >= 25:
                    assert float(rate) == 3.75
                    assert description is not None
                exchange = self.db.exchange(account_bank_ref, created=i, debug=debug)
                rate, description, created = exchange['rate'], exchange['description'], exchange['time']
                if debug:
                    print(f'i={i}, rate={rate}, description={description}, created={created}')
                assert created
                assert rate == 1
                assert description is None

            assert len(self.db.vault(Vault.ACCOUNT)[account_cash_ref]['exchange']) > 0
            assert len(self.db.exchanges(account_cash_ref)) > 0
            # self.db.vault(Vault.ACCOUNT)[account_cash_ref]['exchange'].clear()
            # assert len(self.db.exchanges(account_cash_ref)) == 0

            self.db.reset()

            account_cash_ref, _ = self.db.account(name='cash')

            # حفظ أسعار الصرف باستخدام التواريخ بالنانو ثانية
            self.db.set_exchange(account_cash_ref, created=Helper.day_to_time(25), rate=3.75, description="2024-06-25",
                                 debug=debug)
            self.db.set_exchange(account_cash_ref, created=Helper.day_to_time(22), rate=3.73, description="2024-06-22",
                                 debug=debug)
            self.db.set_exchange(account_cash_ref, created=Helper.day_to_time(15), rate=3.69, description="2024-06-15",
                                 debug=debug)
            self.db.set_exchange(account_cash_ref, created=Helper.day_to_time(10), rate=3.66, debug=debug)

            account_test_ref, _ = self.db.account(name='test-negative-to-positive')

            for i in [x * 0.12 for x in range(-15, 21)]:
                if i <= 0:
                    assert not self.db.set_exchange(account_test_ref, created=Helper.time(), rate=i,
                                                    description=f"range({i})", debug=debug)
                    result = self.db.exchange(account_test_ref, created=Helper.time(), debug=debug)
                    if debug:
                        print(f'exchange = {result}')
                    assert result['rate'] == 1
                else:
                    assert self.db.set_exchange(account_test_ref, created=Helper.time(), rate=i,
                                                description=f"range({i})", debug=debug)
                    result = self.db.exchange(account_test_ref, created=Helper.time(), debug=debug)
                    if debug:
                        print(f'exchange = {result}')
                    assert result['rate'] != 1

            # اختبار النتائج باستخدام التواريخ بالنانو ثانية
            for i in range(1, 31):
                timestamp_ns = Helper.day_to_time(i)
                exchange = self.db.exchange(account_cash_ref, created=timestamp_ns, debug=debug)
                rate, description, created = exchange['rate'], exchange['description'], exchange['time']
                if debug:
                    print(f'i={i}, rate={rate}, description={description}, created={created}')
                assert rate
                assert created
                if i < 10:
                    assert rate == 1
                    assert description is None
                elif i == 10:
                    assert float(rate) == 3.66
                    assert description is None
                elif i < 15:
                    assert float(rate) == 3.66
                    assert description is None
                elif i == 15:
                    assert float(rate) == 3.69
                    assert description is not None
                elif i < 22:
                    assert float(rate) == 3.69
                    assert description is not None
                elif i == 22:
                    assert float(rate) == 3.73
                    assert description is not None
                elif i >= 25:
                    assert float(rate) == 3.75
                    assert description is not None
                exchange = self.db.exchange(account_bank_ref, created=i, debug=debug)
                rate, description, created = exchange['rate'], exchange['description'], exchange['time']
                if debug:
                    print(f'i={i}, rate={rate}, description={description}, created={created}')
                assert created
                assert rate == 1
                assert description is None

            self.db.reset()

            # Same account transfer
            for x in [1, 'a', True, 1.8, None]:
                failed = False
                try:
                    self.db.transfer(
                        unscaled_amount=1,
                        from_account=x,
                        to_account=x,
                        desc='same-account',
                        debug=debug,
                    )
                except:
                    failed = True
                assert failed is True

            # Always preserve box age during transfer

            series: list[tuple] = [
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

            selected_time = Helper.datetime_to_milliseconds(Helper.time_to_datetime(Helper.time())) - Helper.TimeCycle()
            account_ages_ref, _ = self.db.account(name='ages')
            account_future_ref, _ = self.db.account(name='future')

            for total in case:
                if debug:
                    print('--------------------------------------------------------')
                    print(f'case[{total}]', case[total])
                for x in case[total]['series']:
                    self.db.track(
                        unscaled_value=x[0],
                        desc=f"test-{x} ages",
                        account=account_ages_ref,
                        logging=True,
                        created=Helper.time(Helper.milliseconds_to_datetime(selected_time * x[1])),
                    )

                unscaled_total = Helper.unscale(total)
                if debug:
                    print('unscaled_total', unscaled_total)
                refs = self.db.transfer(
                    unscaled_amount=unscaled_total,
                    from_account=account_ages_ref,
                    to_account=account_future_ref,
                    desc='Zakat Movement',
                    debug=debug,
                )

                if debug:
                    print('[refs]', refs)

                ages_cache_balance = self.db.balance(account_ages_ref)
                ages_fresh_balance = self.db.balance(account_ages_ref, False)
                rest = case[total]['rest']
                if debug:
                    print('source',
                          f'cache_balance={ages_cache_balance}, fresh_balance={ages_fresh_balance}, rest={rest}')
                assert ages_cache_balance == rest
                assert ages_fresh_balance == rest

                future_cache_balance = self.db.balance(account_future_ref)
                future_fresh_balance = self.db.balance(account_future_ref, False)
                if debug:
                    print('target',
                          f'cache_balance={future_cache_balance}, fresh_balance={future_fresh_balance}, total={total}')
                    print('refs', refs)
                assert future_cache_balance == total
                assert future_fresh_balance == total

                # TODO: check boxes times for `ages` should equal box times in `future`
                for ref in self.db.vault(Vault.ACCOUNT)[account_ages_ref]['box']:
                    ages_capital = self.db.vault(Vault.ACCOUNT)[account_ages_ref]['box'][ref]['capital']
                    ages_rest = self.db.vault(Vault.ACCOUNT)[account_ages_ref]['box'][ref]['rest']
                    future_capital = 0
                    if ref in self.db.vault(Vault.ACCOUNT)[account_future_ref]['box']:
                        future_capital = self.db.vault(Vault.ACCOUNT)[account_future_ref]['box'][ref]['capital']
                    future_rest = 0
                    if ref in self.db.vault(Vault.ACCOUNT)[account_future_ref]['box']:
                        future_rest = self.db.vault(Vault.ACCOUNT)[account_future_ref]['box'][ref]['rest']
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
                self.db.reset()

            if debug:
                print('####################################################################')

            account_wallet_ref, _ = self.db.account(name='wallet')
            account_safe_ref, _ = self.db.account(name='safe')
            account_bank_ref, _ = self.db.account(name='bank')

            transaction = [
                (
                    20, account_wallet_ref, 12, -2000, -2000, -2000, 1, 1,
                    2000, 2000, 2000, 1, 1,
                ),
                (
                    750, account_wallet_ref, account_safe_ref, -77000, -77000, -77000, 2, 2,
                    75000, 75000, 75000, 1, 1,
                ),
                (
                    600, account_safe_ref, account_bank_ref, 15000, 15000, 15000, 1, 2,
                    60000, 60000, 60000, 1, 1,
                ),
            ]
            for z in transaction:
                x = z[1]
                y = z[2]
                self.db.transfer(
                    unscaled_amount=z[0],
                    from_account=x,
                    to_account=y,
                    desc='test-transfer',
                    debug=debug,
                )
                zz = self.db.balance(x)
                if debug:
                    print(zz, z)
                assert zz == z[3]
                xx = self.db.accounts()[x]
                assert xx == z[3]
                assert self.db.balance(x, False) == z[4]
                assert xx == z[4]

                s = 0
                log = self.db.vault(Vault.ACCOUNT)[x]['log']
                for i in log:
                    s += log[i]['value']
                if debug:
                    print('s', s, 'z[5]', z[5])
                assert s == z[5]

                assert self.db.box_size(x) == z[6]
                assert self.db.log_size(x) == z[7]

                yy = self.db.accounts()[y]
                assert self.db.balance(y) == z[8]
                assert yy == z[8]
                assert self.db.balance(y, False) == z[9]
                assert yy == z[9]

                s = 0
                log = self.db.vault(Vault.ACCOUNT)[y]['log']
                for i in log:
                    s += log[i]['value']
                assert s == z[10]

                assert self.db.box_size(y) == z[11]
                assert self.db.log_size(y) == z[12]

            if debug:
                pp().pprint(self.db.check(2.17, debug=debug))

            # storage

            _path = self.db.path(f'./zakat_test_db/test.{self.db.ext()}')
            if os.path.exists(_path):
                os.remove(_path)
            self.db.save()
            assert os.path.getsize(_path) > 0
            self.db.reset()
            self.db.load()
            assert self.db.vault(Vault.ACCOUNT) is not None

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
                c = self.generate_random_csv_file(csv_path, csv_count, with_rate, debug)
                if debug:
                    print('generate_random_csv_file', c)
                assert c == csv_count
                assert os.path.getsize(csv_path) > 0
                cache_path = self.db.import_csv_cache_path()
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                self.db.reset()
                (created, found, bad) = self.import_csv(csv_path, debug)
                bad_count = len(bad)
                assert bad_count > 0
                if debug:
                    print(f"csv-imported: ({created}, {found}, {bad_count}) = count({csv_count})")
                    print('bad', bad)
                tmp_size = os.path.getsize(cache_path)
                assert tmp_size > 0
                # TODO: assert created + found + bad_count == csv_count
                # TODO: assert created == csv_count
                # TODO: assert bad_count == 0
                (created_2, found_2, bad_2) = self.import_csv(csv_path)
                bad_2_count = len(bad_2)
                if debug:
                    print(f"csv-imported: ({created_2}, {found_2}, {bad_2_count})")
                    print('bad', bad)
                assert bad_2_count > 0
                # TODO: assert tmp_size == os.path.getsize(cache_path)
                # TODO: assert created_2 + found_2 + bad_2_count == csv_count
                # TODO: assert created == found_2
                # TODO: assert bad_count == bad_2_count
                # TODO: assert found_2 == csv_count
                # TODO: assert bad_2_count == 0
                # TODO: assert created_2 == 0

                # payment parts

                positive_parts = self.build_payment_parts(100, positive_only=True, debug=debug)
                assert Helper.check_payment_parts(positive_parts) != 0
                assert Helper.check_payment_parts(positive_parts) != 0
                all_parts = self.build_payment_parts(300, positive_only=False, debug=debug)
                assert Helper.check_payment_parts(all_parts) != 0
                assert Helper.check_payment_parts(all_parts) != 0
                if debug:
                    pp().pprint(positive_parts)
                    pp().pprint(all_parts)
                # dynamic discount
                suite = []
                count = 3
                for exceed in [False, True]:
                    case = []
                    for parts in [positive_parts, all_parts]:
                        part = parts.copy()
                        demand = part['demand']
                        if debug:
                            print(demand, part['total'])
                        i = 0
                        z = demand / count
                        cp = {
                            'account': {},
                            'demand': demand,
                            'exceed': exceed,
                            'total': part['total'],
                        }
                        j = ''
                        for x, y in part['account'].items():
                            x_exchange = self.db.exchange(x, debug=debug)
                            zz = Helper.exchange_calc(z, 1, x_exchange['rate'])
                            if exceed and zz <= demand:
                                i += 1
                                y['part'] = zz
                                if debug:
                                    print(f'exceed={exceed}, y={y}')
                                cp['account'][x] = y
                                case.append(y)
                            elif not exceed and y['balance'] >= zz:
                                i += 1
                                y['part'] = zz
                                if debug:
                                    print(exceed, y)
                                cp['account'][x] = y
                                case.append(y)
                            j = x
                            if i >= count:
                                break
                        if debug:
                            print(f'x={x}, j={j}')
                        if len(cp['account'][j]) > 0:
                            suite.append(cp)
                if debug:
                    print('suite', len(suite))
                for case in suite:
                    if debug:
                        print('case', case)
                    result = Helper.check_payment_parts(case)
                    if debug:
                        print('check_payment_parts', result, f'exceed: {exceed}')
                    assert result == 0

                    report = self.db.check(2.17, debug=debug)
                    (valid, brief, plan) = report
                    if debug:
                        print('valid', valid)
                    zakat_result = self.db.zakat(report, parts=case, debug=debug)
                    if debug:
                        print('zakat-result', zakat_result)
                    assert valid == zakat_result

            assert self.db.save(path + f'.{self.db.ext()}')
            assert self.db.export_json(path + '.json')

            assert self.db.export_json("1000-transactions-test.json")
            assert self.db.save(f"1000-transactions-test.{self.db.ext()}")

            self.db.reset()

            # test transfer between accounts with different exchange rate

            a_SAR = "Bank (SAR)"
            b_USD = "Bank (USD)"
            c_SAR = "Safe (SAR)"

            account_a_SAR_ref, _ = self.db.account(name=a_SAR)
            account_b_USD_ref, _ = self.db.account(name=b_USD)
            account_c_SAR_ref, _ = self.db.account(name=c_SAR)

            # 0: track, 1: check-exchange, 2: do-exchange, 3: transfer
            for case in [
                (0, account_a_SAR_ref, "SAR Gift", 1000, 100000),
                (1, account_a_SAR_ref, 1),
                (0, account_b_USD_ref, "USD Gift", 500, 50000),
                (1, account_b_USD_ref, 1),
                (2, account_b_USD_ref, 3.75),
                (1, account_b_USD_ref, 3.75),
                (3, 100, account_b_USD_ref, account_a_SAR_ref, "100 USD -> SAR", 40000, 137500),
                (0, account_c_SAR_ref, "Salary", 750, 75000),
                (3, 375, account_c_SAR_ref, account_b_USD_ref, "375 SAR -> USD", 37500, 50000),
                (3, 3.75, account_a_SAR_ref, account_b_USD_ref, "3.75 SAR -> USD", 137125, 50100),
            ]:
                if debug:
                    print('case', case)
                match (case[0]):
                    case 0:  # track
                        _, account, desc, x, balance = case
                        self.db.track(unscaled_value=x, desc=desc, account=account, debug=debug)

                        cached_value = self.db.balance(account, cached=True)
                        fresh_value = self.db.balance(account, cached=False)
                        if debug:
                            print('account', account, 'cached_value', cached_value, 'fresh_value', fresh_value)
                        assert cached_value == balance
                        assert fresh_value == balance
                    case 1:  # check-exchange
                        _, account, expected_rate = case
                        t_exchange = self.db.exchange(account, created=Helper.time(), debug=debug)
                        if debug:
                            print('t-exchange', t_exchange)
                        assert t_exchange['rate'] == expected_rate
                    case 2:  # do-exchange
                        _, account, rate = case
                        self.db.set_exchange(account, rate=rate, debug=debug)
                        b_exchange = self.db.exchange(account, created=Helper.time(), debug=debug)
                        if debug:
                            print('b-exchange', b_exchange)
                        assert b_exchange['rate'] == rate
                    case 3:  # transfer
                        _, x, a, b, desc, a_balance, b_balance = case
                        self.db.transfer(x, a, b, desc, debug=debug)

                        cached_value = self.db.balance(a, cached=True)
                        fresh_value = self.db.balance(a, cached=False)
                        if debug:
                            print(
                                'account', a,
                                'cached_value', cached_value,
                                'fresh_value', fresh_value,
                                'a_balance', a_balance,
                            )
                        assert cached_value == a_balance
                        assert fresh_value == a_balance

                        cached_value = self.db.balance(b, cached=True)
                        fresh_value = self.db.balance(b, cached=False)
                        if debug:
                            print('account', b, 'cached_value', cached_value, 'fresh_value', fresh_value)
                        assert cached_value == b_balance
                        assert fresh_value == b_balance

            # Transfer all in many chunks randomly from B to A
            a_SAR_balance = 137125
            b_USD_balance = 50100
            b_USD_exchange = self.db.exchange(account_b_USD_ref, debug=debug)
            amounts = ZakatTracker.create_random_list(b_USD_balance, max_value=1000)
            if debug:
                print('amounts', amounts)
            i = 0
            for x in amounts:
                if debug:
                    print(f'{i} - transfer-with-exchange({x})')
                self.db.transfer(
                    unscaled_amount=Helper.unscale(x),
                    from_account=account_b_USD_ref,
                    to_account=account_a_SAR_ref,
                    desc=f"{x} USD -> SAR",
                    debug=debug,
                )

                b_USD_balance -= x
                cached_value = self.db.balance(account_b_USD_ref, cached=True)
                fresh_value = self.db.balance(account_b_USD_ref, cached=False)
                if debug:
                    print('account', b_USD, 'cached_value', cached_value, 'fresh_value', fresh_value, 'excepted',
                          b_USD_balance)
                assert cached_value == b_USD_balance
                assert fresh_value == b_USD_balance

                a_SAR_balance += int(x * b_USD_exchange['rate'])
                cached_value = self.db.balance(account_a_SAR_ref, cached=True)
                fresh_value = self.db.balance(account_a_SAR_ref, cached=False)
                if debug:
                    print('account', a_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'expected',
                          a_SAR_balance, 'rate', b_USD_exchange['rate'])
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
                self.db.transfer(
                    unscaled_amount=Helper.unscale(x),
                    from_account=account_c_SAR_ref,
                    to_account=account_a_SAR_ref,
                    desc=f"{x} SAR -> a_SAR",
                    debug=debug,
                )

                c_SAR_balance -= x
                cached_value = self.db.balance(account_c_SAR_ref, cached=True)
                fresh_value = self.db.balance(account_c_SAR_ref, cached=False)
                if debug:
                    print('account', c_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'excepted',
                          c_SAR_balance)
                assert cached_value == c_SAR_balance
                assert fresh_value == c_SAR_balance

                a_SAR_balance += x
                cached_value = self.db.balance(account_a_SAR_ref, cached=True)
                fresh_value = self.db.balance(account_a_SAR_ref, cached=False)
                if debug:
                    print('account', a_SAR, 'cached_value', cached_value, 'fresh_value', fresh_value, 'expected',
                          a_SAR_balance)
                assert cached_value == a_SAR_balance
                assert fresh_value == a_SAR_balance
                i += 1

            assert self.db.export_json("accounts-transfer-with-exchange-rates.json")
            assert self.db.save(f"accounts-transfer-with-exchange-rates.{self.db.ext()}")

            # check & zakat with exchange rates for many cycles

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
                account_safe_ref, _ = self.db.account(name='safe')
                account_cave_ref, _ = self.db.account(name='cave')
                if debug:
                    print('rate', rate, 'values', values)
                for case in [
                    (a, account_safe_ref, Helper.time(Helper.milliseconds_to_datetime(Helper.time_to_milliseconds(Helper.time()) - Helper.TimeCycle())), [
                        {account_safe_ref: {0: {'below_nisab': x}}},
                    ], False, m),
                    (b, account_safe_ref, Helper.time(Helper.milliseconds_to_datetime(Helper.time_to_milliseconds(Helper.time()) - Helper.TimeCycle())), [
                        {account_safe_ref: {0: {'count': 1, 'total': y}}},
                    ], True, n),
                    (c, account_cave_ref, Helper.time(Helper.milliseconds_to_datetime(Helper.time_to_milliseconds(Helper.time()) - (Helper.TimeCycle() * 3))), [
                        {account_cave_ref: {0: {'count': 3, 'total': z}}},
                    ], True, o),
                ]:
                    if debug:
                        print(f"############# check(rate: {rate}) #############")
                        print('case', case)
                    self.db.reset()
                    self.db.set_exchange(account=case[1], created=case[2], rate=rate)
                    self.db.track(
                        unscaled_value=case[0],
                        desc='test-check',
                        account=case[1],
                        logging=True,
                        created=case[2],
                    )
                    assert self.db.snapshot()

                    report = self.db.check(2.17, debug=debug)
                    (valid, brief, plan) = report
                    if debug:
                        print('brief', brief)
                        print('case', case)
                        pp().pprint(plan)
                    assert valid == case[4]
                    assert case[5] == brief[0]
                    assert case[5] == brief[1]

                    for x in plan:
                        assert case[1] == x
                        if 'total' in case[3][0][x][0].keys():
                            assert case[3][0][x][0]['total'] == int(brief[2])
                            assert int(plan[x][0]['total']) == case[3][0][x][0]['total']
                            assert int(plan[x][0]['count']) == case[3][0][x][0]['count']
                        else:
                            assert plan[x][0]['below_nisab'] == case[3][0][x][0]['below_nisab']
                    if debug:
                        pp().pprint(report)
                    result = self.db.zakat(report, debug=debug)
                    if debug:
                        print('zakat-result', result, case[4])
                    assert result == case[4]
                    report = self.db.check(2.17, debug=debug)
                    (valid, brief, plan) = report
                    assert valid is False
            return True
        except Exception as e:
            assert self.db.export_json("test-snapshot.json")
            assert self.db.save(f"test-snapshot.{self.db.ext()}")
            raise e


def test(
        debug: bool = False,
        dict_model: bool = True,
        sqlite_model: bool = True,
        mysql_model: bool = False,
        mariadb_model: bool = False,
        postgresql_model: bool = False,
        cockroachdb_model: bool = False,
) -> None:
    """
        Conducts comprehensive tests on various ZakatTracker models.

        This function orchestrates the testing process for different database models,
        including in-memory dictionaries, SQLite, MariaDB, MySQL, PostgreSQL, CockroachDB,
        and Oracle. It initializes the test environment, creates and populates the database,
        and executes a series of test cases for both the `Model` and `ZakatTracker` classes.

        Parameters:
        debug: If True, enables detailed logging and output during the test process.
        dict_model: If True, tests the in-memory dictionary model.
        sqlite_model: If True, tests the SQLite model.
        mysql_model: If True, tests the MySQL model.
        mariadb_model: If True, tests the MariaDB model.
        postgresql_model: If True, tests the PostgreSQL model.
        cockroachdb_model: If True, tests the CockroachDB model.

        Returns: None
    """
    models = []
    durations = {}
    # clean
    test_directory = 'zakat_test_db'
    if os.path.exists(test_directory):
        shutil.rmtree(test_directory)
        print(f"{test_directory} Directory removed successfully.")
    else:
        print(f"{test_directory} Directory does not exist.")
    Helper.test(debug=True)
    # models
    if dict_model:
        models.append(
            DictModel(
                db_path=f"./{test_directory}/zakat.camel",
            ),
        )
    if sqlite_model:
        models.append(
            SQLModel(
                provider="sqlite",
                filename=f"./{test_directory}/zakat.sqlite",
                create_db=True,
                debug=True,
            ),
        )
    if mysql_model:
        models.append(
            SQLModel(
                provider='mysql',
                host='127.0.0.1',
                user='root',
                passwd='t00r',
                db='zakat',
                debug=True,
            ),
        )
    if mariadb_model:
        pass
    if postgresql_model:
        pass
    if cockroachdb_model:
        pass
    for model in models:
        start = time_ns()
        assert model.test(debug=debug)
        ledger = ZakatTracker(model=model)
        assert ledger.test(debug=debug)
        durations[f'{model.__class__.__name__}({model.provider})'] = time_ns() - start
    if debug:
        print("#########################")
        print("######## TEST DONE ########")
        print("#########################")
        for model_name, duration in durations.items():
            print("------------- Model: [" + model_name + "] -------------")
            print(Helper.duration_from_nanoseconds(duration))
        print("#########################")


def main():
    test(debug=True)


if __name__ == "__main__":
    main()
