"""A module for processing and exporting Bluecoins database data to a CSV file.

This module provides functionalities to connect to a Bluecoins database (.fydb),
query transaction data, handle and resolve data conflicts like duplicates and
transactions with identical timestamps, and export the cleaned data into a
structured CSV file. It includes a utility function for precise datetime
manipulation, which is used to resolve timestamp conflicts by incrementing
a datetime by microseconds.

Functions:
    - add_microseconds_and_format(datetime_str: str, extra_us: int = 1) -> str:
        Adds a specified number of microseconds to a datetime string and
        returns a formatted string.
    - test_add_microseconds_and_format():
        A test suite for the add_microseconds_and_format function.
    - is_valid_sqlite_db(db_path: str) -> bool:
        Validates whether a file is a valid SQLite database.
    - test_is_valid_sqlite_db():
        A test suite for the is_valid_sqlite_db function.
    - get_transaction_csv_headers() -> list[str]:
        Returns the headers for the output CSV file.
    - process_bluecoins_data(db_file):
        Main function to process the database and export data.

The module can be run as a standalone script from the command line,
accepting the path to the Bluecoins database file as an argument.
"""
import sqlite3
import csv
import argparse
import os
import sys
import math
from pprint import PrettyPrinter as pp
from datetime import datetime, timedelta


debug = False
verbose = False
yes = False


def add_microseconds_and_format(datetime_str: str, extra_us: int = 1) -> str:
    """
    Parses a datetime string, adds a specified number of microseconds, and returns the result as a string.
    If the input string does not contain microseconds, it adds ".000000" before adding.

    Parameters:
    - datetime_str: A string representing a datetime, including microseconds (e.g., "2023-10-27 10:30:45.123000").
    - extra_us: The number of microseconds to add (default: 1).

    Returns:
    - A string representing the incremented datetime in "YYYY-MM-DD HH:MM:SS.ffffff" format.
    - Returns an error message if the input datetime string is invalid.
    """
    try:
        if "." not in datetime_str:
            datetime_str += ".000000" # adds microseconds if not present
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        incremented_dt = dt + timedelta(microseconds=extra_us)
        return incremented_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM:SS.ffffff'"


def test_add_microseconds_and_format():
    """Tests for the add_microseconds_and_format function using test cases in an array."""

    test_cases = [
        ("2023-10-27 10:30:45.123456", "2023-10-27 10:30:45.123457"),
        ("2023-10-27 10:30:45.123", "2023-10-27 10:30:45.123001"),
        ("2023-10-27 10:30:45", "2023-10-27 10:30:45.000001"),
        ("2023-10-27T10:30:45.123456Z", "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM:SS.ffffff'"),
        ("2023-10-27 10:30:59.999999", "2023-10-27 10:31:00.000000"),
        ("2023-12-31 23:59:59.999999", "2024-01-01 00:00:00.000000"), #test year roll over
        ("2023-10-27 10:30:45.123455", "2023-10-27 10:30:45.123457", 2), # test with extra_us=2
        ("2023-10-27 10:30:45", "2023-10-27 10:30:45.000002", 2), # test with extra_us=2, and no initial us
    ]

    for test_case in test_cases:
        input_str = test_case[0]
        expected_output = test_case[1]
        extra_us = test_case[2] if len(test_case) > 2 else 1
        actual_output = add_microseconds_and_format(input_str, extra_us)
        assert actual_output == expected_output, f"Test failed for input: {input_str}, actual: {actual_output}, expected: {expected_output}, extra_us: {extra_us}"

    if debug:
        print("All tests passed!")


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


def is_valid_sqlite_db(db_path: str) -> bool:
    """
    Checks if a given file path is a valid SQLite database file.

    Args:
        db_path: The file path (string) to check.

    Returns:
        True if the file is a valid SQLite database, False otherwise.
    """
    # 1. Check if the file exists first for an early exit
    if not os.path.exists(db_path):
        if verbose:
            print(f"error: {db_path} doesn't exist")
        return False

    # 2. Attempt to connect to the database
    conn = None
    try:
        # Attempt to connect to the file to verify it's a valid SQLite database.
        conn = sqlite3.connect(db_path)

        # Optional: Perform a very simple, non-modifying operation
        # like reading the schema version to force an actual read operation.
        # This makes the check more robust than just opening the file.
        conn.execute("PRAGMA schema_version;")

        # If we reach here, the connection was successful, and we could
        # execute a basic command, suggesting it's a valid SQLite DB.
        return True

    except sqlite3.DatabaseError:
        # Catches specific errors indicating the file is not a valid SQLite format
        # (e.g., "file is not a database")
        return False
    except Exception:
        # Catch any other unexpected errors (like permission denied, etc.)
        return False
    finally:
        # 3. Ensure the connection is closed
        if conn:
            conn.close()


def test_is_valid_sqlite_db():
    """
    Sets up temporary files, runs all validation tests using assert,
    and cleans up the created files.
    """
    valid_db_path = 'temp_test_valid.db'
    invalid_file_path = 'temp_test_invalid.txt'

    if debug:
        print("--- Starting Test Execution ---")

    # 1. SETUP: Create temporary files
    # Create a known valid database file
    try:
        conn = sqlite3.connect(valid_db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
        conn.close()
    except Exception as e:
        print(f"Setup Error: Failed to create valid DB file. Exiting. {e}")
        return

    # Create a known invalid file (a simple text file)
    try:
        with open(invalid_file_path, 'w') as f:
            f.write('This is not a database.')
    except Exception as e:
        print(f"Setup Error: Failed to create invalid text file. Exiting. {e}")
        return

    # 2. ASSERT TESTS
    try:
        if debug:
            print("Running Assertions...")

        # Test Case 1: Non-existent file
        # Expect False for a file that does not exist
        assert not is_valid_sqlite_db('non_existent.db'), "Test 1 Failed: Non-existent file."

        # Test Case 2: Known valid database file
        # Expect True for the correctly created SQLite file
        assert is_valid_sqlite_db(valid_db_path), "Test 2 Failed: Valid SQLite DB."

        # Test Case 3: Invalid text file (exists but is not a DB)
        # Expect False for the simple text file
        assert not is_valid_sqlite_db(invalid_file_path), "Test 3 Failed: Invalid text file."

        if debug:
            print("✅ All assertions passed successfully!")

    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")

    # 3. CLEANUP
    finally:
        if debug:
            print("Starting cleanup...")
        if os.path.exists(valid_db_path):
            os.remove(valid_db_path)
        if os.path.exists(invalid_file_path):
            os.remove(invalid_file_path)
        if debug:
            print("Cleanup complete.")

    if debug:
        print("--- Test Execution Finished ---")


def process_bluecoins_data(db_file):
    """
    Processes Bluecoins database file, removes duplicates, and handles time conflicts.
    Exports data to a CSV file with the same name as the database file.
    
    Parameters:
    - db_file (str): Path to the Bluecoins database file (.fydb).
    """

    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Execute a query
        total = cursor.execute("""
            SELECT COUNT(*)
            FROM TRANSACTIONSTABLE
            WHERE reminderTransaction IS NULL;
        """).fetchone()
        if total:
            total = total[0]

        dates_range = cursor.execute("""
            SELECT MIN(date), MAX(date)
            FROM TRANSACTIONSTABLE
            WHERE reminderTransaction IS NULL;
        """).fetchone()
        
        dates = cursor.execute("""
            SELECT date, COUNT(*)
            FROM TRANSACTIONSTABLE
            WHERE reminderTransaction IS NULL
            GROUP BY date
            ORDER BY date ASC;
        """).fetchall()
        
        days = cursor.execute("""
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d', date))
            FROM TRANSACTIONSTABLE
            WHERE reminderTransaction IS NULL;
        """).fetchone()
        if days:
            days = days[0]

        files = cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT transactionID)
            FROM PICTURETABLE;
        """).fetchone()
        files_count, transaction_had_files_count = (files[0], files[1]) if files else (0,0)

        labels = cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT transactionIDLabels)
            FROM LABELSTABLE;
        """).fetchone()
        labels_count, transaction_had_labels_count = (labels[0], labels[1]) if labels else (0,0)

        cols = 99
        currencies = cursor.execute("""
            SELECT  transactionCurrency,
                    COUNT(*) AS count,
                    max(conversionRateNew) AS max_rate,
                    min(conversionRateNew) AS min_rate
            FROM TRANSACTIONSTABLE
            WHERE reminderTransaction IS NULL
            GROUP BY transactionCurrency
            ORDER BY count DESC;
        """).fetchall()
        selected_currencies = str.join(',', [
            "'SDG'",
            "'SAR'",
            "'USD'",
        ])
        currencies_count = len(currencies)
        print(f"Found ({files_count}) files in ({transaction_had_files_count}) transactions...")
        print(f"Found ({labels_count}) labels in ({transaction_had_labels_count}) transactions...")
        print(f"Found ({currencies_count}) currencies...")
        if currencies_count > 0:
            print("=" * cols)
            print(f"Currency|\tCount\t|\t\tMax Rate\t\t|\t\tMin Rate\t\t|")
            print("=" * cols)
            for currency, count, max_rate, min_rate in currencies:
                print(f"{currency}\t|\t{count}\t|\t{max_rate:.24f}\t|\t{min_rate:.24f}\t|")
        print("-" * cols)
        print(f"Selected Currencies: {selected_currencies}")
        print("=" * cols)

        tx_avg = math.floor(total / days)
        print(f"Found: {total} transactions shown across {days} days (~ {tx_avg} transactions/day),")
        print(f"within {dates_range}.")
        print("-" * cols)
        if not yes:
            user_input = input("Type 'Y' to continue or anything for exit: ")
            if user_input.strip().upper() != 'Y':
                sys.exit(0)
        print("Processing...")

        data = {}
        duplicated = 0
        filtered = 0
        for date, count in dates:
            records = cursor.execute(f"""
                SELECT  t.transactionsTableID as id,
                        a.accountName AS account,
                        i.itemName AS desc,
                        t.amount AS value,
                        t.date AS date,
                        t.conversionRateNew AS rate
                FROM TRANSACTIONSTABLE AS t
                LEFT JOIN ACCOUNTSTABLE AS a ON t.accountID = a.accountsTableID
                LEFT JOIN ITEMTABLE AS i ON t.itemID = i.itemTableID
                WHERE   t.amount != 0
                        AND t.date = '{date}'
                        AND t.transactionCurrency IN ({selected_currencies})
                        AND t.reminderTransaction IS NULL
                ORDER BY t.transactionsTableID ASC;
            """).fetchall()
            # transform
            rows = {} # id: row
            for record in records:
                id1, account1, desc1, value1, date1, rate1 = record
                assert id1 not in rows
                # get labels if exists
                labels = cursor.execute("""
                    SELECT labelName
                    FROM LABELSTABLE
                    WHERE transactionIDLabels = ?;
                """, (id1, )).fetchall()
                if labels:
                    print('labels', labels)
                    desc1 += " - " + " - ".join(item[0] for item in labels)
                rows[id1] = (
                    account1,
                    desc1,
                    value1,
                    date1 + ".000000",
                    rate1,
                    id1,
                )

            # look for transfer to the same account
            index = sorted(rows)
            same_account_transfer = []
            for i in range(0, len(index)):
                if i > 0:
                    account1, desc1, value1, date1, rate1, id1 = rows[index[i]]
                    account2, desc2, value2, date2, rate2, id2 = rows[index[i - 1]]
                    if account1 == account2 and date1 == date2 and abs(value1) == abs(value2):
                        if debug:
                            print('bad============================================')
                            print(i, index[i], rows[index[i]])
                            print(i-1, index[i - 1], rows[index[i - 1]])
                        if index[i] not in same_account_transfer:
                            same_account_transfer.append(index[i])
                        if index[i - 1] not in same_account_transfer:
                            same_account_transfer.append(index[i - 1])
            # remove "same account transfer" records
            if same_account_transfer:
                if debug:
                    print('same_account_transfer', same_account_transfer)
                for i in same_account_transfer:
                    del rows[i]
            # check for duplicates and ignore them
            unique_rows = {}
            for i, row in rows.items():
                if row not in unique_rows.values():
                    unique_rows[i] = row
                else:
                    duplicated += 1
                    print('duplicated', row)
            rows = unique_rows
            rest_count = len(rows)
            filtered += rest_count
            if rest_count == 2:
                keys = list(rows.keys())
                account1, desc1, value1, date1, rate1, id1 = rows[keys[0]]
                account2, desc2, value2, date2, rate2, id2 = rows[keys[1]]
                if account1 != account2 and abs(value1) != abs(value2):
                    print('============================================')
                    print(f"Found same time different account and amount")
                    pp().pprint(rows)
                    print('--------------------------------------------')
                    new_date = add_microseconds_and_format(date2, 1)
                    print(f"{date2} => {new_date}")
                    rows[keys[1]] = account2, desc2, value2, new_date, rate2, id2
                    print('--------------------------------------------')
                    pp().pprint(rows)
                    print('--------------------------------------------')
            if rest_count > 2:
                print('============================================')
                print(f"More than 2 transacions ({rest_count})...")
                pp().pprint(rows)
                print('--------------------------------------------')
                y = 0
                for i, row in rows.items():
                    account1, desc1, value1, date1, rate1, id1 = row
                    new_date = add_microseconds_and_format(date, y)
                    y += 1
                    print(f"{date1} => {new_date}")
                    rows[i] = account1, desc1, value1, new_date, rate1, id1
                print('--------------------------------------------')
                pp().pprint(rows)
                print('--------------------------------------------')
            if rows:
                data[date] = rows

        # Close the connection
        conn.close()

        # Create the CSV filename
        csv_file = os.path.splitext(db_file)[0] + ".csv"

        # Open a CSV file for writing
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            # Create a CSV writer object
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(get_transaction_csv_headers())
            # Write the rows to the CSV file
            for _, rows in data.items():
                csv_writer.writerows(rows.values())
        print(f"Total read transactions {total}, with {total - filtered} error/ignored.")
        print(f"Filtered to {filtered} records, found {duplicated} duplicated.")
        print(f'Imported {filtered} to {csv_file}')
        print('OK')
        return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: Database file '{db_file}' not found.")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Bluecoins database and export data to CSV.")
    parser.add_argument("--self-test", action="store_true", help="Run module self-tests and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("db_file", nargs="?", help="Path to the Bluecoins database file (.fydb)")
    parser.add_argument("-y", "--yes", action="store_true", help="Proceed without confirmation prompt")
    args = parser.parse_args()

    # sys.argv is the list of command-line arguments.
    # sys.argv[0] is the script name itself, so we check if the list has only one item.
    if len(sys.argv) <= 1:
        print("🚨 No arguments provided.")
        parser.print_help(sys.stderr) # Print help message to standard error stream (optional but common practice)
        sys.exit(1) # Exit the script with a non-zero status code (convention for failure)

    # Run the tests
    verbose = args.verbose
    debug = args.self_test or verbose
    test_add_microseconds_and_format()
    test_is_valid_sqlite_db()
    if args.self_test:
        sys.exit(0)
    if not is_valid_sqlite_db(args.db_file):
        print(f"error: {args.db_file} is invalid sqlite3 database")
        sys.exit(1)
    yes = args.yes
    code = process_bluecoins_data(args.db_file)
    sys.exit(code if isinstance(code, int) else 0)
