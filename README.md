<h1 align="center">
<img src="https://raw.githubusercontent.com/vzool/zakat/main/images/logo.jpg" width="333">
</h1><br>

<div align="center" style="text-align: center;">

# ☪️ Zakat: A Python Library for Islamic Financial Management
** **We must pay Zakat if the remaining of every transaction reaches the Haul and Nisab limits** **
###### [PROJECT UNDER ACTIVE R&D]
<p>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/license-MIT%20License-red.svg"/>
    </a>
    <a href="https://www.python.org/downloads/">
        <img src="https://img.shields.io/badge/python-3.10%2B-blue"/>
    </a>
    <a href="https://github.com/vzool/zakat/actions/workflows/python-package.yml">
        <img src="https://github.com/vzool/zakat/actions/workflows/python-package.yml/badge.svg"/>
    </a>
    <a href="https://github.com/vzool/zakat/releases/latest">
        <img src="https://img.shields.io/github/release/vzool/zakat.svg"/>
    </a>
    <a href="https://pypi.org/project/zakat/">
        <img src="https://img.shields.io/pypi/v/zakat"/>
    </a>
    <a href="https://github.com/vzool/zakat/blob/main/README.ar.md">
        <img src="https://img.shields.io/badge/lang-ar-green.svg" alt="ar" data-canonical-src="https://img.shields.io/badge/lang-en-green.svg" style="max-width: 100%;">
    </a>
</p>

</div>

Zakat is a user-friendly Python library designed to simplify the tracking and calculation of Zakat, a fundamental pillar of Islamic finance. Whether you're an individual or an organization, Zakat provides the tools to accurately manage your Zakat obligations.

### Get Started:

Install the Zakat library using pip:

```bash
pip install zakat
```

###### Testing

```shell
python -c "import zakat, sys; sys.exit(zakat.test())"
```

###### Example

```python
from zakat import ZakatTracker
from datetime import datetime
from dateutil.relativedelta import relativedelta

ledger = ZakatTracker(':memory:') # or './zakat_db'

# Add balance (track a transaction)
ledger.track(10000, "Initial deposit") # default account is 1
# or
ledger.track(
    10000, # amount
    "Initial deposit", # description
    account="pocket",
    created_time_ns=ZakatTracker.time(datetime.now()),
)
# or old transaction
ledger.track(
    10000, # amount
    "Initial deposit", # description
    account="bunker",
    created_time_ns=ZakatTracker.time(datetime.now() - relativedelta(years=1)),
)

# Note: If any account does not exist it will be automatically created.

# Subtract balance
ledger.sub(500, "Plummer maintenance expense") # default account is 1
# or
ledger.sub(
    500, # amount
    "Internet monthly subscription", # description
    account="pocket",
    created_time_ns=ZakatTracker.time(datetime.now()),
)

# Transfer balance
ledger.transfer(100, "pocket", "bank") # default time is now
# or
ledger.transfer(
    100,
    "pocket", # from account
    "safe", # to account
    created_time_ns=ZakatTracker.time(datetime.now()),
)
# or
ledger.exchange("bank (USD)", 3.75) # rate
ledger.transfer(375, "pocket", "bank (USD)") # This time exchange rates considered

# Note: The age of balances in all transactions are preserved while transfering.

# Estimate Zakat (generate a report)
report = ledger.check(silver_gram_price=2.5)

valid, brief, plan = report # True, [2900000.0, 1000000.0, 25000.0], ...

# valid (bool): any transactions reached Haul and Nisab limits collectively?
# brief (list:3) = [a, b, c]

a, b, c = brief
# a: sum of all balances
# b: sum of all transactions applicable to Zakat collectively
# c: Zakat cut summary due

# Perform Zakat (Apply Zakat)
# discount from the same accounts if Zakat applicable individually or collectively
ledger.zakat(report) # --> True
# or Collect all Zakat and discount from selected accounts
parts = ledger.build_payment_parts(c)
# modify `parts` to distribute your Zakat on selected accounts
ledger.zakat(report, parts) # --> False
```

###### Vault data structure:

The main data storage file system on disk is [`camelX`](https://github.com/vzool/camelX) format, but it is shown in JSON format for example above (note: times will different if applied by yourself):

```json
{
    "account": {
        "1": {
            "balance": 950000,
            "box": {
                "63877648909315874816": {
                    "capital": 1000000,
                    "count": 0,
                    "last": 0,
                    "rest": 950000,
                    "total": 0
                }
            },
            "count": 2,
            "log": {
                "63877648909315874816": {
                    "value": 1000000,
                    "desc": "Initial deposit",
                    "ref": null,
                    "file": {}
                },
                "63877648909316186112": {
                    "value": -50000,
                    "desc": "Plummer maintenance expense",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877648909315874816
        },
        "pocket": {
            "balance": 892500,
            "box": {
                "63877648909315997696": {
                    "capital": 1000000,
                    "count": 0,
                    "last": 0,
                    "rest": 892500,
                    "total": 0
                }
            },
            "count": 5,
            "log": {
                "63877648909315997696": {
                    "value": 1000000,
                    "desc": "Initial deposit",
                    "ref": null,
                    "file": {}
                },
                "63877648909316251648": {
                    "value": -50000,
                    "desc": "Internet monthly subscription",
                    "ref": null,
                    "file": {}
                },
                "63877648909316571136": {
                    "value": -10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                },
                "63877648909316677632": {
                    "value": -10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                },
                "63877648909316784128": {
                    "value": -37500,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877648909315997696
        },
        "bunker": {
            "balance": 975000.0,
            "box": {
                "63846112909316063232": {
                    "capital": 1000000,
                    "count": 1,
                    "last": 63877648909317111808,
                    "rest": 975000.0,
                    "total": 25000.0
                }
            },
            "count": 2,
            "log": {
                "63846112909316063232": {
                    "value": 1000000,
                    "desc": "Initial deposit",
                    "ref": null,
                    "file": {}
                },
                "63877648909317152768": {
                    "value": -25000.0,
                    "desc": "zakat-\u0632\u0643\u0627\u0629",
                    "ref": 63846112909316063232,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63846112909316063232
        },
        "bank": {
            "balance": 10000,
            "box": {
                "63877648909315997696": {
                    "capital": 10000,
                    "count": 0,
                    "last": 0,
                    "rest": 10000,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877648909315997696": {
                    "value": 10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877648909315997696
        },
        "safe": {
            "balance": 10000,
            "box": {
                "63877648909315997696": {
                    "capital": 10000,
                    "count": 0,
                    "last": 0,
                    "rest": 10000,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877648909315997696": {
                    "value": 10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877648909315997696
        },
        "bank (USD)": {
            "balance": 37500,
            "box": {
                "63877648909315997696": {
                    "capital": 37500,
                    "count": 0,
                    "last": 0,
                    "rest": 37500,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877648909315997696": {
                    "value": 37500,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877648909315997696
        }
    },
    "exchange": {},
    "history": {
        "63877648909315907584": [
            {
                "action": "CREATE",
                "account": 1,
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": 1,
                "ref": 63877648909315874816,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": 1,
                "ref": 63877648909315874816,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877648909316014080": [
            {
                "action": "CREATE",
                "account": "pocket",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877648909316145152": [
            {
                "action": "CREATE",
                "account": "bunker",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "bunker",
                "ref": 63846112909316063232,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "bunker",
                "ref": 63846112909316063232,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877648909316202496": [
            {
                "action": "LOG",
                "account": 1,
                "ref": 63877648909316186112,
                "file": null,
                "key": null,
                "value": -50000,
                "math": null
            },
            {
                "action": "SUB",
                "account": 1,
                "ref": 63877648909315874816,
                "file": null,
                "key": null,
                "value": 50000,
                "math": null
            }
        ],
        "63877648909316268032": [
            {
                "action": "LOG",
                "account": "pocket",
                "ref": 63877648909316251648,
                "file": null,
                "key": null,
                "value": -50000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 50000,
                "math": null
            }
        ],
        "63877648909316579328": [
            {
                "action": "LOG",
                "account": "pocket",
                "ref": 63877648909316571136,
                "file": null,
                "key": null,
                "value": -10000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "bank",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "bank",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "bank",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            }
        ],
        "63877648909316685824": [
            {
                "action": "LOG",
                "account": "pocket",
                "ref": 63877648909316677632,
                "file": null,
                "key": null,
                "value": -10000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "safe",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "safe",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "safe",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            }
        ],
        "63877648909316800512": [
            {
                "action": "LOG",
                "account": "pocket",
                "ref": 63877648909316784128,
                "file": null,
                "key": null,
                "value": -37500,
                "math": null
            },
            {
                "action": "SUB",
                "account": "pocket",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 37500,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "bank (USD)",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "bank (USD)",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 37500,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "bank (USD)",
                "ref": 63877648909315997696,
                "file": null,
                "key": null,
                "value": 37500,
                "math": null
            }
        ],
        "63877648909317079040": [
            {
                "action": "REPORT",
                "account": null,
                "ref": 63877648909317095424,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "ZAKAT",
                "account": "bunker",
                "ref": 63846112909316063232,
                "file": null,
                "key": "last",
                "value": 0,
                "math": "EQUAL"
            },
            {
                "action": "ZAKAT",
                "account": "bunker",
                "ref": 63846112909316063232,
                "file": null,
                "key": "total",
                "value": 25000.0,
                "math": "ADDITION"
            },
            {
                "action": "ZAKAT",
                "account": "bunker",
                "ref": 63846112909316063232,
                "file": null,
                "key": "count",
                "value": 1,
                "math": "ADDITION"
            },
            {
                "action": "LOG",
                "account": "bunker",
                "ref": 63877648909317152768,
                "file": null,
                "key": null,
                "value": -25000.0,
                "math": null
            }
        ]
    },
    "lock": null,
    "report": {
        "63877648909317095424": [
            true,
            [
                2900000.0,
                1000000.0,
                25000.0
            ],
            {
                "bunker": {
                    "0": {
                        "total": 25000.0,
                        "count": 1,
                        "box_time": 63846112909316063232,
                        "box_capital": 1000000,
                        "box_rest": 1000000,
                        "box_last": 0,
                        "box_total": 0,
                        "box_count": 0,
                        "box_log": "Initial deposit",
                        "exchange_rate": 1,
                        "exchange_time": 63877648909316956160,
                        "exchange_desc": null
                    }
                }
            }
        ]
    }
}
```

### Key Features:

- Transaction Tracking: Easily record both income and expenses with detailed descriptions, ensuring comprehensive financial records.

- Automated Zakat Calculation: Automatically calculate Zakat due based on the Nisab (minimum threshold), Haul (time cycles) and the current market price of silver, simplifying compliance with Islamic financial principles.

- Customizable "Nisab": Set your own "Nisab" value based on your preferred calculation method or personal financial situation.

- Customizable "Haul": Set your own "Haul" cycle based on your preferred calender method or personal financial situation.

- Multiple Accounts: Manage Zakat for different assets or accounts separately for greater financial clarity.

- Import/Export: Seamlessly import transaction data from CSV files and export calculated Zakat reports in JSON format for further analysis or record-keeping.

- Data Persistence: Securely save and load your Zakat tracker data for continued use across sessions.

- History Tracking: Optionally enable a detailed history of actions for transparency and review (can be disabled optionally).

### Benefits:

- Accurate Zakat Calculation: Ensure precise calculation of Zakat obligations, promoting financial responsibility and spiritual well-being.

- Streamlined Financial Management: Simplify the management of your finances by keeping track of transactions and Zakat calculations in one place.

- Enhanced Transparency: Maintain a clear record of your financial activities and Zakat payments for greater accountability and peace of mind.

- User-Friendly: Easily navigate through the library's intuitive interface and functionalities, even without extensive technical knowledge.

### Customizable:

- Tailor the library's settings (e.g., Nisab value and Haul cycles) to your specific needs and preferences.

### Who Can Benefit:

- Individuals: Effectively manage personal finances and fulfill Zakat obligations.

- Organizations: Streamline Zakat calculation and distribution for charitable projects and initiatives.

- Islamic Financial Institutions: Integrate Zakat into existing systems for enhanced financial management and reporting.

### Documentation

- [Mechanism of Zakat: The Rooms and Boxes Algorithm](./docs/markdown/algorithm.md)

- [The Zakat Formula: A Mathematical Representation of Islamic Charity](./docs/markdown/mathematics.md)

- [How Exchange Rates Work in a Zakat Calculation System?](./docs/markdown/exchange_rates.md)

- [Zakat-Aware Inventory Tracking Algorithm (with Lunar Cycle)](./docs/markdown/inventory.md) [**PLANNED**]

### Videos:

* [Mastering Zakat: The Rooms and Boxes Algorithm Explained!](https://www.youtube.com/watch?v=maxttQ5Xo5g)
* [طريقة الزكاة في العصر الرقمي: خوارزمية الغرف والصناديق](https://www.youtube.com/watch?v=kuhHzPjYD6o)
* [Zakat Algorithm in 42 seconds](https://www.youtube.com/watch?v=1ipCcqf48go)
* [How Exchange Rates Impact Zakat Calculation?](https://www.youtube.com/watch?v=PW6tjZgtShE)

Explore the documentation, source code and examples to begin tracking your Zakat and achieving financial peace of mind in accordance with Islamic principles.
