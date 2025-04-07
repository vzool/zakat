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
bank_account_id = ledger.create_account("البنك")
ledger.transfer(100, pocket_account_id, bank_account_id) #الوقت الافتراضي هو
# أو
transfer_report = ledger.transfer(
    100,
    from_account=pocket_account_id,
    to_account=ledger.create_account("الخزنة"),
    created_time_ns=Time.time(datetime.now()),
)
# أو
bank_usd_account_id = ledger.create_account("البنك (USD)")
ledger.exchange(bank_usd_account_id, rate=3.75) #افترض أن العملة الحالية هي سعر صرف ريال سعودي = 1
ledger.transfer(
    375,
    pocket_account_id,
    bank_usd_account_id,
) # هذه المرة تم النظر في أسعار الصرف

# ملحوظة: يتم الاحتفاظ بعمر الأرصدة في جميع المعاملات أثناء النقل.

# تقدير الزكاة (إنشاء تقرير)
zakat_report = ledger.check(silver_gram_price=2.5)


# أداء الزكاة (تطبيق الزكاة)
# الخصم من نفس الحسابات إذا كانت الزكاة واجبة فرديا أو جماعيا
ledger.zakat(zakat_report) # --> True
# أو قم بتحصيل جميع الزكاة والخصم من الحسابات المحددة
parts = ledger.build_payment_parts(zakat_report.summary.total_zakat_due)
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
      "created": 63879017249542580000,
      "name": "",
      "box": {
        "63879017249542578176": {
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
        "63879017249542578176": {
          "value": 1000000,
          "desc": "ايداع مبدئي",
          "ref": null,
          "file": {}
        },
        "63879017249544478720": {
          "value": -50000,
          "desc": "Plummer maintenance expense",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017249543176192": {
      "balance": 892500,
      "created": 63879017249543225000,
      "name": "الجيب",
      "box": {
        "63879017249543471104": {
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
        "63879017249543471104": {
          "value": 1000000,
          "desc": "ايداع مبدئي",
          "ref": null,
          "file": {}
        },
        "63879017249544757248": {
          "value": -50000,
          "desc": "اشتراك الانترنت الشهري",
          "ref": null,
          "file": {}
        },
        "63879017249545461760": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63879017249546223616": {
          "value": -10000,
          "desc": "",
          "ref": null,
          "file": {}
        },
        "63879017249547042816": {
          "value": -37500,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017249543749632": {
      "balance": 975000,
      "created": 63879017249543800000,
      "name": "المخبئ",
      "box": {
        "63847481249544003584": {
          "capital": 1000000,
          "rest": 975000,
          "zakat": {
            "count": 1,
            "last": 63879017249548120000,
            "total": 25000
          }
        }
      },
      "count": 2,
      "log": {
        "63847481249544003584": {
          "value": 1000000,
          "desc": "Initial deposit",
          "ref": null,
          "file": {}
        },
        "63879017249548304384": {
          "value": -25000,
          "desc": "zakat-زكاة",
          "ref": 63847481249544000000,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017249545216000": {
      "balance": 10000,
      "created": 63879017249545260000,
      "name": "البنك",
      "box": {
        "63879017249543471104": {
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
        "63879017249543471104": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017249546018816": {
      "balance": 10000,
      "created": 63879017249546060000,
      "name": "الخزنة",
      "box": {
        "63879017249543471104": {
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
        "63879017249543471104": {
          "value": 10000,
          "desc": "",
          "ref": null,
          "file": {}
        }
      },
      "hide": false,
      "zakatable": true
    },
    "63879017249546682368": {
      "balance": 10000,
      "created": 63879017249546730000,
      "name": "البنك (USD)",
      "box": {
        "63879017249543471104": {
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
        "63879017249543471104": {
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
    "63879017249546682368": {
      "63879017249546911744": {
        "rate": 3.75,
        "description": null,
        "time": 63879017249546910000
      }
    }
  },
  "history": {
    "63879017249542676480": {
      "63879017249542791168": {
        "action": "CREATE",
        "account": "1",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      "63879017249543020544": {
        "action": "LOG",
        "account": "1",
        "ref": 63879017249542580000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017249543110656": {
        "action": "TRACK",
        "account": "1",
        "ref": 63879017249542580000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017249543258112": {
      "63879017249543323648": {
        "action": "CREATE",
        "account": "63879017249543176192",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017249543397376": {
      "63879017249543438336": {
        "action": "NAME",
        "account": "63879017249543176192",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017249543512064": {
      "63879017249543643136": {
        "action": "LOG",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017249543700480": {
        "action": "TRACK",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017249543823360": {
      "63879017249543880704": {
        "action": "CREATE",
        "account": "63879017249543749632",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017249543929856": {
      "63879017249543970816": {
        "action": "NAME",
        "account": "63879017249543749632",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017249544265728": {
      "63879017249544380416": {
        "action": "LOG",
        "account": "63879017249543749632",
        "ref": 63847481249544000000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      },
      "63879017249544437760": {
        "action": "TRACK",
        "account": "63879017249543749632",
        "ref": 63847481249544000000,
        "file": null,
        "key": null,
        "value": 1000000,
        "math": null
      }
    },
    "63879017249544511488": {
      "63879017249544634368": {
        "action": "LOG",
        "account": "1",
        "ref": 63879017249544480000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      "63879017249544708096": {
        "action": "SUBTRACT",
        "account": "1",
        "ref": 63879017249542580000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    },
    "63879017249544806400": {
      "63879017249545060352": {
        "action": "LOG",
        "account": "63879017249543176192",
        "ref": 63879017249544760000,
        "file": null,
        "key": null,
        "value": -50000,
        "math": null
      },
      "63879017249545134080": {
        "action": "SUBTRACT",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 50000,
        "math": null
      }
    },
    "63879017249545281536": {
      "63879017249545330688": {
        "action": "CREATE",
        "account": "63879017249545216000",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017249545371648": {
      "63879017249545404416": {
        "action": "NAME",
        "account": "63879017249545216000",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017249545486336": {
      "63879017249545650176": {
        "action": "LOG",
        "account": "63879017249543176192",
        "ref": 63879017249545460000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      "63879017249545691136": {
        "action": "SUBTRACT",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017249545904128": {
        "action": "LOG",
        "account": "63879017249545216000",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017249545953280": {
        "action": "TRACK",
        "account": "63879017249545216000",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017249546084352": {
      "63879017249546133504": {
        "action": "CREATE",
        "account": "63879017249546018816",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017249546166272": {
      "63879017249546199040": {
        "action": "NAME",
        "account": "63879017249546018816",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017249546264576": {
      "63879017249546387456": {
        "action": "LOG",
        "account": "63879017249543176192",
        "ref": 63879017249546220000,
        "file": null,
        "key": null,
        "value": -10000,
        "math": null
      },
      "63879017249546428416": {
        "action": "SUBTRACT",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017249546584064": {
        "action": "LOG",
        "account": "63879017249546018816",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017249546633216": {
        "action": "TRACK",
        "account": "63879017249546018816",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017249546747904": {
      "63879017249546797056": {
        "action": "CREATE",
        "account": "63879017249546682368",
        "ref": null,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      }
    },
    "63879017249546829824": {
      "63879017249546870784": {
        "action": "NAME",
        "account": "63879017249546682368",
        "ref": null,
        "file": null,
        "key": null,
        "value": "",
        "math": null
      }
    },
    "63879017249546936320": {
      "63879017249546977280": {
        "action": "EXCHANGE",
        "account": "63879017249546682368",
        "ref": 63879017249546910000,
        "file": null,
        "key": null,
        "value": 3.75,
        "math": null
      }
    },
    "63879017249547067392": {
      "63879017249547190272": {
        "action": "LOG",
        "account": "63879017249543176192",
        "ref": 63879017249547040000,
        "file": null,
        "key": null,
        "value": -37500,
        "math": null
      },
      "63879017249547231232": {
        "action": "SUBTRACT",
        "account": "63879017249543176192",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 37500,
        "math": null
      },
      "63879017249547395072": {
        "action": "LOG",
        "account": "63879017249546682368",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      },
      "63879017249547436032": {
        "action": "TRACK",
        "account": "63879017249546682368",
        "ref": 63879017249543470000,
        "file": null,
        "key": null,
        "value": 10000,
        "math": null
      }
    },
    "63879017249548042240": {
      "63879017249548099584": {
        "action": "REPORT",
        "account": null,
        "ref": 63879017249548070000,
        "file": null,
        "key": null,
        "value": null,
        "math": null
      },
      "63879017249548189696": {
        "action": "ZAKAT",
        "account": "63879017249543749632",
        "ref": 63847481249544000000,
        "file": null,
        "key": "last",
        "value": 0,
        "math": "EQUAL"
      },
      "63879017249548230656": {
        "action": "ZAKAT",
        "account": "63879017249543749632",
        "ref": 63847481249544000000,
        "file": null,
        "key": "total",
        "value": 25000,
        "math": "ADDITION"
      },
      "63879017249548263424": {
        "action": "ZAKAT",
        "account": "63879017249543749632",
        "ref": 63847481249544000000,
        "file": null,
        "key": "count",
        "value": 1,
        "math": "ADDITION"
      },
      "63879017249548345344": {
        "action": "LOG",
        "account": "63879017249543749632",
        "ref": 63879017249548304000,
        "file": null,
        "key": null,
        "value": -25000,
        "math": null
      }
    }
  },
  "lock": null,
  "report": {
    "63879017249548066816": {
      "valid": true,
      "summary": {
        "total_wealth": 2900000,
        "num_wealth_items": 6,
        "num_zakatable_items": 1,
        "total_zakatable_amount": 1000000,
        "total_zakat_due": 25000
      },
      "plan": {
        "63879017249543749632": [
          {
            "box": {
              "capital": 1000000,
              "rest": 975000,
              "zakat": {
                "count": 1,
                "last": 63879017249548120000,
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
              "time": 63879017249547720000
            },
            "below_nisab": false,
            "total": 25000,
            "count": 1,
            "ref": 63847481249544000000
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