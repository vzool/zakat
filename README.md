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
parts = ledger.build_payment_parts(zakat_report.summary.total_zakat_due)
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
      "created": 63879017256646705000,
      "name": "",
      "box": {
        "63879017256646705152": {
          "capital": 1000000,
          "rest": 950000,
          "zakat": {
            "count": 0,
            "last": 0,
            "total": 0
          }
        }
      },
      "count": 2,
      "log": {
        "63879017256646705152": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63879017256648155136": {
          "value": -50000,
          "desc": "Plummer maintenance expense",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017256647188480": {
      "balance": 892500,
      "created": 63879017256647230000,
      "name": "pocket",
      "box": {
        "63879017256647409664": {
          "capital": 1000000,
          "rest": 892500,
          "zakat": {
            "count": 0,
            "last": 0,
            "total": 0
          }
        }
      },
      "count": 5,
      "log": {
        "63879017256647409664": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63879017256648392704": {
          "value": -50000,
          "desc": "Internet monthly subscription",
          "ref": null,
          "file": {}
        },
        "63879017256648802304": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63879017256649555968": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63879017256650096640": {
          "value": -37500,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017256647622656": {
      "balance": 975000,
      "created": 63879017256647655000,
      "name": "bunker",
      "box": {
        "63847481256647794688": {
          "capital": 1000000,
          "rest": 975000,
          "zakat": {
            "count": 1,
            "last": 63879017256650820000,
            "total": 25000
          }
        }
      },
      "count": 2,
      "log": {
        "63847481256647794688": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63879017256650932224": {
          "value": -25000,
          "desc": "zakat-زكاة",
          "ref": 63847481256647795000,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017256648605696": {
      "balance": 10000,
      "created": 63879017256648640000,
      "name": "bank",
      "box": {
        "63879017256647409664": {
          "capital": 10000,
          "rest": 10000,
          "zakat": {
            "count": 0,
            "last": 0,
            "total": 0
          }
        }
      },
      "count": 1,
      "log": {
        "63879017256647409664": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017256649383936": {
      "balance": 10000,
      "created": 63879017256649425000,
      "name": "safe",
      "box": {
        "63879017256647409664": {
          "capital": 10000,
          "rest": 10000,
          "zakat": {
            "count": 0,
            "last": 0,
            "total": 0
          }
        }
      },
      "count": 1,
      "log": {
        "63879017256647409664": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017256649859072": {
      "balance": 10000,
      "created": 63879017256649890000,
      "name": "bank (USD)",
      "box": {
        "63879017256647409664": {
          "capital": 10000,
          "rest": 10000,
          "zakat": {
            "count": 0,
            "last": 0,
            "total": 0
          }
        }
      },
      "count": 1,
      "log": {
        "63879017256647409664": {
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
    "63879017256649859072": {
      "63879017256649998336": {
        "rate": 3.75,
        "description": null,
        "time": 63879017256650000000
      }
    }
  },
  "history": {
    "63879017256646787072": {
      "63879017256646885376": {
        "action": "CREATE",
        "account": "1",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      "63879017256647065600": {
        "action": "LOG",
        "account": "1",
        "ref": 63879017256646705000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017256647139328": {
        "action": "TRACK",
        "account": "1",
        "ref": 63879017256646705000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017256647254016": {
      "63879017256647303168": {
        "action": "CREATE",
        "account": "63879017256647188480",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017256647352320": {
      "63879017256647385088": {
        "action": "NAME",
        "account": "63879017256647188480",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017256647442432": {
      "63879017256647540736": {
        "action": "LOG",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017256647589888": {
        "action": "TRACK",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017256647680000": {
      "63879017256647712768": {
        "action": "CREATE",
        "account": "63879017256647622656",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017256647745536": {
      "63879017256647778304": {
        "action": "NAME",
        "account": "63879017256647622656",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017256647999488": {
      "63879017256648081408": {
        "action": "LOG",
        "account": "63879017256647622656",
        "ref": 63847481256647795000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017256648122368": {
        "action": "TRACK",
        "account": "63879017256647622656",
        "ref": 63847481256647795000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017256648187904": {
      "63879017256648294400": {
        "action": "LOG",
        "account": "1",
        "ref": 63879017256648155000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      "63879017256648351744": {
        "action": "SUBTRACT",
        "account": "1",
        "ref": 63879017256646705000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    },
    "63879017256648425472": {
      "63879017256648531968": {
        "action": "LOG",
        "account": "63879017256647188480",
        "ref": 63879017256648390000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      "63879017256648564736": {
        "action": "SUBTRACT",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    },
    "63879017256648663040": {
      "63879017256648704000": {
        "action": "CREATE",
        "account": "63879017256648605696",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017256648736768": {
      "63879017256648761344": {
        "action": "NAME",
        "account": "63879017256648605696",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017256648818688": {
      "63879017256649031680": {
        "action": "LOG",
        "account": "63879017256647188480",
        "ref": 63879017256648800000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      "63879017256649072640": {
        "action": "SUBTRACT",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017256649285632": {
        "action": "LOG",
        "account": "63879017256648605696",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017256649334784": {
        "action": "TRACK",
        "account": "63879017256648605696",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017256649441280": {
      "63879017256649482240": {
        "action": "CREATE",
        "account": "63879017256649383936",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017256649515008": {
      "63879017256649539584": {
        "action": "NAME",
        "account": "63879017256649383936",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017256649580544": {
      "63879017256649662464": {
        "action": "LOG",
        "account": "63879017256647188480",
        "ref": 63879017256649560000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      "63879017256649695232": {
        "action": "SUBTRACT",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017256649801728": {
        "action": "LOG",
        "account": "63879017256649383936",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017256649826304": {
        "action": "TRACK",
        "account": "63879017256649383936",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017256649900032": {
      "63879017256649932800": {
        "action": "CREATE",
        "account": "63879017256649859072",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017256649957376": {
      "63879017256649973760": {
        "action": "NAME",
        "account": "63879017256649859072",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017256650022912": {
      "63879017256650047488": {
        "action": "EXCHANGE",
        "account": "63879017256649859072",
        "ref": 63879017256650000000,
        "file": null,
        "key": null,
        "value": 3.75,
        "math": null
      }
    },
    "63879017256650121216": {
      "63879017256650203136": {
        "action": "LOG",
        "account": "63879017256647188480",
        "ref": 63879017256650100000,
        "file": null,
        "key": null,
        "value": -37500,
        "math": null
      },
      "63879017256650227712": {
        "action": "SUBTRACT",
        "account": "63879017256647188480",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 37500,
        "math": null
      },
      "63879017256650334208": {
        "action": "LOG",
        "account": "63879017256649859072",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017256650366976": {
        "action": "TRACK",
        "account": "63879017256649859072",
        "ref": 63879017256647410000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017256650760192": {
      "63879017256650801152": {
        "action": "REPORT",
        "account": null,
        "ref": 63879017256650785000,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      "63879017256650866688": {
        "action": "ZAKAT",
        "account": "63879017256647622656",
        "ref": 63847481256647795000,
        "file": null,
        "key": "last",
        "value": 0,
        "math": "EQUAL"
      },
      "63879017256650891264": {
        "action": "ZAKAT",
        "account": "63879017256647622656",
        "ref": 63847481256647795000,
        "file": null,
        "key": "total",
        "value": 25000,
        "math": "ADDITION"
      },
      "63879017256650907648": {
        "action": "ZAKAT",
        "account": "63879017256647622656",
        "ref": 63847481256647795000,
        "file": null,
        "key": "count",
        "value": 1,
        "math": "ADDITION"
      },
      "63879017256650964992": {
        "action": "LOG",
        "account": "63879017256647622656",
        "ref": 63879017256650930000,
        "file": null,
        "key": null,
        "value": -25000,
        "math": null
      }
    }
  },
  "lock": null,
  "report": {
    "63879017256650784768": {
      "valid": true,
      "summary": {
        "total_wealth": 2900000,
        "num_zakatable_items": 1,
        "total_zakatable_amount": 1000000,
        "total_zakat_due": 25000
      },
      "plan": {
        "63879017256647622656": [
          {
            "box": {
              "capital": 1000000,
              "rest": 975000,
              "zakat": {
                "count": 1,
                "last": 63879017256650820000,
                "total": 25000
              }
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
              "time": 63879017256650555000
            },
            "below_nisab": false,
            "total": 25000,
            "count": 1,
            "ref": 63847481256647795000
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
