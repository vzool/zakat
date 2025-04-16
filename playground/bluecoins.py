import sqlite3, csv
from datetime import timedelta
import argparse
import os
from pprint import PrettyPrinter as pp
from datetime import datetime, timedelta


debug = False


def add_millisecond_and_format(datetime_str: str, extra_ms: int = 1) -> str:
    """
    Parses a datetime string, adds a specified number of milliseconds, and returns the result as a string.
    If the input string does not contain milliseconds, it adds ".000000" before adding.

    Parameters:
    - datetime_str: A string representing a datetime, including milliseconds (e.g., "2023-10-27 10:30:45.123").
    - extra_ms: The number of milliseconds to add (default: 1).

    Returns:
    - A string representing the incremented datetime in "YYYY-MM-DD HH:MM:SS.ffffff" format.
    - Returns an error message if the input datetime string is invalid.
    """
    try:
        if "." not in datetime_str:
            datetime_str += ".000000" #added milliseconds if not present
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        incremented_dt = dt + timedelta(milliseconds=extra_ms*1e-3)
        return incremented_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM:SS.ffffff'"


def test_add_millisecond_and_format():
    """Tests for the add_millisecond_and_format function using test cases in an array."""

    test_cases = [
        ("2023-10-27 10:30:45.123456", "2023-10-27 10:30:45.123457"),
        ("2023-10-27 10:30:45.123", "2023-10-27 10:30:45.123001"),
        ("2023-10-27 10:30:45", "2023-10-27 10:30:45.000001"),
        ("2023-10-27T10:30:45.123456Z", "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM:SS.ffffff'"),
        ("2023-10-27 10:30:59.999999", "2023-10-27 10:31:00.000000"),
        ("2023-12-31 23:59:59.999999", "2024-01-01 00:00:00.000000"), #test year roll over
        ("2023-10-27 10:30:45.123455", "2023-10-27 10:30:45.123457", 2), # test with extra_ms=2
        ("2023-10-27 10:30:45", "2023-10-27 10:30:45.000002", 2), # test with extra_ms=2, and no initial ms
    ]

    for test_case in test_cases:
        input_str = test_case[0]
        expected_output = test_case[1]
        extra_ms = test_case[2] if len(test_case) > 2 else 1
        actual_output = add_millisecond_and_format(input_str, extra_ms)
        assert actual_output == expected_output, f"Test failed for input: {input_str}, actual: {actual_output}, expected: {expected_output}, extra_ms: {extra_ms}"

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
            SELECT COUNT(*) FROM TRANSACTIONSTABLE;
        """).fetchone()
        if total:
            total = total[0]

        dates_range = cursor.execute("""
            SELECT MIN(date), MAX(date)
            FROM TRANSACTIONSTABLE;
        """).fetchone()
        
        dates = cursor.execute("""
            SELECT date, COUNT(*)
            FROM TRANSACTIONSTABLE
            GROUP BY date
            ORDER BY date ASC;
        """).fetchall()
        
        days = cursor.execute("""
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d', date))
            FROM TRANSACTIONSTABLE;
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

        print(f"Found: {total} transactions shown across {days} days within {dates_range}.")
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
                ORDER BY t.transactionsTableID ASC;
            """).fetchall()
            # transform
            rows = {} # id: row
            for record in records:
                id1, account1, desc1, value1, date1, rate1 = record
                assert id1 not in rows
                # get labels if exists
                labels = cursor.execute(f"""
                    SELECT labelName
                    FROM LABELSTABLE
                    WHERE transactionIDLabels = {id1};
                """).fetchall()
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
                        same_account_transfer.append(index[i])
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
                    new_date = add_millisecond_and_format(date2, 1)
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
                    new_date = add_millisecond_and_format(date, y)
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
        exit(0)

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: Database file '{db_file}' not found.")


if __name__ == "__main__":
    # Run the tests
    test_add_millisecond_and_format()
    parser = argparse.ArgumentParser(description="Process Bluecoins database and export data to CSV.")
    parser.add_argument("db_file", help="Path to the Bluecoins database file (.fydb)")
    args = parser.parse_args()

    process_bluecoins_data(args.db_file)
