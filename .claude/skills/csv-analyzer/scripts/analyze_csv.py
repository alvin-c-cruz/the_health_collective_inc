#!/usr/bin/env python3
"""
CSV Analyzer Script
Analyzes CSV files and provides comprehensive statistics and insights.
"""

import sys
import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
import re


def detect_delimiter(file_path, sample_size=5):
    """Auto-detect the CSV delimiter."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        sample = ''.join([f.readline() for _ in range(sample_size)])

    sniffer = csv.Sniffer()
    try:
        delimiter = sniffer.sniff(sample).delimiter
        return delimiter
    except:
        # Default to comma if detection fails
        return ','


def parse_number(value):
    """Try to parse a string as a number, handling currency and formatting."""
    if not value or value.strip() == '':
        return None

    # Remove currency symbols, commas, and spaces
    cleaned = re.sub(r'[$,\s]', '', str(value))

    try:
        # Try integer first
        if '.' not in cleaned:
            return int(cleaned)
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def is_date_column(values):
    """Check if column contains dates."""
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}-\d{1,2}-\d{4}',
    ]

    sample = [v for v in values[:20] if v]
    if not sample:
        return False

    matches = sum(1 for v in sample if any(re.match(p, str(v)) for p in date_patterns))
    return matches / len(sample) > 0.5


def analyze_csv(file_path):
    """Main analysis function."""

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    # Detect delimiter
    delimiter = detect_delimiter(file_path)

    # Read CSV
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        return {"error": "CSV file is empty"}

    headers = [h for h in rows[0].keys() if h]  # Filter out None/empty headers

    # Initialize analysis structures
    column_data = {col: [] for col in headers}
    column_stats = {}

    # Collect data by column
    for row in rows:
        for col in headers:
            column_data[col].append(row.get(col, ''))

    # Analyze each column
    for col, values in column_data.items():
        # Convert all values to strings to ensure hashability
        non_empty = [str(v).strip() for v in values if v and str(v).strip()]

        stats = {
            'total_values': len(values),
            'non_empty': len(non_empty),
            'empty': len(values) - len(non_empty),
            'unique': len(set(non_empty)),
        }

        # Try to parse as numbers
        numbers = [parse_number(v) for v in non_empty]
        numbers = [n for n in numbers if n is not None]

        if numbers and len(numbers) > len(non_empty) * 0.5:
            # Numeric column
            stats['type'] = 'numeric'
            stats['sum'] = sum(numbers)
            stats['average'] = sum(numbers) / len(numbers)
            stats['min'] = min(numbers)
            stats['max'] = max(numbers)
        elif is_date_column(non_empty):
            # Date column
            stats['type'] = 'date'
            stats['sample_values'] = non_empty[:3]
        else:
            # Text column
            stats['type'] = 'text'
            counter = Counter(non_empty)
            stats['most_common'] = counter.most_common(5)

        column_stats[col] = stats

    # Generate insights
    insights = generate_insights(rows, column_stats, headers)

    return {
        'file_name': os.path.basename(file_path),
        'total_rows': len(rows),
        'total_columns': len(headers),
        'columns': headers,
        'column_stats': column_stats,
        'insights': insights,
    }


def generate_insights(rows, column_stats, headers):
    """Generate business insights from the data."""
    insights = []

    # Find total/amount columns
    amount_cols = [col for col, stats in column_stats.items()
                   if stats.get('type') == 'numeric' and
                   any(keyword in col.lower() for keyword in ['total', 'amount', 'price'])]

    if amount_cols:
        for col in amount_cols:
            stats = column_stats[col]
            insights.append(f"💰 {col}: Total = {stats['sum']:,.2f}, Average = {stats['average']:,.2f}")

    # Find payment method columns
    payment_cols = [col for col in headers if col and any(keyword in col.lower()
                   for keyword in ['payment', 'mop', 'method'])]

    if payment_cols:
        for col in payment_cols:
            stats = column_stats[col]
            if stats.get('most_common'):
                insights.append(f"💳 Payment Methods: {', '.join(f'{v} ({c})' for v, c in stats['most_common'][:3])}")

    # Check for status column
    status_cols = [col for col in headers if col and 'status' in col.lower()]
    if status_cols:
        for col in status_cols:
            stats = column_stats[col]
            if stats.get('most_common'):
                insights.append(f"📊 Status: {', '.join(f'{v} ({c})' for v, c in stats['most_common'][:3])}")

    # Data quality insights
    high_empty_cols = [col for col, stats in column_stats.items()
                       if stats['empty'] > stats['total_values'] * 0.3]
    if high_empty_cols:
        insights.append(f"⚠️  Columns with many missing values: {', '.join(high_empty_cols)}")

    return insights


def format_output(result):
    """Format the analysis results for display."""
    if 'error' in result:
        return f"❌ Error: {result['error']}"

    output = []
    output.append("=" * 70)
    output.append(f"📄 CSV ANALYSIS: {result['file_name']}")
    output.append("=" * 70)
    output.append(f"\n📊 Summary:")
    output.append(f"   Total Rows: {result['total_rows']:,}")
    output.append(f"   Total Columns: {result['total_columns']}")
    output.append(f"\n📋 Columns: {', '.join(result['columns'])}")

    # Column details
    output.append(f"\n\n📈 Column Analysis:")
    output.append("-" * 70)

    for col, stats in result['column_stats'].items():
        output.append(f"\n🔹 {col}")
        output.append(f"   Type: {stats['type'].upper()}")
        output.append(f"   Values: {stats['non_empty']:,} (Empty: {stats['empty']})")
        output.append(f"   Unique: {stats['unique']}")

        if stats['type'] == 'numeric':
            output.append(f"   Sum: {stats['sum']:,.2f}")
            output.append(f"   Average: {stats['average']:,.2f}")
            output.append(f"   Range: {stats['min']:,.2f} to {stats['max']:,.2f}")
        elif stats.get('most_common'):
            top_values = ', '.join(f"{v} ({c})" for v, c in stats['most_common'][:3])
            output.append(f"   Most Common: {top_values}")

    # Insights
    if result['insights']:
        output.append(f"\n\n💡 Key Insights:")
        output.append("-" * 70)
        for insight in result['insights']:
            output.append(f"   {insight}")

    output.append("\n" + "=" * 70)

    return '\n'.join(output)


if __name__ == '__main__':
    import io

    # Set UTF-8 encoding for stdout on Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python3 analyze_csv.py <csv_file_path>")
        sys.exit(1)

    csv_file = sys.argv[1]
    result = analyze_csv(csv_file)
    print(format_output(result))
