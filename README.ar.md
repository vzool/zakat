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
ledger.track(
    10000, # المبلغ
    "Initial deposit", # الوصف
    account="المخبئ",
    created_time_ns=ZakatTracker.time(datetime.now() - relativedelta(years=1)),
)

# ملحوظة: إذا لم يكن هناك حساب موجود، فسيتم إنشاؤه تلقائيًا.

# خصم
ledger.sub(500, "Plummer maintenance expense") # الحساب الافتراضي هو 1
# or
ledger.sub(
    500, # المبلغ
    "اشتراك الانترنت الشهري",
    account="الجيب",
    created_time_ns=ZakatTracker.time(datetime.now()),
)

# تحويل الأرصدة
ledger.transfer(100, "الجيب", "البنك") # الوقت الافتراضي هو الآن
# أو
ledger.transfer(
    100,
    "الجيب", # from account
    "الخزنة", # to account
    created_time_ns=ZakatTracker.time(datetime.now()),
)
# أو
ledger.exchange("البنك (USD)", 3.75) # معدل الصرف
ledger.transfer(
    375,
    "الجيب",
    "البنك (USD)",
) # هذه المرة تم النظر في أسعار الصرف

# ملحوظة: يتم الاحتفاظ بعمر الأرصدة في جميع المعاملات أثناء النقل.

# تقدير الزكاة (إنشاء تقرير)
report = ledger.check(silver_gram_price=2.5)

valid, brief, plan = report # True, [2900000.0, 1000000.0, 25000.0], ...

# valid (bool): هل وصلت أي من المعاملات إلى حدي الإجارة والنصاب مجتمعين؟
# brief (list:3) = [a, b, c]

a, b, c = brief
# a: مجموع كل الأرصدة
# b: مجموع المعاملات التي تجب فيها الزكاة مجتمعة
# c: ملخص قطع الزكاة المستحق

# أداء الزكاة (تطبيق الزكاة)
# الخصم من نفس الحسابات إذا كانت الزكاة واجبة فرديا أو جماعيا
ledger.zakat(report)
# أو قم بتحصيل جميع الزكاة والخصم من الحسابات المحددةparts = ledger.build_payment_parts(c)
# تعديل "الأجزاء" لتوزيع الزكاة على الحسابات المحددة
ledger.zakat(report, parts) # --> False
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