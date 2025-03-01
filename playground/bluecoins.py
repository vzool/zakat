import sqlite3, csv
import datetime
from datetime import timedelta
  
# Connect to the database
conn = sqlite3.connect('bluecoins.fydb')
cursor = conn.cursor()
sql = """
-- account, desc, value, date, rate
SELECT	a.accountName AS account,
					i.itemName AS desc,
					t.amount AS value,
					t.date AS date,
					t.conversionRateNew AS rate
					-- , t.transactionsTableID as id
FROM TRANSACTIONSTABLE AS t
LEFT JOIN ACCOUNTSTABLE AS a ON t.accountID = a.accountsTableID
LEFT JOIN ITEMTABLE AS i ON t.itemID = i.itemTableID
WHERE	t.amount != 0
					AND	t.transactionCurrency IN (
									'SDG'
									,'SAR'
									, 'USD'
								)
ORDER BY t.date ASC;
"""
# Execute a query
cursor.execute(sql)
rows = cursor.fetchall()
# Close the connection
conn.close()

z = 0
print('before-unique', len(rows))
unique_list = []
for row in rows:
    if row not in unique_list:
        unique_list.append(row)
    else:
    	z += 1
    	print('duplicated', row)
rows = unique_list
print('after-unique', len(rows))

# look for transfer to the same account
x = 0
bad = []
for i in range(0, len(rows)):
	if i > 0:
		account1, desc1, value1, date1, rate1 = rows[i]
		account2, desc2, value2, date2, rate2 = rows[i - 1]
		if account1 == account2 and date1 == date2 and abs(value1) == abs(value2):
			bad.append(i - 1)
			bad.append(i)
			x += 1
			print(i-1, rows[i - 1])
			print(i, rows[i])
			print('b============================================================')

# remove bad records
for i in bad:
	del rows[i]

# check for duplicated times

# look for transactions in the same time with different amount
y = 0
for i in range(0, len(rows)):
	if i > 0:
		account1, desc1, value1, date1, rate1 = rows[i]
		account2, desc2, value2, date2, rate2 = rows[i - 1]
		if abs(value1) != abs(value2) and date1 == date2:
			print(i-1, rows[i - 1])
			print(i, rows[i])
			print('t============================================================')
			new_date = (datetime.datetime.strptime(rows[i][3], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
			print(rows[i][3])
			print(new_date)
			print('-------------------------------------------------------------------------------------------------------------------')
			account, desc, value, date, rate = rows[i]
			rows[i] = (account, desc, value, new_date, rate)
			y += 1

print('Duplicated-count', z)
print('Same-transfer-account-count', x)
print('Same-transfer-time-count', y)
# Open a CSV file for writing
with open('bluecoins.csv', 'w', newline='') as csvfile:
  # Create a CSV writer object
  csvwriter = csv.writer(csvfile)
  # Write the column names (optional)
  #csvwriter.writerow([description[0] for description in cursor.description])
  # Write the rows to the CSV file
  csvwriter.writerows(rows)
print(f'imported {len(rows)}')
