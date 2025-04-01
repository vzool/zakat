import sqlite3, csv
import datetime
from datetime import timedelta
import argparse
import os
from pprint import PrettyPrinter as pp

debug = False

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
                        AND t.transactionCurrency IN (
                                'SDG', 'SAR', 'USD'
                            )
                ORDER BY t.transactionsTableID ASC;
            """).fetchall()
            # transform
            rows = {} # id: row
            for record in records:
                id1, account1, desc1, value1, date1, rate1 = record
                assert id1 not in rows
                rows[id1] = (account1, desc1, value1, date1, rate1)

            # look for transfer to the same account
            index = sorted(rows)
            same_account_transfer = []
            for i in range(0, len(index)):
                if i > 0:
                    account1, desc1, value1, date1, rate1 = rows[index[i]]
                    account2, desc2, value2, date2, rate2 = rows[index[i - 1]]
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
            if rest_count > 2:
                print('============================================')
                print(f"More than 2 transacions ({rest_count})...")
                pp().pprint(rows)
                y = 0
                for i, row in rows.items():
                    account1, desc1, value1, date1, rate1 = row
                    new_date = f"{date}.{y}"
                    y += 1
                    print(f"{date1} => {new_date}")
                    rows[i] = account1, desc1, value1, new_date, rate1
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
            csvwriter = csv.writer(csvfile)
            # Write the rows to the CSV file
            for _, rows in data.items():
                csvwriter.writerows(rows.values())
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
    parser = argparse.ArgumentParser(description="Process Bluecoins database and export data to CSV.")
    parser.add_argument("db_file", help="Path to the Bluecoins database file (.fydb)")
    args = parser.parse_args()

    process_bluecoins_data(args.db_file)
