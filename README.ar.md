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
from zakat import ZakatTracker
from datetime import datetime
from dateutil.relativedelta import relativedelta

ledger = ZakatTracker(':memory:') # or './zakat_db'

# إضافة رصيد (تتبع عملية مالية)
ledger.track(10000, "ايداع مبدئي") # default account is 1
# أو
ledger.track(
    10000, # المبلغ
    "ايداع مبدئي",
    account="الجيب",
    created_time_ns=ZakatTracker.time(datetime.now()),
)
# أو معاملة بتاريخ قديم
box_ref = ledger.track(
    10000, # المبلغ
    "Initial deposit", # الوصف
    account="المخبئ",
    created_time_ns=ZakatTracker.time(datetime.now() - relativedelta(years=1)),
)

# ملحوظة: إذا لم يكن هناك حساب موجود، فسيتم إنشاؤه تلقائيًا.

# خصم
ledger.subtract(500, "Plummer maintenance expense") # الحساب الافتراضي هو 1
# or
subtract_report = ledger.subtract(
    500, # المبلغ
    "اشتراك الانترنت الشهري",
    account="الجيب",
    created_time_ns=ZakatTracker.time(datetime.now()),
)

# تحويل الأرصدة
ledger.transfer(100, "الجيب", "البنك") # الوقت الافتراضي هو الآن
# أو
transfer_report = ledger.transfer(
    100,
    "الجيب", # from account
    "الخزنة", # to account
    created_time_ns=ZakatTracker.time(datetime.now()),
)
# أو
ledger.exchange("البنك (USD)", rate=3.75) #افترض أن العملة الحالية هي سعر صرف ريال سعودي = 1
ledger.transfer(
    375,
    "الجيب",
    "البنك (USD)",
) # هذه المرة تم النظر في أسعار الصرف

# ملحوظة: يتم الاحتفاظ بعمر الأرصدة في جميع المعاملات أثناء النقل.

# تقدير الزكاة (إنشاء تقرير)
zakat_report = ledger.check(silver_gram_price=2.5)


# أداء الزكاة (تطبيق الزكاة)
# الخصم من نفس الحسابات إذا كانت الزكاة واجبة فرديا أو جماعيا
ledger.zakat(zakat_report) # --> True
# أو قم بتحصيل جميع الزكاة والخصم من الحسابات المحددة
parts = ledger.build_payment_parts(c)
# تعديل "الأجزاء" لتوزيع الزكاة على الحسابات المحددة
ledger.zakat(zakat_report, parts) # --> False
```

###### بنية بيانات قاعدة البيانات (vault):

نظام ملفات تخزين البيانات الرئيسي على القرص هو تنسيق [`camelX`](https://github.com/vzool/camelX)، ولكنه يظهر هنا بتنسيق JSON للبيانات التي تم إنشاؤها بواسطة المثال أعلاه (ملاحظة: ستختلف الأوقات إذا قمت بإعادة تطبيقها بنفسك):

```JSON
{
    "account": {
        "1": {
            "balance": 950000,
            "box": {
                "63877702571799379968": {
                    "capital": 1000000,
                    "count": 0,
                    "last": 0,
                    "rest": 950000,
                    "total": 0
                }
            },
            "count": 2,
            "log": {
                "63877702571799379968": {
                    "value": 1000000,
                    "desc": "\u0627\u064a\u062f\u0627\u0639 \u0645\u0628\u062f\u0626\u064a",
                    "ref": null,
                    "file": {}
                },
                "63877702571799691264": {
                    "value": -50000,
                    "desc": "Plummer maintenance expense",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877702571799379968
        },
        "\u0627\u0644\u062c\u064a\u0628": {
            "balance": 892500,
            "box": {
                "63877702571799511040": {
                    "capital": 1000000,
                    "count": 0,
                    "last": 0,
                    "rest": 892500,
                    "total": 0
                }
            },
            "count": 5,
            "log": {
                "63877702571799511040": {
                    "value": 1000000,
                    "desc": "\u0627\u064a\u062f\u0627\u0639 \u0645\u0628\u062f\u0626\u064a",
                    "ref": null,
                    "file": {}
                },
                "63877702571799756800": {
                    "value": -50000,
                    "desc": "\u0627\u0634\u062a\u0631\u0627\u0643 \u0627\u0644\u0627\u0646\u062a\u0631\u0646\u062a \u0627\u0644\u0634\u0647\u0631\u064a",
                    "ref": null,
                    "file": {}
                },
                "63877702571799805952": {
                    "value": -10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                },
                "63877702571799904256": {
                    "value": -10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                },
                "63877702571800043520": {
                    "value": -37500,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877702571799511040
        },
        "\u0627\u0644\u0645\u062e\u0628\u0626": {
            "balance": 975000.0,
            "box": {
                "63846166571799568384": {
                    "capital": 1000000,
                    "count": 1,
                    "last": 63877702571800305664,
                    "rest": 975000.0,
                    "total": 25000.0
                }
            },
            "count": 2,
            "log": {
                "63846166571799568384": {
                    "value": 1000000,
                    "desc": "Initial deposit",
                    "ref": null,
                    "file": {}
                },
                "63877702571800338432": {
                    "value": -25000.0,
                    "desc": "zakat-\u0632\u0643\u0627\u0629",
                    "ref": 63846166571799568384,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63846166571799568384
        },
        "\u0627\u0644\u0628\u0646\u0643": {
            "balance": 10000,
            "box": {
                "63877702571799511040": {
                    "capital": 10000,
                    "count": 0,
                    "last": 0,
                    "rest": 10000,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877702571799511040": {
                    "value": 10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877702571799511040
        },
        "\u0627\u0644\u062e\u0632\u0646\u0629": {
            "balance": 10000,
            "box": {
                "63877702571799511040": {
                    "capital": 10000,
                    "count": 0,
                    "last": 0,
                    "rest": 10000,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877702571799511040": {
                    "value": 10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877702571799511040
        },
        "\u0627\u0644\u0628\u0646\u0643 (USD)": {
            "balance": 10000,
            "box": {
                "63877702571799511040": {
                    "capital": 10000,
                    "count": 0,
                    "last": 0,
                    "rest": 10000,
                    "total": 0
                }
            },
            "count": 1,
            "log": {
                "63877702571799511040": {
                    "value": 10000,
                    "desc": "",
                    "ref": null,
                    "file": {}
                }
            },
            "hide": false,
            "zakatable": true,
            "created": 63877702571799511040
        }
    },
    "exchange": {
        "\u0627\u0644\u0628\u0646\u0643 (USD)": {
            "63877702571800002560": {
                "rate": 3.75,
                "description": null,
                "time": 63877702571800002560
            }
        }
    },
    "history": {
        "63877702571799412736": [
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
                "ref": 63877702571799379968,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": 1,
                "ref": 63877702571799379968,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877702571799519232": [
            {
                "action": "CREATE",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877702571799650304": [
            {
                "action": "CREATE",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63846166571799568384,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63846166571799568384,
                "file": null,
                "key": null,
                "value": 1000000,
                "math": null
            }
        ],
        "63877702571799699456": [
            {
                "action": "LOG",
                "account": 1,
                "ref": 63877702571799691264,
                "file": null,
                "key": null,
                "value": -50000,
                "math": null
            },
            {
                "action": "SUB",
                "account": 1,
                "ref": 63877702571799379968,
                "file": null,
                "key": null,
                "value": 50000,
                "math": null
            }
        ],
        "63877702571799764992": [
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799756800,
                "file": null,
                "key": null,
                "value": -50000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 50000,
                "math": null
            }
        ],
        "63877702571799822336": [
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799805952,
                "file": null,
                "key": null,
                "value": -10000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "\u0627\u0644\u0628\u0646\u0643",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u0628\u0646\u0643",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "\u0627\u0644\u0628\u0646\u0643",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            }
        ],
        "63877702571799912448": [
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799904256,
                "file": null,
                "key": null,
                "value": -10000,
                "math": null
            },
            {
                "action": "SUB",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "\u0627\u0644\u062e\u0632\u0646\u0629",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062e\u0632\u0646\u0629",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "\u0627\u0644\u062e\u0632\u0646\u0629",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            }
        ],
        "63877702571800010752": [
            {
                "action": "EXCHANGE",
                "account": "\u0627\u0644\u0628\u0646\u0643 (USD)",
                "ref": 63877702571800002560,
                "file": null,
                "key": null,
                "value": 3.75,
                "math": null
            }
        ],
        "63877702571800051712": [
            {
                "action": "LOG",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571800043520,
                "file": null,
                "key": null,
                "value": -37500,
                "math": null
            },
            {
                "action": "SUB",
                "account": "\u0627\u0644\u062c\u064a\u0628",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 37500,
                "math": null
            },
            {
                "action": "CREATE",
                "account": "\u0627\u0644\u0628\u0646\u0643 (USD)",
                "ref": null,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u0628\u0646\u0643 (USD)",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            },
            {
                "action": "TRACK",
                "account": "\u0627\u0644\u0628\u0646\u0643 (USD)",
                "ref": 63877702571799511040,
                "file": null,
                "key": null,
                "value": 10000,
                "math": null
            }
        ],
        "63877702571800281088": [
            {
                "action": "REPORT",
                "account": null,
                "ref": 63877702571800289280,
                "file": null,
                "key": null,
                "value": null,
                "math": null
            },
            {
                "action": "ZAKAT",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63846166571799568384,
                "file": null,
                "key": "last",
                "value": 0,
                "math": "EQUAL"
            },
            {
                "action": "ZAKAT",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63846166571799568384,
                "file": null,
                "key": "total",
                "value": 25000.0,
                "math": "ADDITION"
            },
            {
                "action": "ZAKAT",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63846166571799568384,
                "file": null,
                "key": "count",
                "value": 1,
                "math": "ADDITION"
            },
            {
                "action": "LOG",
                "account": "\u0627\u0644\u0645\u062e\u0628\u0626",
                "ref": 63877702571800338432,
                "file": null,
                "key": null,
                "value": -25000.0,
                "math": null
            }
        ]
    },
    "lock": null,
    "report": {
        "63877702571800289280": [
            true,
            [
                2900000.0,
                1000000.0,
                25000.0
            ],
            {
                "\u0627\u0644\u0645\u062e\u0628\u0626": {
                    "0": {
                        "total": 25000.0,
                        "count": 1,
                        "box_time": 63846166571799568384,
                        "box_capital": 1000000,
                        "box_rest": 1000000,
                        "box_last": 0,
                        "box_total": 0,
                        "box_count": 0,
                        "box_log": "Initial deposit",
                        "exchange_rate": 1,
                        "exchange_time": 63877702571800199168,
                        "exchange_desc": null
                    }
                }
            }
        ]
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