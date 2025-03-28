<h1 align="center">
<img src="https://raw.githubusercontent.com/vzool/zakat/main/images/logo.jpg" width="333">
</h1><br>

<div align="center" style="text-align: center;">

<div dir="rtl">

# ☪️ الزكاة (Zakat): مكتبة بايثون للإدارة المالية الإسلامية
** **يجب علينا إخراج الزكاة إذا بلغ ما تبقى من كل معاملة مالية مقدار النصاب ومدة الحول** **

###### [المشروع تحت البحث والتطوير النشط]
</div>

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
    <a href="https://github.com/vzool/zakat/blob/main/README.md">
        <img src="https://img.shields.io/badge/lang-en-green.svg" alt="en" data-canonical-src="https://img.shields.io/badge/lang-en-green.svg" style="max-width: 100%;">
    </a>
</p>
</div>

<div dir="rtl">

الزكاة (Zakat) هي مكتبة بايثون سهلة الاستخدام مصممة لتبسيط عملية تتبع وحساب الزكاة، وهي ركن أساسي في المالية الإسلامية. سواء كنت فردًا أو مؤسسة، يوفر الزكاة (Zakat) الأدوات اللازمة لإدارة التزاماتك الزكوية بدقة.

### ابدأ الآن:

قم بتثبيت مكتبة الزكاة (Zakat) باستخدام pip:

```bash
pip install zakat
```

###### الاختبارات

```bash
python -c "import zakat, sys; sys.exit(zakat.test())"
```

###### مثال

```python
from zakat import ZakatTracker, Time
from datetime import datetime
from dateutil.relativedelta import relativedelta

ledger = ZakatTracker(':memory:') # or './zakat_db'

# إضافة رصيد (تتبع عملية مالية)
ledger.track(10000, "ايداع مبدئي") # default account is 1
# أو
pocket_account_id = ledger.create_account("الجيب")
ledger.track(
    10000, # المبلغ
    "ايداع مبدئي",
    account=pocket_account_id,
    created_time_ns=Time.time(datetime.now()),
)
# أو معاملة بتاريخ قديم
box_ref = ledger.track(
    10000, # المبلغ
    "Initial deposit", # الوصف
    account=ledger.create_account("المخبئ"),
    created_time_ns=Time.time(datetime.now() - relativedelta(years=1)),
)

# ملحوظة: إذا لم يكن هناك حساب موجود، فسيتم إنشاؤه تلقائيًا.

# خصم
ledger.subtract(500, "Plummer maintenance expense") # الحساب الافتراضي هو 1
# or
subtract_report = ledger.subtract(
    500, # المبلغ
    "اشتراك الانترنت الشهري",
    account=pocket_account_id,
    created_time_ns=Time.time(datetime.now()),
)

# تحويل الأرصدة
ledger.transfer(100, pocket_account_id, "البنك") # الوقت الافتراضي هو الآن
# أو
transfer_report = ledger.transfer(
    100,
    from_account=pocket_account_id,
    to_account=ledger.create_account("الخزنة"),
    created_time_ns=Time.time(datetime.now()),
)
# أو
ledger.exchange("البنك (USD)", rate=3.75) #افترض أن العملة الحالية هي سعر صرف ريال سعودي = 1
ledger.transfer(
    375,
    pocket_account_id,
    "البنك (USD)",
) # هذه المرة تم النظر في أسعار الصرف

# ملحوظة: يتم الاحتفاظ بعمر الأرصدة في جميع المعاملات أثناء النقل.

# تقدير الزكاة (إنشاء تقرير)
zakat_report = ledger.check(silver_gram_price=2.5)


# أداء الزكاة (تطبيق الزكاة)
# الخصم من نفس الحسابات إذا كانت الزكاة واجبة فرديا أو جماعيا
ledger.zakat(zakat_report) # --> True
# أو قم بتحصيل جميع الزكاة والخصم من الحسابات المحددة
parts = ledger.build_payment_parts(zakat_report.statistics.zakat_cut_balances)
# تعديل "الأجزاء" لتوزيع الزكاة على الحسابات المحددة
ledger.zakat(zakat_report, parts) # --> False
```

###### بنية بيانات قاعدة البيانات (vault):

نظام ملفات تخزين البيانات الرئيسي على القرص هو تنسيق [`JSON5`](https://json5.org)، ولكنه يظهر هنا بتنسيق JSON للبيانات التي تم إنشاؤها بواسطة المثال أعلاه (ملاحظة: ستختلف الأوقات إذا قمت بإعادة تطبيقها بنفسك):

```JSON
{
  "account": {
    "1": {
      "balance": 950000,
      "created": 63878879829929860000,
      "name": "",
      "box": {
        "63878879829929861120": {
          "capital": 1000000,
          "count": 0,
          "last": 0,
          "rest": 950000,
          "total": 0
        }
      },
      "count": 2,
      "log": {
        "63878879829929861120": {
          "value": 1000000,
          "desc": "ايداع مبدئي",
          "ref": null,
          "file": {}
        },
        "63878879829930860544": {
          "value": -50000,
          "desc": "Plummer maintenance expense",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878879829930221568": {
      "balance": 892500,
      "created": 63878879829930260000,
      "name": "الجيب",
      "box": {
        "63878879829930352640": {
          "capital": 1000000,
          "count": 0,
          "last": 0,
          "rest": 892500,
          "total": 0
        }
      },
      "count": 5,
      "log": {
        "63878879829930352640": {
          "value": 1000000,
          "desc": "ايداع مبدئي",
          "ref": null,
          "file": {}
        },
        "63878879829931016192": {
          "value": -50000,
          "desc": "اشتراك الانترنت الشهري",
          "ref": null,
          "file": {}
        },
        "63878879829931155456": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63878879829931491328": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63878879829931778048": {
          "value": -37500,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878879829930467328": {
      "balance": 975000,
      "created": 63878879829930490000,
      "name": "المخبئ",
      "box": {
        "63847343829930549248": {
          "capital": 1000000,
          "count": 1,
          "last": 63878879829932474000,
          "rest": 975000,
          "total": 25000
        }
      },
      "count": 2,
      "log": {
        "63847343829930549248": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63878879829932539904": {
          "value": -25000,
          "desc": "zakat-زكاة",
          "ref": 63847343829930550000,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "البنك": {
      "balance": 10000,
      "created": 63878879829930350000,
      "name": "",
      "box": {
        "63878879829930352640": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878879829930352640": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63878879829931409408": {
      "balance": 10000,
      "created": 63878879829931430000,
      "name": "الخزنة",
      "box": {
        "63878879829930352640": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878879829930352640": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "البنك (USD)": {
      "balance": 10000,
      "created": 63878879829930350000,
      "name": "",
      "box": {
        "63878879829930352640": {
          "capital": 10000,
          "count": 0,
          "last": 0,
          "rest": 10000,
          "total": 0
        }
      },
      "count": 1,
      "log": {
        "63878879829930352640": {
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
    "البنك (USD)": {
      "63878879829931687936": {
        "rate": 3.75,
        "description": null,
        "time": 63878879829931690000
      }
    }
  },
  "history": {
    "63878879829929943040": [
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
        "ref": 63878879829929860000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "1",
        "ref": 63878879829929860000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878879829930287104": [
      {
        "action": "CREATE",
        "account": "63878879829930221568",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878879829930377216": [
      {
        "action": "LOG",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878879829930516480": [
      {
        "action": "CREATE",
        "account": "63878879829930467328",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878879829930762240": [
      {
        "action": "LOG",
        "account": "63878879829930467328",
        "ref": 63847343829930550000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878879829930467328",
        "ref": 63847343829930550000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    ],
    "63878879829930885120": [
      {
        "action": "LOG",
        "account": "1",
        "ref": 63878879829930860000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "1",
        "ref": 63878879829929860000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    ],
    "63878879829931048960": [
      {
        "action": "LOG",
        "account": "63878879829930221568",
        "ref": 63878879829931020000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    ],
    "63878879829931180032": [
      {
        "action": "LOG",
        "account": "63878879829930221568",
        "ref": 63878879829931155000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "CREATE",
        "account": "البنك",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      {
        "action": "LOG",
        "account": "البنك",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "البنك",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878879829931450368": [
      {
        "action": "CREATE",
        "account": "63878879829931409408",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    ],
    "63878879829931507712": [
      {
        "action": "LOG",
        "account": "63878879829930221568",
        "ref": 63878879829931490000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "LOG",
        "account": "63878879829931409408",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "63878879829931409408",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878879829931720704": [
      {
        "action": "EXCHANGE",
        "account": "البنك (USD)",
        "ref": 63878879829931690000,
        "file": null,
        "key": null,
        "value": 3.75,
        "math": null
      }
    ],
    "63878879829931794432": [
      {
        "action": "LOG",
        "account": "63878879829930221568",
        "ref": 63878879829931780000,
        "file": null,
        "key": null,
        "value": -37500,
        "math": null
      },
      {
        "action": "SUBTRACT",
        "account": "63878879829930221568",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 37500,
        "math": null
      },
      {
        "action": "CREATE",
        "account": "البنك (USD)",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      {
        "action": "LOG",
        "account": "البنك (USD)",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      {
        "action": "TRACK",
        "account": "البنك (USD)",
        "ref": 63878879829930350000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    ],
    "63878879829932433408": [
      {
        "action": "REPORT",
        "account": null,
        "ref": 63878879829932450000,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      {
        "action": "ZAKAT",
        "account": "63878879829930467328",
        "ref": 63847343829930550000,
        "file": null,
        "key": "last",
        "value": 0,
        "math": "EQUAL"
      },
      {
        "action": "ZAKAT",
        "account": "63878879829930467328",
        "ref": 63847343829930550000,
        "file": null,
        "key": "total",
        "value": 25000,
        "math": "ADDITION"
      },
      {
        "action": "ZAKAT",
        "account": "63878879829930467328",
        "ref": 63847343829930550000,
        "file": null,
        "key": "count",
        "value": 1,
        "math": "ADDITION"
      },
      {
        "action": "LOG",
        "account": "63878879829930467328",
        "ref": 63878879829932540000,
        "file": null,
        "key": null,
        "value": -25000,
        "math": null
      }
    ]
  },
  "lock": null,
  "report": {
    "63878879829932449792": {
      "valid": true,
      "statistics": {
        "overall_wealth": 2900000,
        "zakatable_transactions_count": 0,
        "zakatable_transactions_balance": 1000000,
        "zakat_cut_balances": 25000
      },
      "plan": {
        "63878879829930467328": [
          {
            "box": {
              "capital": 1000000,
              "count": 1,
              "last": 63878879829932474000,
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
              "time": 63878879829932270000
            },
            "below_nisab": false,
            "total": 25000,
            "count": 1,
            "ref": 63847343829930550000
          }
        ]
      }
    }
  }
}
```

### الميزات الرئيسية:

- تتبع المعاملات: سجل بسهولة كل من الدخل والنفقات مع أوصاف مفصلة، مما يضمن سجلات مالية شاملة.

- حساب الزكاة التلقائي: احسب تلقائيًا الزكاة المستحقة بناءً على النصاب (الحد الأدنى) والحول (الدورات الزمنية) وسعر السوق الحالي للفضة، مما يبسط الامتثال للمبادئ المالية الإسلامية.

- الحول القابل للتخصيص: اضبط مدة الحول الخاصة بك بناءً على التقويم الذي تفضله لديك أو وضعك المالي الشخصي.

- حسابات متعددة: إدارة الزكاة لأصول أو حسابات مختلفة بشكل منفصل لمزيد من الوضوح المالي.

- الاستيراد/التصدير: استيراد بيانات المعاملات بسلاسة من ملفات CSV وتصدير تقارير الزكاة المحسوبة بتنسيق JSON لمزيد من التحليل أو حفظ السجلات.

- استمرارية البيانات: حفظ بيانات متتبع الزكاة الخاصة بك وتحميلها بأمان للاستخدام المستمر عبر الجلسات.

- تتبع السجل: تمكين سجل مفصل اختياري للإجراءات من أجل الشفافية والمراجعة (يمكن تعطيله اختياري).

### الفوائد:

- حساب الزكاة الدقيق: ضمان الحساب الدقيق لالتزامات الزكاة، وتعزيز المسؤولية المالية والرفاهية الروحية.

- إدارة مالية مبسطة: تبسيط إدارة أموالك من خلال تتبع المعاملات وحسابات الزكاة في مكان واحد.

- شفافية معززة: الحفاظ على سجل واضح لنشاطاتك المالية ومدفوعات الزكاة لمزيد من المساءلة وراحة البال.

- سهل الاستخدام: يمكنك التنقل بسهولة من خلال واجهة المكتبة ووظائفها سهلة الاستخدام، حتى من دون معرفة تقنية واسعة.

- قابل للتخصيص: يمكنك تخصيص إعدادات المكتبة (على سبيل المثال، قيمة النصاب ومدة الحول) وفقًا لاحتياجاتك وتفضيلاتك المحددة.

### من يمكنه الاستفادة:

- الأفراد: إدارة الشؤون المالية الشخصية بشكل فعال والوفاء بالتزامات الزكاة.

- المنظمات: تبسيط حساب الزكاة وتوزيعها على المشاريع والمبادرات الخيرية.

- المؤسسات المالية الإسلامية: دمج الزكاة (Zakat) في الأنظمة الحالية لتحسين الإدارة المالية وإعداد التقارير.

### الوثائق

- [آلية الزكاة: خوارزمية الغرف والصناديق](./docs/markdown/algorithm.ar.md)

- [صيغة الزكاة: تمثيل رياضي للصدقة الإسلامية](./docs/markdown/mathematics.ar.md)

- [كيفية عمل أسعار الصرف في نظام حساب الزكاة؟](./docs/markdown/exchange_rates.ar.md)

- [خوارزمية تتبع المخزون مع مراعاة الزكاة (مع الدورة القمرية)](./docs/markdown/inventory.ar.md) [**مخطط له**]

### المحتوى المرئي:

* [Mastering Zakat: The Rooms and Boxes Algorithm Explained!](https://www.youtube.com/watch?v=maxttQ5Xo5g)
* [طريقة الزكاة في العصر الرقمي: خوارزمية الغرف والصناديق](https://www.youtube.com/watch?v=kuhHzPjYD6o)
* [Zakat Algorithm in 42 seconds](https://www.youtube.com/watch?v=1ipCcqf48go)
* [How Exchange Rates Impact Zakat Calculation?](https://www.youtube.com/watch?v=PW6tjZgtShE)

استكشف الوثائق والبرمجة المصدرية والأمثلة لبدء تتبع الزكاة (Zakat) الخاصة بك وتحقيق راحة البال المالية وفقًا للمبادئ الإسلامية.
</div>