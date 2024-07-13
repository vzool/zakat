### **Zakat-Aware Inventory Tracking Algorithm (with Lunar Cycle)**

1. **Initial Recording:**
   * **Quantity:** Record the number of items in each batch.
   * **Original Price:** Note the price you paid for each batch.
   * **Purchase Date (Hijri):** Record the date of purchase according to the Islamic lunar calendar (Hijri).

2. **Price Change Tracking:**
   * **Record Changes:** Update the "exchange rate" for each batch whenever the price changes.

3. **Zakat Calculation (End of Lunar Year):**
    * **For each batch:**
        * Determine if a full lunar year has passed since the purchase date. 
            * If yes:
                * Calculate the "Zakat value" using the current quantity and the latest exchange rate.
                * Include this batch in the total Zakat calculation.
            * If no:
                * Exclude this batch from the Zakat calculation for this year. Its Zakat will be due in the following year when it completes a full lunar cycle.
    * **Sum the "Zakat values" of all eligible batches to get your total inventory value.**
    * **Apply the 2.5% Zakat rate to the total value.**

**Explanation:**

* **Lunar Year Cycle:**  Zakat on inventory is due after the goods have been in your possession for a full lunar year. This algorithm tracks the purchase date in the Hijri calendar to ensure accurate timing.
* **Eligibility for Zakat:**  Only batches that have completed a full lunar year cycle are included in the Zakat calculation for that year.
* **Postponed Zakat:**  Batches that haven't yet completed a full lunar year are excluded from the current year's Zakat calculation. Their Zakat will be due in the following year.

**Example (with Lunar Cycle):**

* **Initial Recording:**
    * Batch 1: 100 scarves bought on 1st Muharram 1446H at $10 each.
    * Batch 2: 50 scarves bought on 15th Rajab 1446H at $15 each.
* **Price Change:** Later in the year, the price of scarves in Batch 2 increases to $20 each.
* **Zakat Calculation (End of 1446H):**
    * Batch 1: Full lunar year completed - include in Zakat calculation.
        * 100 scarves at $10 each = $1000 Zakat value
    * Batch 2:  Not yet a full lunar year - exclude from Zakat calculation.
* **Zakat Calculation (End of 1447H):**
    * Batch 1: Already included in last year's Zakat - exclude.
    * Batch 2: Full lunar year completed - include in Zakat calculation.
        * 50 scarves at $20 each = $1000 Zakat value

**Additional Tips:**

* **Hijri Calendar Tools:** Utilize online converters or apps to easily track dates in the Hijri calendar.
* **Clear Labeling:**  Clearly label each batch with its purchase date (Hijri) to facilitate easy tracking.

By incorporating the lunar year cycle, this algorithm ensures a more precise and religiously compliant calculation of Zakat on your inventory.
