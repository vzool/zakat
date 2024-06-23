"""
 _____     _         _     _____               _             
|__  /__ _| | ____ _| |_  |_   _| __ __ _  ___| | _____ _ __ 
  / // _` | |/ / _` | __|   | || '__/ _` |/ __| |/ / _ \ '__|
 / /| (_| |   < (_| | |_    | || | | (_| | (__|   <  __/ |   
/____\__,_|_|\_\__,_|\__|   |_||_|  \__,_|\___|_|\_\___|_|   

"رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنتَ خَيْرُ الْفَاتِحِينَ (89)" -- سورة الأعراف
... Never Trust, Always Verify ...

This module provides a ZakatTracker class for tracking and calculating Zakat.

The ZakatTracker class allows users to record financial transactions, and calculate Zakat due based on the Nisab (the minimum threshold for Zakat) and Haul (after completing one year since every transaction received in the same account).
We use the current silver price and manage account balances.
It supports importing transactions from CSV files, exporting data to JSON format, and saving/loading the tracker state.

Key Features:

*   Tracking of positive and negative transactions
*   Calculation of Zakat based on Nisab, Haul and silver price
*   Import of transactions from CSV files
*   Export of data to JSON format
*   Persistence of tracker state using pickle files
*   History tracking (optional)

The module also includes a few helper functions and classes:

*   `JSONEncoder`: A custom JSON encoder for serializing enum values.
*   `Action` (Enum): An enumeration representing different actions in the tracker.
*   `MathOperation` (Enum): An enumeration representing mathematical operations in the tracker.

The ZakatTracker class is designed to be flexible and extensible, allowing users to customize it to their specific needs.

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
import csv
import json
import pickle
import random
import datetime
from time import sleep
from pprint import PrettyPrinter as pp
from math import floor
from enum import Enum, auto

class Action(Enum):
	CREATE = auto()
	TRACK = auto()
	LOG = auto()
	SUB = auto()
	ADD_FILE = auto()
	REMOVE_FILE = auto()
	REPORT = auto()
	ZAKAT = auto()

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, Action) or isinstance(obj, MathOperation):
			return obj.name  # Serialize as the enum member's name
		return super().default(obj)

class MathOperation(Enum):
	ADDITION = auto()
	EQUAL = auto()
	SUBTRACTION = auto()

class ZakatTracker:
	"""
    A class for tracking and calculating Zakat.

    This class provides functionalities for recording transactions, calculating Zakat due,
    and managing account balances. It also offers features like importing transactions from
    CSV files, exporting data to JSON format, and saving/loading the tracker state.

    The `ZakatTracker` class is designed to handle both positive and negative transactions,
    allowing for flexible tracking of financial activities related to Zakat. It also supports
    the concept of a "nisab" (minimum threshold for Zakat) and a "haul" (complete one year for Transaction) can calculate Zakat due
    based on the current silver price.

    The class uses a pickle file as its database to persist the tracker state,
    ensuring data integrity across sessions. It also provides options for enabling or
    disabling history tracking, allowing users to choose their preferred level of detail.

    In addition, the `ZakatTracker` class includes various helper methods like
    `time`, `time_to_datetime`, `lock`, `free`, `recall`, `export_json`,
    and more. These methods provide additional functionalities and flexibility
    for interacting with and managing the Zakat tracker.

    Attributes:
        ZakatCut (function): A function to calculate the Zakat percentage.
        TimeCycle (function): A function to determine the time cycle for Zakat.
        Nisab (function): A function to calculate the Nisab based on the silver price.
        Version (str): The version of the ZakatTracker class.

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
                    - log (dict): A dictionary storing transaction logs.
                        - {timestamp} (dict):
                            - value (int): The transaction amount (positive or negative).
                            - desc (str): The description of the transaction.
                            - file (dict): A dictionary storing file references associated with the transaction.
                    - zakatable (bool): Indicates whether the account is subject to Zakat.
            - history (dict):
                - {timestamp} (list): A list of dictionaries storing the history of actions performed.
                    - {action_dict} (dict):
                        - action (Action): The type of action (CREATE, TRACK, LOG, SUB, ADD_FILE, REMOVE_FILE, REPORT, ZAKAT).
                        - account (str): The account number associated with the action.
                        - ref (int): The reference number of the transaction.
                        - file (int): The reference number of the file (if applicable).
                        - key (str): The key associated with the action (e.g., 'rest', 'total').
                        - value (int): The value associated with the action.
                        - math (MathOperation): The mathematical operation performed (if applicable).
            - lock (int or None): The timestamp indicating the current lock status (None if not locked).
            - report (dict):
                - {timestamp} (tuple): A tuple storing Zakat report details.

    """

	# Hybrid Constants
	ZakatCut	= lambda x: 0.025*x # Zakat Cut in one Lunar Year
	TimeCycle	= lambda  : int(60*60*24*354.367056*1e9) # Lunar Year in nanoseconds
	Nisab		= lambda x: 585*x # Silver Price in Local currency value
	Version		= lambda  : '0.2.01'

	def __init__(self, db_path: str = "zakat.pickle", history_mode: bool = True):
		"""
        Initialize ZakatTracker with database path and history mode.

        Parameters:
        db_path (str): The path to the database file. Default is "zakat.pickle".
        history_mode (bool): The mode for tracking history. Default is True.

        Returns:
        None
        """
		self.reset()
		self._history(history_mode)
		self.path(db_path)
		self.load()

	def path(self, _path: str = None) -> str:
		"""
        Set or get the database path.

        Parameters:
        _path (str): The path to the database file. If not provided, it returns the current path.

        Returns:
        str: The current database path.
        """
		if _path is not None:
			self._vault_path = _path
		return self._vault_path

	def _history(self, status: bool = None) -> bool:
		"""
        Enable or disable history tracking.

        Parameters:
        status (bool): The status of history tracking. Default is True.

        Returns:
        None
        """
		if status is not None:
			self._history_mode = status
		return self._history_mode

	def reset(self) -> None:
		"""
        Reset the internal data structure to its initial state.

        Parameters:
        None

        Returns:
        None
        """
		self._vault = {}
		self._vault['account'] = {}
		self._vault['history'] = {}
		self._vault['lock'] = None
		self._vault['report'] = {}

	@staticmethod
	def time(now: datetime = None) -> int:
		"""
        Generates a timestamp based on the provided datetime object or the current datetime.

        Parameters:
        now (datetime, optional): The datetime object to generate the timestamp from. If not provided, the current datetime is used.

        Returns:
        int: The timestamp in positive nanoseconds since the Unix epoch (January 1, 1970), before 1970 will return in negative until 1000AD.
        """
		if now is None:
			now = datetime.datetime.now()
		ordinal_day = now.toordinal()
		ns_in_day = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() * 10**9
		return int((ordinal_day - 719_163) * 86_400_000_000_000 + ns_in_day)

	@staticmethod
	def time_to_datetime(ordinal_ns: int) -> datetime:
		"""
        Converts an ordinal number (number of days since 1000-01-01) to a datetime object.

        Parameters:
        ordinal_ns (int): The ordinal number of days since 1000-01-01.

        Returns:
        datetime: The corresponding datetime object.
        """
		ordinal_day = ordinal_ns // 86_400_000_000_000 + 719_163
		ns_in_day = ordinal_ns % 86_400_000_000_000
		d = datetime.datetime.fromordinal(ordinal_day)
		t = datetime.timedelta(seconds=ns_in_day // 10**9)
		return datetime.datetime.combine(d, datetime.time()) + t

	def _step(self, action: Action = None, account = None, ref: int = None, file: int = None, value: int = None, key: str = None, math_operation: MathOperation = None) -> int:
		"""
		This method is responsible for recording the actions performed on the ZakatTracker.

		Parameters:
		- action (Action): The type of action performed.
		- account (str): The account number on which the action was performed.
		- ref (int): The reference number of the action.
		- file (int): The file reference number of the action.
		- value (int): The value associated with the action.
		- key (str): The key associated with the action.
		- math_operation (MathOperation): The mathematical operation performed during the action.

		Returns:
		- int: The lock time of the recorded action. If no lock was performed, it returns 0.
		"""
		if not self._history():
			return 0
		_lock = self._vault['lock']
		if self.nolock():
			_lock = self._vault['lock'] = ZakatTracker.time()
			self._vault['history'][_lock] = []
		if action is None:
			return _lock
		self._vault['history'][_lock].append({
			'action': action,
			'account': account,
			'ref': ref,
			'file': file,
			'key': key,
			'value': value,
			'math': math_operation,
		})

	def nolock(self) -> bool:
		"""
        Check if the vault lock is currently not set.

        :return: True if the vault lock is not set, False otherwise.
        """
		return self._vault['lock'] is None

	def lock(self) -> int:
		"""
        Acquires a lock on the ZakatTracker instance.

        Returns:
        int: The lock ID. This ID can be used to release the lock later.
        """
		return self._step()

	def box(self) -> dict:
		"""
        Returns a copy of the internal vault dictionary.

        This method is used to retrieve the current state of the ZakatTracker object.
        It provides a snapshot of the internal data structure, allowing for further
        processing or analysis.

        :return: A copy of the internal vault dictionary.
        """
		return self._vault.copy()

	def steps(self) -> dict:
		"""
        Returns a copy of the history of steps taken in the ZakatTracker.

        The history is a dictionary where each key is a unique identifier for a step,
        and the corresponding value is a dictionary containing information about the step.

        :return: A copy of the history of steps taken in the ZakatTracker.
        """
		return self._vault['history'].copy()

	def free(self, _lock: int, auto_save: bool = True) -> bool:
		"""
        Releases the lock on the database.

        Parameters:
        _lock (int): The lock ID to be released.
        auto_save (bool): Whether to automatically save the database after releasing the lock.

        Returns:
        bool: True if the lock is successfully released and (optionally) saved, False otherwise.
        """
		if _lock == self._vault['lock']:
			self._vault['lock'] = None
			if auto_save:
				return self.save(self.path())
			return True
		return False

	def account_exists(self, account) -> bool:
		"""
        Check if the given account exists in the vault.

        Parameters:
        account (str): The account number to check.

        Returns:
        bool: True if the account exists, False otherwise.
        """
		return account in self._vault['account']

	def box_size(self, account) -> int:
		"""
		Calculate the size of the box for a specific account.

		Parameters:
		account (str): The account number for which the box size needs to be calculated.

		Returns:
		int: The size of the box for the given account. If the account does not exist, -1 is returned.
		"""
		if self.account_exists(account):
			return len(self._vault['account'][account]['box'])
		return -1

	def log_size(self, account) -> int:
		"""
        Get the size of the log for a specific account.

        Parameters:
        account (str): The account number for which the log size needs to be calculated.

        Returns:
        int: The size of the log for the given account. If the account does not exist, -1 is returned.
        """
		if self.account_exists(account):
			return len(self._vault['account'][account]['log'])
		return -1

	def recall(self, dry = True, debug = False) -> bool:
		"""
		Revert the last operation.

		Parameters:
		dry (bool): If True, the function will not modify the data, but will simulate the operation. Default is True.
		debug (bool): If True, the function will print debug information. Default is False.

		Returns:
		bool: True if the operation was successful, False otherwise.
		"""
		if not self.nolock() or len(self._vault['history']) == 0:
			return False
		if len(self._vault['history']) <= 0:
			return
		ref = sorted(self._vault['history'].keys())[-1]
		if debug:
			print('recall', ref)
		memory = self._vault['history'][ref]
		if debug:
			print(type(memory), 'memory', memory)

		limit = len(memory) + 1
		sub_positive_log_negative = 0
		for i in range(-1, -limit, -1):
			x = memory[i]
			if debug:
				print(type(x), x)
			match x['action']:
				case Action.CREATE:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if debug:
								print('account', self._vault['account'][x['account']])
							assert len(self._vault['account'][x['account']]['box']) == 0
							assert self._vault['account'][x['account']]['balance'] == 0
							assert self._vault['account'][x['account']]['count'] == 0
							if dry:
								continue
							del self._vault['account'][x['account']]

				case Action.TRACK:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if dry:
								continue
							self._vault['account'][x['account']]['balance'] -= x['value']
							self._vault['account'][x['account']]['count'] -= 1
							del self._vault['account'][x['account']]['box'][x['ref']]

				case Action.LOG:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if x['ref'] in self._vault['account'][x['account']]['log']:
								if dry:
									continue
								if sub_positive_log_negative == -x['value']:
									self._vault['account'][x['account']]['count'] -= 1
									sub_positive_log_negative = 0
								del self._vault['account'][x['account']]['log'][x['ref']]

				case Action.SUB:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if x['ref'] in self._vault['account'][x['account']]['box']:
								if dry:
									continue
								self._vault['account'][x['account']]['box'][x['ref']]['rest'] += x['value']
								self._vault['account'][x['account']]['balance'] += x['value']
								sub_positive_log_negative = x['value']

				case Action.ADD_FILE:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if x['ref'] in self._vault['account'][x['account']]['log']:
								if x['file'] in self._vault['account'][x['account']]['log'][x['ref']]['file']:
									if dry:
										continue
									del self._vault['account'][x['account']]['log'][x['ref']]['file'][x['file']]

				case Action.REMOVE_FILE:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if x['ref'] in self._vault['account'][x['account']]['log']:
								if dry:
									continue
								self._vault['account'][x['account']]['log'][x['ref']]['file'][x['file']] = x['value']

				case Action.REPORT:
					if x['ref'] in self._vault['report']:
						if dry:
							continue
						del self._vault['report'][x['ref']]

				case Action.ZAKAT:
					if x['account'] is not None:
						if self.account_exists(x['account']):
							if x['ref'] in self._vault['account'][x['account']]['box']:
								if x['key'] in self._vault['account'][x['account']]['box'][x['ref']]:
									if dry:
										continue
									match x['math']:
										case MathOperation.ADDITION:
											self._vault['account'][x['account']]['box'][x['ref']][x['key']] -= x['value']
										case MathOperation.EQUAL:
											self._vault['account'][x['account']]['box'][x['ref']][x['key']] = x['value']
										case MathOperation.SUBTRACTION:
											self._vault['account'][x['account']]['box'][x['ref']][x['key']] += x['value']

		if not dry:
			del self._vault['history'][ref]
		return True

	def track(self, value: int = 0, desc: str = '', account: str = 1, logging: bool = True, created: int = None, debug: bool = False) -> int:
		"""
        This function tracks a transaction for a specific account.

        Parameters:
        value (int): The value of the transaction. Default is 0.
        desc (str): The description of the transaction. Default is an empty string.
        account (str): The account for which the transaction is being tracked. Default is '1'.
        logging (bool): Whether to log the transaction. Default is True.
        created (int): The timestamp of the transaction. If not provided, it will be generated. Default is None.
        debug (bool): Whether to print debug information. Default is False.

        Returns:
        int: The timestamp of the transaction.

        This function creates a new account if it doesn't exist, logs the transaction if logging is True, and updates the account's balance and box.

		Raises:
		ValueError: If the transction happend again in the same time.
        """
		if created is None:
			created = ZakatTracker.time()
		_nolock = self.nolock(); self.lock()
		if not self.account_exists(account):
			if debug:
				print(f"account {account} created")
			self._vault['account'][account] = {
				'balance': 0,
				'box': {},
				'count': 0,
				'log': {},
				'zakatable': True,
			}
			self._step(Action.CREATE, account)
		if value == 0:
			if _nolock: self.free(self.lock())
			return 0
		if logging:
			self._log(value, desc, account, created)
		assert created not in self._vault['account'][account]['box']
		self._vault['account'][account]['box'][created] = {
			'capital': value,
			'count': 0,
			'last': 0,
			'rest': value,
			'total': 0,
		}
		self._step(Action.TRACK, account, ref=created, value=value)
		if _nolock: self.free(self.lock())
		return created

	def _log(self, value: int, desc: str = '', account: str = 1, created: int = None) -> int:
		"""
		Log a transaction into the account's log.

		Parameters:
		value (int): The value of the transaction.
		desc (str): The description of the transaction.
		account (str): The account to log the transaction into. Default is '1'.
		created (int): The timestamp of the transaction. If not provided, it will be generated.

		Returns:
		int: The timestamp of the logged transaction.

		This method updates the account's balance, count, and log with the transaction details.
		It also creates a step in the history of the transaction.

		Raises:
		ValueError: If the transction happend again in the same time.
		"""
		if created is None:
			created = ZakatTracker.time()
		self._vault['account'][account]['balance'] += value
		self._vault['account'][account]['count'] += 1
		assert created not in self._vault['account'][account]['log']
		self._vault['account'][account]['log'][created] = {
			'value': value,
			'desc': desc,
			'file': {},
		}
		self._step(Action.LOG, account, ref=created, value=value)
		return created

	def accounts(self) -> dict:
		"""
        Returns a dictionary containing account numbers as keys and their respective balances as values.

        Parameters:
        None

        Returns:
        dict: A dictionary where keys are account numbers and values are their respective balances.
        """
		result = {}
		for i in self._vault['account']:
			result[i] = self._vault['account'][i]['balance']
		return result

	def boxes(self, account) -> dict:
		"""
        Retrieve the boxes (transactions) associated with a specific account.

        Parameters:
        account (str): The account number for which to retrieve the boxes.

        Returns:
        dict: A dictionary containing the boxes associated with the given account.
        If the account does not exist, an empty dictionary is returned.
        """
		if self.account_exists(account):
			return self._vault['account'][account]['box']
		return {}

	def logs(self, account) -> dict:
		"""
		Retrieve the logs (transactions) associated with a specific account.

		Parameters:
		account (str): The account number for which to retrieve the logs.

		Returns:
		dict: A dictionary containing the logs associated with the given account.
		If the account does not exist, an empty dictionary is returned.
		"""
		if self.account_exists(account):
			return self._vault['account'][account]['log']
		return {}

	def add_file(self, account: str, ref: int, path: str) -> int:
		"""
		Adds a file reference to a specific transaction log entry in the vault.

		Parameters:
		account (str): The account number associated with the transaction log.
		ref (int): The reference to the transaction log entry.
		path (str): The path of the file to be added.

		Returns:
		int: The reference of the added file. If the account or transaction log entry does not exist, returns 0.
		"""
		if self.account_exists(account):
			if ref in self._vault['account'][account]['log']:
				file_ref = ZakatTracker.time()
				self._vault['account'][account]['log'][ref]['file'][file_ref] = path
				_nolock = self.nolock(); self.lock()
				self._step(Action.ADD_FILE, account, ref=ref, file=file_ref)
				if _nolock: self.free(self.lock())
				return file_ref
		return 0

	def remove_file(self, account: str, ref: int, file_ref: int) -> bool:
		"""
		Removes a file reference from a specific transaction log entry in the vault.

		Parameters:
		account (str): The account number associated with the transaction log.
		ref (int): The reference to the transaction log entry.
		file_ref (int): The reference of the file to be removed.

		Returns:
		bool: True if the file reference is successfully removed, False otherwise.
		"""
		if self.account_exists(account):
			if ref in self._vault['account'][account]['log']:
				if file_ref in self._vault['account'][account]['log'][ref]['file']:
					x = self._vault['account'][account]['log'][ref]['file'][file_ref]
					del self._vault['account'][account]['log'][ref]['file'][file_ref]
					_nolock = self.nolock(); self.lock()
					self._step(Action.REMOVE_FILE, account, ref=ref, file=file_ref, value=x)
					if _nolock: self.free(self.lock())
					return True
		return False

	def balance(self, account: str = 1, cached: bool = True) -> int:
		"""
		Calculate and return the balance of a specific account.

		Parameters:
		account (str): The account number. Default is '1'.
		cached (bool): If True, use the cached balance. If False, calculate the balance from the box. Default is True.

		Returns:
		int: The balance of the account.

		Note:
		If cached is True, the function returns the cached balance.
		If cached is False, the function calculates the balance from the box by summing up the 'rest' values of all box items.
		"""
		if cached:
			return self._vault['account'][account]['balance']
		x = 0
		return [x := x + y['rest'] for y in self._vault['account'][account]['box'].values()][-1]

	def zakatable(self, account, status: bool = None) -> bool:
		"""
        Check or set the zakatable status of a specific account.

        Parameters:
        account (str): The account number.
        status (bool, optional): The new zakatable status. If not provided, the function will return the current status.

        Returns:
        bool: The current or updated zakatable status of the account.

        Raises:
        None

        Example:
        >>> tracker = ZakatTracker()
        >>> tracker.zakatable('account1', True)  # Set the zakatable status of 'account1' to True
        True
        >>> tracker.zakatable('account1')  # Get the zakatable status of 'account1'
        True
        """
		if self.account_exists(account):
			if status is None:
				return self._vault['account'][account]['zakatable']
			self._vault['account'][account]['zakatable'] = status
			return status
		return False

	def sub(self, x: int, desc: str = '', account: str = 1, created: int = None, debug: bool = False) -> int:
		"""
		Subtracts a specified amount from the account's balance.

		Parameters:
		x (int): The amount to subtract.
		desc (str): The description of the transaction.
		account (str): The account from which to subtract.
		created (int): The timestamp of the transaction.
		debug (bool): A flag to enable debug mode.

		Returns:
		int: The timestamp of the transaction.

		If the amount to subtract is greater than the account's balance,
		the remaining amount will be transferred to a new transaction with a negative value.

		Raises:
		ValueError: If the transction happend again in the same time.
		"""
		if x < 0:
			return
		if x == 0:
			return self.track(x, '', account)
		if created is None:
			created = ZakatTracker.time()
		_nolock = self.nolock(); self.lock()
		self.track(0, '', account)
		self._log(-x, desc, account, created)
		ids = sorted(self._vault['account'][account]['box'].keys())
		limit = len(ids) + 1
		target = x
		if debug:
			print('ids', ids)
		ages = []
		for i in range(-1, -limit, -1):
			if target == 0:
				break
			j = ids[i]
			if debug:
				print('i', i, 'j', j)
			if self._vault['account'][account]['box'][j]['rest'] >= target:
				self._vault['account'][account]['box'][j]['rest'] -= target
				self._step(Action.SUB, account, ref=j, value=target)
				ages.append((j, target))
				target = 0
				break
			elif self._vault['account'][account]['box'][j]['rest'] < target and self._vault['account'][account]['box'][j]['rest'] > 0:
				chunk = self._vault['account'][account]['box'][j]['rest']
				target -= chunk
				self._step(Action.SUB, account, ref=j, value=chunk)
				ages.append((j, chunk))
				self._vault['account'][account]['box'][j]['rest'] = 0
		if target > 0:
			self.track(-target, desc, account, False, created)
			ages.append((created, target))
		if _nolock: self.free(self.lock())
		return (created, ages)

	def transfer(self, value: int, from_account: str, to_account: str, desc: str = '', created: int = None) -> list[int]:
		"""
		Transfers a specified value from one account to another.

		Parameters:
		value (int): The amount to be transferred.
		from_account (str): The account from which the value will be transferred.
		to_account (str): The account to which the value will be transferred.
		desc (str, optional): A description for the transaction. Defaults to an empty string.
		created (int, optional): The timestamp of the transaction. If not provided, the current timestamp will be used.

		Returns:
		list[int]: A list of timestamps corresponding to the transactions made during the transfer.

		Raises:
		ValueError: If the transction happend again in the same time.
		"""
		if created is None:
			created = ZakatTracker.time()
		(_, ages) = self.sub(value, desc, from_account, created)
		times = []
		for age in ages:
			y = self.track(age[1], desc, to_account, logging=True, created=age[0])
			times.append(y)
		return times

	def check(self, silver_gram_price: float, nisab: float = None, debug: bool = False, now: int = None, cycle: float = None) -> tuple:
		"""
		Check the eligibility for Zakat based on the given parameters.

		Parameters:
		silver_gram_price (float): The price of a gram of silver.
		nisab (float): The minimum amount of wealth required for Zakat. If not provided, it will be calculated based on the silver_gram_price.
		debug (bool): Flag to enable debug mode.
		now (int): The current timestamp. If not provided, it will be calculated using ZakatTracker.time().
		cycle (float): The time cycle for Zakat. If not provided, it will be calculated using ZakatTracker.TimeCycle().

		Returns:
		tuple: A tuple containing a boolean indicating the eligibility for Zakat, a list of brief statistics, and a dictionary containing the Zakat plan.
		"""
		if now is None:
			now = ZakatTracker.time()
		if cycle is None:
			cycle = ZakatTracker.TimeCycle()
		if nisab is None:
			nisab = ZakatTracker.Nisab(silver_gram_price)
		plan = {}
		below_nisab = 0
		brief = [0, 0, 0]
		valid = False
		for x in self._vault['account']:
			if not self._vault['account'][x]['zakatable']:
				continue
			_box = self._vault['account'][x]['box']
			limit = len(_box) + 1
			ids = sorted(self._vault['account'][x]['box'].keys())
			for i in range(-1, -limit, -1):
				j = ids[i]
				if _box[j]['rest'] <= 0:
					continue
				brief[0] += _box[j]['rest']
				index = limit + i - 1
				epoch = (now - j) / cycle
				if debug:
					print(f"Epoch: {epoch}", _box[j])
				if _box[j]['last'] > 0:
					epoch = (now - _box[j]['last']) / cycle
				if debug:
					print(f"Epoch: {epoch}")
				epoch = floor(epoch)
				if debug:
					print(f"Epoch: {epoch}", type(epoch), epoch == 0, 1-epoch, epoch)
				if epoch == 0:
					continue
				if debug:
					print("Epoch - PASSED")
				brief[1] += _box[j]['rest']
				if _box[j]['rest'] >= nisab:
					total = 0
					for _ in range(epoch):
						total += ZakatTracker.ZakatCut(_box[j]['rest'] - total)
					if total > 0:
						if x not in plan:
							plan[x] = {}
						valid = True
						brief[2] += total
						plan[x][index] = {'total': total, 'count': epoch}
				else:
					chunk = ZakatTracker.ZakatCut(_box[j]['rest'])
					if chunk > 0:
						if x not in plan:
							plan[x] = {}
						if j not in plan[x].keys():
							plan[x][index] = {}
						below_nisab += _box[j]['rest']
						brief[2] += chunk
						plan[x][index]['below_nisab'] = chunk
		valid = valid or below_nisab >= nisab
		if debug:
			print(f"below_nisab({below_nisab}) >= nisab({nisab})")
		return (valid, brief, plan)

	def build_payment_parts(self, demand: float, positive_only: bool = True) -> dict:
		"""
		Build payment parts for the zakat distribution.

		Parameters:
		demand (float): The total demand for payment.
		positive_only (bool): If True, only consider accounts with positive balance. Default is True.

		Returns:
		dict: A dictionary containing the payment parts for each account. The dictionary has the following structure:
		{
			'account': {
				'account_id': {'balance': float, 'part': float},
				...
			},
			'exceed': bool,
			'demand': float,
			'total': float,
		}
		"""
		total = 0
		parts = {
			'account': {},
			'exceed': False,
			'demand': demand,
		}
		for x, y in self.accounts().items():
			if positive_only and y <= 0:
				continue
			total += y
			parts['account'][x] = {'balance': y, 'part': 0}
		parts['total'] = total
		return parts

	def check_payment_parts(self, parts: dict) -> int:
		"""
        Checks the validity of payment parts.

        Parameters:
        parts (dict): A dictionary containing payment parts information.

        Returns:
        int: Returns 0 if the payment parts are valid, otherwise returns the error code.

        Error Codes:
        1: 'demand', 'account', 'total', or 'exceed' key is missing in parts.
        2: 'balance' or 'part' key is missing in parts['account'][x].
        3: 'part' value in parts['account'][x] is less than or equal to 0.
        4: If 'exceed' is False, 'balance' value in parts['account'][x] is less than or equal to 0.
        5: 'part' value in parts['account'][x] is less than 0.
        6: If 'exceed' is False, 'part' value in parts['account'][x] is greater than 'balance' value.
        7: The sum of 'part' values in parts['account'] does not match with 'demand' value.
        """
		for i in ['demand', 'account', 'total', 'exceed']:
			if not i in parts:
				return 1
		exceed = parts['exceed']
		for x in parts['account']:
			for j in ['balance', 'part']:
				if not j in parts['account'][x]:
					return 2
				if parts['account'][x]['part'] <= 0:
					return 3
				if not exceed and parts['account'][x]['balance'] <= 0:
					return 4
		demand = parts['demand']
		z = 0
		for _, y in parts['account'].items():
			if y['part'] < 0:
				return 5
			if not exceed and y['part'] > y['balance']:
				return 6
			z += y['part']
		if z != demand:
			return 7
		return 0

	def zakat(self, report: tuple, parts: dict = None, debug: bool = False) -> bool:
		"""
		Perform Zakat calculation based on the given report and optional parts.

		Parameters:
		report (tuple): A tuple containing the validity of the report, the report data, and the zakat plan.
		parts (dict): A dictionary containing the payment parts for the zakat.
		debug (bool): A flag indicating whether to print debug information.

		Returns:
		bool: True if the zakat calculation is successful, False otherwise.
		"""
		(valid, _, plan) = report
		if not valid:
			return valid
		parts_exist = parts is not None
		if parts_exist:
			for part in parts:
				if self.check_payment_parts(part) != 0:
					return False
		if debug:
			print('######### zakat #######')
			print('parts_exist', parts_exist)
		_nolock = self.nolock(); self.lock()
		report_time = ZakatTracker.time()
		self._vault['report'][report_time] = report
		self._step(Action.REPORT, ref=report_time)
		created = ZakatTracker.time()
		for x in plan:
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
				self._step(Action.ZAKAT, x, j, value=self._vault['account'][x]['box'][j]['last'], key='last', math_operation=MathOperation.EQUAL)
				self._vault['account'][x]['box'][j]['last'] = created
				self._vault['account'][x]['box'][j]['total'] += plan[x][i]['total']
				self._step(Action.ZAKAT, x, j, value=plan[x][i]['total'], key='total', math_operation=MathOperation.ADDITION)
				self._vault['account'][x]['box'][j]['count'] += plan[x][i]['count']
				self._step(Action.ZAKAT, x, j, value=plan[x][i]['count'], key='count', math_operation=MathOperation.ADDITION)
				if not parts_exist:
					self._vault['account'][x]['box'][j]['rest'] -= plan[x][i]['total']
					self._step(Action.ZAKAT, x, j, value=plan[x][i]['total'], key='rest', math_operation=MathOperation.SUBTRACTION)
		if parts_exist:
			for transaction in parts:
				for account, part in transaction['account'].items():
					if debug:
						print('zakat-part', account, part['part'])
					self.sub(part['part'], 'zakat-part', account, debug=debug)
		if _nolock: self.free(self.lock())
		return True

	def export_json(self, path: str = "data.json") -> bool:
		"""
        Exports the current state of the ZakatTracker object to a JSON file.

        Parameters:
        path (str): The path where the JSON file will be saved. Default is "data.json".

        Returns:
        bool: True if the export is successful, False otherwise.

        Raises:
        No specific exceptions are raised by this method.
        """
		with open(path, "w") as file:
			json.dump(self._vault, file, indent=4, cls=JSONEncoder)
			return True
		return False

	def save(self, path: str = None) -> bool:
		"""
		Save the current state of the ZakatTracker object to a pickle file.

		Parameters:
		path (str): The path where the pickle file will be saved. If not provided, it will use the default path.

		Returns:
		bool: True if the save operation is successful, False otherwise.
		"""
		if path is None:
			path = self.path()
		with open(path, "wb") as f:
			pickle.dump(self._vault, f)
			return True
		return False

	def load(self, path: str = None) -> bool:
		"""
		Load the current state of the ZakatTracker object from a pickle file.

		Parameters:
		path (str): The path where the pickle file is located. If not provided, it will use the default path.

		Returns:
		bool: True if the load operation is successful, False otherwise.
		"""
		if path is None:
			path = self.path()
		if os.path.exists(path):
			with open(path, "rb") as f:
				self._vault = pickle.load(f)
				return True
		return False

	def import_csv(self, path: str = 'file.csv') -> tuple:
		"""
        Import transactions from a CSV file.

        Parameters:
        path (str): The path to the CSV file. Default is 'file.csv'.

        Returns:
        tuple: A tuple containing the number of transactions created, the number of transactions found in the cache, and a dictionary of bad transactions.

        The CSV file should have the following format:
        account, desc, value, date
        For example:
        safe-45, "Some text", 34872, 1988-06-30 00:00:00

        The function reads the CSV file, checks for duplicate transactions, and creates the transactions in the system.
        """
		cache = []
		tmp = "tmp"
		try:
			with open(tmp, "rb") as f:
				cache = pickle.load(f)
		except:
			pass
		date_formats = [
			"%Y-%m-%d %H:%M:%S",
			"%Y-%m-%dT%H:%M:%S",
			"%Y-%m-%dT%H%M%S",
			"%Y-%m-%d",
		]
		created, found, bad = 0, 0, {}
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
				date = 0
				for time_format in date_formats:
					try:
						date = self.time(datetime.datetime.strptime(row[3], time_format))
						break
					except:
						pass
				# TODO: not allowed for negative dates
				if date == 0 or value == 0:
					bad[i] = row
					continue
				if value > 0:
					self.track(value, desc, account, True, date)
				elif value < 0:
					self.sub(-value, desc, account, date)
				created += 1
				cache.append(hashed)
		with open(tmp, "wb") as f:
				pickle.dump(cache, f)
		return (created, found, bad)

	########
	# TESTS #
	#######

	@staticmethod
	def DurationFromNanoSeconds(ns: int) -> tuple:
		"""REF https://github.com/JayRizzo/Random_Scripts/blob/master/time_measure.py#L106
			Convert NanoSeconds to Human Readable Time Format.
			A NanoSeconds is a unit of time in the International System of Units (SI) equal to one millionth (0.000001 or 10−6 or 1⁄1,000,000) of a second.
			Its symbol is μs, sometimes simplified to us when Unicode is not available.
			A microsecond is equal to 1000 nanoseconds or 1⁄1,000 of a millisecond.

			INPUT : ms (AKA: MilliSeconds)
			OUTPUT: tuple(string TIMELAPSED, string SPOKENTIME) like format.
			OUTPUT Variables: TIMELAPSED, SPOKENTIME

			Example  Input: DurationFromNanoSeconds(ns)
			**"Millennium:Century:Years:Days:Hours:Minutes:Seconds:MilliSeconds:MicroSeconds:NanoSeconds"**
			Example Output: ('039:0001:047:325:05:02:03:456:789:012', ' 39 Millennia,    1 Century,  47 Years,  325 Days,  5 Hours,  2 Minutes,  3 Seconds,  456 MilliSeconds,  789 MicroSeconds,  12 NanoSeconds')
			DurationFromNanoSeconds(1234567890123456789012)
		"""
		μs, ns      = divmod(ns, 1000)
		ms, μs      = divmod(μs, 1000)
		s, ms       = divmod(ms, 1000)
		m, s        = divmod(s, 60)
		h, m        = divmod(m, 60)
		d, h        = divmod(h, 24)
		y, d        = divmod(d, 365)
		c, y        = divmod(y, 100)
		n, c        = divmod(c, 10)
		TIMELAPSED  = f"{n:03.0f}:{c:04.0f}:{y:03.0f}:{d:03.0f}:{h:02.0f}:{m:02.0f}:{s:02.0f}::{ms:03.0f}::{μs:03.0f}::{ns:03.0f}"
		SPOKENTIME  = f"{n: 3d} Millennia, {c: 4d} Century, {y: 3d} Years, {d: 4d} Days, {h: 2d} Hours, {m: 2d} Minutes, {s: 2d} Seconds, {ms: 3d} MilliSeconds, {μs: 3d} MicroSeconds, {ns: 3d} NanoSeconds"
		return TIMELAPSED, SPOKENTIME

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
	def generate_random_csv_file(path: str = "data.csv", count: int = 1000) -> None:
		"""
		Generate a random CSV file with specified parameters.

		Parameters:
		path (str): The path where the CSV file will be saved. Default is "data.csv".
		count (int): The number of rows to generate in the CSV file. Default is 1000.

		Returns:
		None. The function generates a CSV file at the specified path with the given count of rows.
		Each row contains a randomly generated account, description, value, and date.
		The value is randomly generated between 1000 and 100000, and the date is randomly generated between 1950-01-01 and 2023-12-31.
		If the row number is not divisible by 13, the value is multiplied by -1.
		"""
		with open(path, "w", newline="") as csvfile:
			writer = csv.writer(csvfile)
			for i in range(count):
				account = f"acc-{random.randint(1, 1000)}"
				desc = f"Some text {random.randint(1, 1000)}"
				value = random.randint(1000, 100000)
				date = ZakatTracker.generate_random_date(datetime.datetime(1950, 1, 1), datetime.datetime(2023, 12, 31)).strftime("%Y-%m-%d %H:%M:%S")
				if not i % 13 == 0:
					value *= -1
				writer.writerow([account, desc, value, date])

	def _test_core(self, restore = False, debug = False):
		
		random.seed(1234567890)
		
		# sanity check - random forward time
		
		xlist = []
		limit = 1000
		for _ in range(limit):
			y = ZakatTracker.time()
			z = '-'
			if not y in xlist:
				xlist.append(y)
			else:
				z = 'x'
			if debug:
				print(z, y)
		xx = len(xlist)
		if debug:
			print('count', xx, ' - unique: ', (xx/limit)*100, '%')
		assert limit == xx
		
		# sanity check - convert date since 1000AD
		
		for year in range(1000, 9000):
			ns = ZakatTracker.time(datetime.datetime.strptime(f"{year}-12-30 18:30:45","%Y-%m-%d %H:%M:%S"))
			date = ZakatTracker.time_to_datetime(ns)
			if debug:
				print(date)
			assert date.year == year
			assert date.month == 12
			assert date.day == 30
			assert date.hour == 18
			assert date.minute == 30
			assert date.second in [44, 45]
		assert self.nolock()

		assert self._history() is True
		
		table = {
			1: [
				(0,  10,   10,   10,   10, 1, 1),
				(0,  20,   30,   30,   30, 2, 2),
				(0,  30,   60,   60,   60, 3, 3),
				(1,  15,   45,   45,   45, 3, 4),
				(1,  50,   -5,   -5,   -5, 4, 5),
				(1, 100, -105, -105, -105, 5, 6),
			],
			'wallet': [
				(1,   90,  -90,  -90,  -90, 1, 1),
				(0,  100,   10,   10,   10, 2, 2),
				(1,  190, -180, -180, -180, 3, 3),
				(0, 1000,  820,  820,  820, 4, 4),
			],
		}
		for x in table:
			for y in table[x]:
				self.lock()
				ref = 0
				if y[0] == 0:
					ref = self.track(y[1], 'test-add', x, True, ZakatTracker.time(), debug)
				else:
					(ref, z) = self.sub(y[1], 'test-sub', x, ZakatTracker.time())
					if debug:
						print('_sub', z, ZakatTracker.time())
				assert ref != 0
				assert len(self._vault['account'][x]['log'][ref]['file']) == 0
				for i in range(3):
					file_ref = self.add_file(x, ref, 'file_' + str(i))
					sleep(0.0000001)
					assert file_ref != 0
					if debug:
						print('ref', ref, 'file', file_ref)
					assert len(self._vault['account'][x]['log'][ref]['file']) == i+1
				file_ref = self.add_file(x, ref, 'file_' + str(3))
				assert self.remove_file(x, ref, file_ref)
				assert self.balance(x) == y[2]
				z = self.balance(x, False)
				if debug:
					print("debug-1", z, y[3])
				assert z == y[3]
				l = self._vault['account'][x]['log']
				z = 0
				for i in l:
					z += l[i]['value']
				if debug:
					print("debug-2", z, type(z))
					print("debug-2", y[4], type(y[4]))
				assert z == y[4]
				if debug:
					print('debug-2 - PASSED')
				assert self.box_size(x) == y[5]
				assert self.log_size(x) == y[6]
				assert not self.nolock()
				self.free(self.lock())
				assert self.nolock()
			assert self.boxes(x) != {}
			assert self.logs(x) != {}

			assert self.zakatable(x)
			assert self.zakatable(x, False) is False
			assert self.zakatable(x) is False
			assert self.zakatable(x, True)
			assert self.zakatable(x)

		if restore is True:
			count = len(self._vault['history'])
			if debug:
				print('history-count', count)
			assert count == 10
			# try mode
			for _ in range(count):
				assert self.recall(True, debug)
			count = len(self._vault['history'])
			if debug:
				print('history-count', count)
			assert count == 10
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
					assert self.recall(False, debug)
			assert self.recall(False, debug) is False
			count = len(self._vault['history'])
			if debug:
				print('history-count', count)
			assert count == 0
			self.reset()

	def test(self, debug: bool = False):

		try:

			assert self._history()

			# Not allowed for duplicate transactions in the same account and time

			created = ZakatTracker.time()
			self.track(100, 'test-1', 'same', True, created)
			failed = False
			try:
				self.track(50, 'test-1', 'same', True, created)
			except:
				failed = True
			assert failed is True

			self.reset()

			# Always preserve box age during transfer

			created = ZakatTracker.time()
			series = [
				(30, 4),
				(60, 3),
				(90, 2),
			]
			case = {
				30: {
					'series': series,
					'rest' : 150,
				},
				60: {
					'series': series,
					'rest' : 120,
				},
				90: {
					'series': series,
					'rest' : 90,
				},
				180: {
					'series': series,
					'rest' : 0,
				},
				270: {
					'series': series,
					'rest' : -90,
				},
				360: {
					'series': series,
					'rest' : -180,
				},
			}

			selected_time = ZakatTracker.time() - ZakatTracker.TimeCycle()
				
			for total in case:
				for x in case[total]['series']:
					self.track(x[0], f"test-{x} ages", 'ages', True, selected_time * x[1])

				refs = self.transfer(total, 'ages', 'future', 'Zakat Movement')

				if debug:
					print('refs', refs)

				ages_cache_balance = self.balance('ages')
				ages_fresh_balance = self.balance('ages', False)
				rest = case[total]['rest']
				if debug:
					print('source', ages_cache_balance, ages_fresh_balance, rest)
				assert ages_cache_balance == rest
				assert ages_fresh_balance == rest

				future_cache_balance = self.balance('future')
				future_fresh_balance = self.balance('future', False)
				if debug:
					print('target', future_cache_balance, future_fresh_balance, total)
					print('refs', refs)
				assert future_cache_balance == total
				assert future_fresh_balance == total

				for ref in self._vault['account']['ages']['box']:
					ages_capital = self._vault['account']['ages']['box'][ref]['capital']
					ages_rest = self._vault['account']['ages']['box'][ref]['rest']
					future_capital = 0
					if ref in self._vault['account']['future']['box']:
						future_capital = self._vault['account']['future']['box'][ref]['capital']
					future_rest = 0
					if ref in self._vault['account']['future']['box']:
						future_rest = self._vault['account']['future']['box'][ref]['rest']
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
				assert len(self._vault['history']) == 0

			assert self._history()
			assert self._history(False) is False
			assert self._history() is False
			assert self._history(True)
			assert self._history()

			self._test_core(True, debug)
			self._test_core(False, debug)

			transaction = [
				(
					20, 'wallet', 1, 800, 800, 800, 4, 5,
									-85, -85, -85, 6, 7,
				),
				(
					750, 'wallet', 'safe',  50,   50,  50, 4, 6,
											750, 750, 750, 1, 1,
				),
				(
					600, 'safe', 'bank', 150, 150, 150, 1, 2,
										600, 600, 600, 1, 1,
				),
			]
			for z in transaction:
				self.lock()
				x = z[1]
				y = z[2]
				self.transfer(z[0], x, y, 'test-transfer')
				assert self.balance(x) == z[3]
				xx = self.accounts()[x]
				assert xx == z[3]
				assert self.balance(x, False) == z[4]
				assert xx == z[4]

				l = self._vault['account'][x]['log']
				s = 0
				for i in l:
					s += l[i]['value']
				if debug:
					print('s', s, 'z[5]', z[5])
				assert s == z[5]

				assert self.box_size(x) == z[6]
				assert self.log_size(x) == z[7]

				yy = self.accounts()[y]
				assert self.balance(y) == z[8]
				assert yy == z[8]
				assert self.balance(y, False) == z[9]
				assert yy == z[9]

				l = self._vault['account'][y]['log']
				s = 0
				for i in l:
					s += l[i]['value']
				assert s == z[10]

				assert self.box_size(y) == z[11]
				assert self.log_size(y) == z[12]

			if debug:
				pp().pprint(self.check(2.17))

			assert not self.nolock()
			history_count = len(self._vault['history'])
			if debug:
				print('history-count', history_count)
			assert history_count == 11
			assert not self.free(ZakatTracker.time())
			assert self.free(self.lock())
			assert self.nolock()
			assert len(self._vault['history']) == 11

			# storage

			_path = self.path('test.pickle')
			if os.path.exists(_path):
				os.remove(_path)
			self.save()
			assert os.path.getsize(_path) > 0
			self.reset()
			assert self.recall(False, debug) is False
			self.load()
			assert self._vault['account'] is not None

			# recall

			assert self.nolock()
			assert len(self._vault['history']) == 11
			assert self.recall(False, debug) is True
			assert len(self._vault['history']) == 10
			assert self.recall(False, debug) is True
			assert len(self._vault['history']) == 9

			# csv
			
			_path = "test.csv"
			count = 1000
			if os.path.exists(_path):
				os.remove(_path)
			self.generate_random_csv_file(_path, count)
			assert os.path.getsize(_path) > 0
			tmp = "tmp"
			if os.path.exists(tmp):
				os.remove(tmp)
			(created, found, bad) = self.import_csv(_path)
			bad_count = len(bad)
			if debug:
				print(f"csv-imported: ({created}, {found}, {bad_count})")
			tmp_size = os.path.getsize(tmp)
			assert tmp_size > 0
			assert created + found + bad_count == count
			assert created == count
			assert bad_count == 0
			(created_2, found_2, bad_2) = self.import_csv(_path)
			bad_2_count = len(bad_2)
			if debug:
				print(f"csv-imported: ({created_2}, {found_2}, {bad_2_count})")
				print(bad)
			assert tmp_size == os.path.getsize(tmp)
			assert created_2 + found_2 + bad_2_count == count
			assert created == found_2
			assert bad_count == bad_2_count
			assert found_2 == count
			assert bad_2_count == 0
			assert created_2 == 0

			# payment parts

			positive_parts = self.build_payment_parts(100, positive_only=True)
			assert self.check_payment_parts(positive_parts) != 0
			assert self.check_payment_parts(positive_parts) != 0
			all_parts = self.build_payment_parts(300, positive_only= False)
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
					for x, y in part['account'].items():
						if exceed and z <= demand:
							i += 1
							y['part'] = z
							if debug:
								print(exceed, y)
							cp['account'][x] = y
							case.append(y)
						elif not exceed and y['balance'] >= z:
								i += 1
								y['part'] = z
								if debug:
									print(exceed, y)
								cp['account'][x] = y
								case.append(y)
						if i >= count:
								break
					if len(cp['account'][x]) > 0:
						suite.append(cp)
			if debug:
				print('suite', len(suite))
			for case in suite:
				if debug:
					print(case)
				result = self.check_payment_parts(case)
				if debug:
					print('check_payment_parts', result)
				assert result == 0
				
			report = self.check(2.17, None, debug)
			(valid, brief, plan) = report
			if debug:
				print('valid', valid)
			assert self.zakat(report, parts=suite, debug=debug)

			assert self.export_json("1000-transactions-test.json")
			assert self.save("1000-transactions-test.pickle")

			# check & zakat

			cases = [
				(1000, 'safe', ZakatTracker.time()-ZakatTracker.TimeCycle(), [
					{'safe': {0: {'below_nisab': 25}}},
				], False),
				(2000, 'safe', ZakatTracker.time()-ZakatTracker.TimeCycle(), [
					{'safe': {0: {'count': 1, 'total': 50}}},
				], True),
				(10000, 'cave', ZakatTracker.time()-(ZakatTracker.TimeCycle()*3), [
					{'cave': {0: {'count': 3, 'total': 731.40625}}},
				], True),
			]
			for case in cases:
				if debug:
					print("############# check #############")
				self.reset()
				self.track(case[0], 'test-check', case[1], True, case[2])

				assert self.nolock()
				assert len(self._vault['history']) == 1
				assert self.lock()
				assert not self.nolock()
				report = self.check(2.17, None, debug)
				(valid, brief, plan) = report
				assert valid == case[4]
				if debug:
					print(brief)
				assert case[0] == brief[0]
				assert case[0] == brief[1]

				if debug:
					pp().pprint(plan)

				for x in plan:
					assert case[1] == x
					if 'total' in case[3][0][x][0].keys():
						assert case[3][0][x][0]['total'] == brief[2]
						assert plan[x][0]['total'] == case[3][0][x][0]['total']
						assert plan[x][0]['count'] == case[3][0][x][0]['count']
					else:
						assert plan[x][0]['below_nisab'] == case[3][0][x][0]['below_nisab']
				if debug:
					pp().pprint(report)
				result = self.zakat(report, debug=debug)
				if debug:
					print('zakat-result', result, case[4])
				assert result == case[4]
				report = self.check(2.17, None, debug)
				(valid, brief, plan) = report
				assert valid is False

			assert len(self._vault['history']) == 2
			assert not self.nolock()
			assert self.recall(False, debug) is False
			self.free(self.lock())
			assert self.nolock()
			assert len(self._vault['history']) == 2
			assert self.recall(False, debug) is True
			assert len(self._vault['history']) == 1

			assert self.nolock()
			assert len(self._vault['history']) == 1

			assert self.recall(False, debug) is True
			assert len(self._vault['history']) == 0

			assert len(self._vault['account']) == 0
			assert len(self._vault['history']) == 0
			assert len(self._vault['report']) == 0
			assert self.nolock()
		except:
			pp().pprint(self._vault)
			raise

def main():
	ledger = ZakatTracker()
	start = ZakatTracker.time()
	ledger.test(True)
	print("#########################")
	print("######## TEST DONE ########")
	print("#########################")
	print(ZakatTracker.DurationFromNanoSeconds(ZakatTracker.time()-start))
	print("#########################")

if __name__ == "__main__":
	main()
