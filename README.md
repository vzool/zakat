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
from zakat import tracker, time
from datetime import datetime
from dateutil.relativedelta import relativedelta

ledger = tracker(':memory:') # or './zakat_db'

# Add balance (track a transaction)
ledger.track(10000, "Initial deposit") # default account is 1
# or
pocket_account_id = ledger.create_account("pocket")
ledger.track(
    10000, # amount
    "Initial deposit", # description
    account=pocket_account_id,
    created_time_ns=time(datetime.now()),
)
# or old transaction
box_ref = ledger.track(
    10000, # amount
    "Initial deposit", # description
    account=ledger.create_account("bunker"),
    created_time_ns=time(datetime.now() - relativedelta(years=1)),
)

# Note: If any account does not exist it will be automatically created.

# Subtract balance
ledger.subtract(500, "Plummer maintenance expense") # default account is 1
# or
subtract_report = ledger.subtract(
    500, # amount
    "Internet monthly subscription", # description
    account=pocket_account_id,
    created_time_ns=time(datetime.now()),
)

# Transfer balance
bank_account_id = ledger.create_account("bank")
ledger.transfer(100, pocket_account_id, bank_account_id) # default time is now
# or
transfer_report = ledger.transfer(
    100,
    from_account=pocket_account_id,
    to_account=ledger.create_account("safe"),
    created_time_ns=time(datetime.now()),
)
# or
bank_usd_account_id = ledger.create_account("bank (USD)")
ledger.exchange(bank_usd_account_id, rate=3.75) # suppose current currency is SAR rate=1
ledger.transfer(375, pocket_account_id, bank_usd_account_id) # This time exchange rates considered

# Note: The age of balances in all transactions are preserved while transfering.

# Estimate Zakat (generate a report)
zakat_report = ledger.check(silver_gram_price=2.5)


# Perform Zakat (Apply Zakat)
# discount from the same accounts if Zakat applicable individually or collectively
ledger.zakat(zakat_report) # --> True
# or Collect all Zakat and discount from selected accounts
parts = ledger.build_payment_parts(zakat_report.statistics.zakat_cut_balances)
# modify `parts` to distribute your Zakat on selected accounts
ledger.zakat(zakat_report, parts) # --> False
```

###### Vault data structure:

The main data storage file system on disk is [`JSON`](https://json.org/) format, but it is shown here in JSON format for data generated by the example above (note: times will be different if re-applied by yourself):

```json
{
  "account": {
    "1": {
      "balance": 950000,
      "created": 63878934600205940000,
      "name": "",
      "box": {
        "63878934600205942784": {
          "capital": 1000000,
          "count": 0,
          "last": 0,
          "rest": 950000,
          "total": 0
        }
      },
      "count": 2,
      "log": {
        "63878934600205942784": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63878934600207310848": {
          "value": -50000,
          "desc": "Plummer maintenance expense",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878934600206401536": {
      "balance": 892500,
      "created": 63878934600206480000,
      "name": "pocket",
      "box": {
        "63878934600206639104": {
          "capital": 1000000,
          "count": 0,
          "last": 0,
          "rest": 892500,
          "total": 0
        }
      },
      "count": 5,
      "log": {
        "63878934600206639104": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63878934600207499264": {
          "value": -50000,
          "desc": "Internet monthly subscription",
          "ref": null,
          "file": {}
        },
        "63878934600207835136": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63878934600208302080": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63878934600208826368": {
          "value": -37500,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878934600206794752": {
      "balance": 975000,
      "created": 63878934600206836000,
      "name": "bunker",
      "box": {
        "63847398600206958592": {
          "capital": 1000000,
          "count": 1,
          "last": 63878934600209790000,
          "rest": 975000,
          "total": 25000
        }
      },
      "count": 2,
      "log": {
        "63847398600206958592": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63878934600209907712": {
          "value": -25000,
          "desc": "zakat-زكاة",
          "ref": 63847398600206960000,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878934600207663104": {
      "balance": 10000,
      "created": 63878934600207710000,
      "name": "bank",
      "box": {
        "63878934600206639104": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878934600206639104": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878934600208146432": {
      "balance": 10000,
      "created": 63878934600208196000,
      "name": "safe",
      "box": {
        "63878934600206639104": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878934600206639104": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878934600208564224": {
      "balance": 10000,
      "created": 63878934600208610000,
      "name": "bank (USD)",
      "box": {
        "63878934600206639104": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878934600206639104": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    }
  },
  "exchange": {
    "63878934600208564224": {
      "63878934600208728064": {
        "rate": 3.75,
        "description": null,
        "time": 63878934600208730000
      }
    }
  },
  "history": {
    "63878934600206049280": [
      {
        "action": "CREATE",
        "account": "1",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      {
        "action": "LOG",
        "account": "1",
        "ref": 63878934600205940000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "1",
        "ref": 63878934600205940000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878934600206516224": [
      {
        "action": "CREATE",
        "account": "63878934600206401536",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878934600206589952": [
      {
        "action": "NAME",
        "account": "63878934600206401536",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    ],
    "63878934600206671872": [
      {
        "action": "LOG",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878934600206860288": [
      {
        "action": "CREATE",
        "account": "63878934600206794752",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878934600206917632": [
      {
        "action": "NAME",
        "account": "63878934600206794752",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    ],
    "63878934600207212544": [
      {
        "action": "LOG",
        "account": "63878934600206794752",
        "ref": 63847398600206960000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878934600206794752",
        "ref": 63847398600206960000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878934600207343616": [
      {
        "action": "LOG",
        "account": "1",
        "ref": 63878934600207310000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "1",
        "ref": 63878934600205940000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    ],
    "63878934600207532032": [
      {
        "action": "LOG",
        "account": "63878934600206401536",
        "ref": 63878934600207500000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    ],
    "63878934600207736832": [
      {
        "action": "CREATE",
        "account": "63878934600207663104",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878934600207785984": [
      {
        "action": "NAME",
        "account": "63878934600207663104",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    ],
    "63878934600207859712": [
      {
        "action": "LOG",
        "account": "63878934600206401536",
        "ref": 63878934600207835000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "LOG",
        "account": "63878934600207663104",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878934600207663104",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878934600208220160": [
      {
        "action": "CREATE",
        "account": "63878934600208146432",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878934600208269312": [
      {
        "action": "NAME",
        "account": "63878934600208146432",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    ],
    "63878934600208334848": [
      {
        "action": "LOG",
        "account": "63878934600206401536",
        "ref": 63878934600208300000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "LOG",
        "account": "63878934600208146432",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878934600208146432",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878934600208637952": [
      {
        "action": "CREATE",
        "account": "63878934600208564224",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878934600208687104": [
      {
        "action": "NAME",
        "account": "63878934600208564224",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    ],
    "63878934600208760832": [
      {
        "action": "EXCHANGE",
        "account": "63878934600208564224",
        "ref": 63878934600208730000,
        "file": null,
        "key": null,
        "value": 3.75,
        "math": null
      }
    ],
    "63878934600208850944": [
      {
        "action": "LOG",
        "account": "63878934600206401536",
        "ref": 63878934600208830000,
        "file": null,
        "key": null,
        "value": -37500,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878934600206401536",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 37500,
        "math": null
      },
      {
        "action": "LOG",
        "account": "63878934600208564224",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878934600208564224",
        "ref": 63878934600206640000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878934600209727488": [
      {
        "action": "REPORT",
        "account": null,
        "ref": 63878934600209760000,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      {
        "action": "ZAKAT",
        "account": "63878934600206794752",
        "ref": 63847398600206960000,
        "file": null,
        "key": "last",
        "value": 0,
        "math": "EQUAL"
      },
      {
        "action": "ZAKAT",
        "account": "63878934600206794752",
        "ref": 63847398600206960000,
        "file": null,
        "key": "total",
        "value": 25000,
        "math": "ADDITION"
      },
      {
        "action": "ZAKAT",
        "account": "63878934600206794752",
        "ref": 63847398600206960000,
        "file": null,
        "key": "count",
        "value": 1,
        "math": "ADDITION"
      },
      {
        "action": "LOG",
        "account": "63878934600206794752",
        "ref": 63878934600209910000,
        "file": null,
        "key": null,
        "value": -25000,
        "math": null
      }
    ]
  },
  "lock": null,
  "report": {
    "63878934600209760256": {
      "valid": true,
      "statistics": {
        "overall_wealth": 2900000,
        "zakatable_transactions_count": 0,
        "zakatable_transactions_balance": 1000000,
        "zakat_cut_balances": 25000
      },
      "plan": {
        "63878934600206794752": [
          {
            "box": {
              "capital": 1000000,
              "count": 1,
              "last": 63878934600209790000,
              "rest": 975000,
              "total": 25000
            },
            "log": {
              "value": 1000000,
              "desc": "Initial deposit",
              "ref": null,
              "file": {}
            },
            "exchange": {
              "rate": 1,
              "description": null,
              "time": 63878934600209460000
            },
            "below_nisab": false,
            "total": 25000,
            "count": 1,
            "ref": 63847398600206960000
          }
        ]
      }
    }
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
