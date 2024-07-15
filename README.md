<h1 align="center">
<img src="https://raw.githubusercontent.com/vzool/zakat/main/images/logo.jpg" width="333">
</h1><br>

<div align="center" style="text-align: center;">

# ☪️ Zakat: A Python Library for Islamic Financial Management
** **We must pay Zakat if the remaining of every transaction reaches the Haul and Nisab limits** **
###### [PROJECT UNDER ACTIVE R&D]
<p>
<a href="https://github.com/vzool/zakat/blob/main/README.ar.md"><img src="https://img.shields.io/badge/lang-ar-green.svg" alt="ar" data-canonical-src="https://img.shields.io/badge/lang-en-green.svg" style="max-width: 100%;"></a>
</p>

</div>

Zakat is a user-friendly Python library designed to simplify the tracking and calculation of Zakat, a fundamental pillar of Islamic finance. Whether you're an individual or an organization, Zakat provides the tools to accurately manage your Zakat obligations.

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

- [Mechanism of Zakat: The Rooms and Boxes Algorithm](./docs/algorithm.md)

- [The Zakat Formula: A Mathematical Representation of Islamic Charity](./docs/mathematics.md)

- [How Exchange Rates Work in a Zakat Calculation System?](./docs/exchange_rates.md)

- [Zakat-Aware Inventory Tracking Algorithm (with Lunar Cycle)](./docs/inventory.md) [**PLANNED**]

### Get Started:

Install the Zakat library using pip:

```bash
pip install zakat
```

###### Testing

```shell
python -c "import zakat, sys; sys.exit(zakat.test())"
```

Explore the documentation, source code and examples to begin tracking your Zakat and achieving financial peace of mind in accordance with Islamic principles.
