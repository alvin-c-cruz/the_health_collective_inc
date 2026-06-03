---
name: csv-analyzer
description: Analyze CSV files with sales receipts, patient data, and transaction details. Provides statistics, summaries, and insights from CSV data.
allowed-tools: Bash(python3 *)
---

# CSV Analyzer Skill

This skill analyzes CSV files containing sales/receipt data and provides comprehensive insights.

## Usage

When the user provides a CSV file path or asks to analyze CSV data, use this skill:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_csv.py "$1"
```

Where `$1` is the path to the CSV file.

## What This Skill Does

1. **Reads CSV files** with various formats (comma, tab, pipe-delimited)
2. **Provides basic statistics**: row count, column count, data types
3. **Summarizes numerical columns**: totals, averages, min/max values
4. **Identifies patterns**: most common values, payment methods, referrers
5. **Detects data quality issues**: missing values, duplicates, anomalies
6. **Generates insights**: daily totals, product analysis, discount patterns

## Expected CSV Structure

The skill is optimized for receipt/sales data with columns like:
- Date
- Receipt Number
- Patient/Customer Name
- Status
- Payment Method (MOP)
- Product/Service
- Prices, Discounts, Totals

But it can handle any CSV format and will adapt to the columns present.

## Output

The skill returns:
- Summary statistics
- Column-by-column analysis
- Key insights and patterns
- Data quality report
- Formatted tables for easy reading

## Examples

```
User: "Analyze this sales data: receipts.csv"
→ Runs analysis and provides comprehensive report

User: "What are the total sales in this file: daily_sales.csv"
→ Calculates totals and provides breakdown

User: "Check for any issues in patient_receipts.csv"
→ Runs data quality checks and reports problems
```
