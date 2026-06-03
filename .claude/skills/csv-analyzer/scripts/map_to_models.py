#!/usr/bin/env python3
"""
CSV to Models Mapper
Analyzes CSV and suggests how to map it to application models.
"""

import sys
import csv
import os
import re
from collections import Counter


def detect_delimiter(file_path, sample_size=5):
    """Auto-detect the CSV delimiter."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        sample = ''.join([f.readline() for _ in range(sample_size)])

    sniffer = csv.Sniffer()
    try:
        delimiter = sniffer.sniff(sample).delimiter
        return delimiter
    except:
        return ','


def analyze_csv_for_mapping(file_path):
    """Analyze CSV and generate model mapping suggestions."""

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    delimiter = detect_delimiter(file_path)

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)

    if not rows:
        return {"error": "CSV file is empty"}

    headers = [h for h in rows[0].keys() if h]

    # Analyze the data structure
    mapping = {
        'csv_file': os.path.basename(file_path),
        'total_rows': len(rows),
        'headers': headers,
        'sample_row': rows[0] if rows else {},
        'models_needed': [],
        'field_mappings': {},
        'import_plan': []
    }

    # Detect what type of data this is based on columns
    col_lower = [h.lower() if h else '' for h in headers]

    # Determine primary model
    if any('receipt' in c for c in col_lower):
        mapping['primary_model'] = 'Transaction (Daily Sales)'
        mapping['description'] = 'Sales/Receipt transactions with line items and payments'
    elif any('patient' in c for c in col_lower) or any('customer' in c for c in col_lower):
        mapping['primary_model'] = 'Transaction (Daily Sales)'
        mapping['description'] = 'Patient/Customer transactions'
    else:
        mapping['primary_model'] = 'Unknown - needs review'
        mapping['description'] = 'Unable to auto-detect model type'

    # Generate field mappings for Transaction model
    field_mappings = {}

    for header in headers:
        h_lower = header.lower()

        if 'date' in h_lower:
            field_mappings[header] = {
                'model': 'Transaction',
                'field': 'record_date',
                'notes': 'Transaction date',
                'transform': 'Convert to YYYY-MM-DD format'
            }
        elif 'receipt' in h_lower and ('n' in h_lower or 'num' in h_lower):
            field_mappings[header] = {
                'model': 'Transaction',
                'field': 'record_number',
                'notes': 'Receipt/transaction number',
                'transform': 'Store as string'
            }
        elif 'patient' in h_lower or 'customer' in h_lower:
            field_mappings[header] = {
                'model': 'Customer',
                'field': 'customer_name / first_name + last_name',
                'notes': 'Customer/Patient name',
                'transform': 'Parse into last_name, first_name, middle_name if possible'
            }
        elif 'status' in h_lower:
            field_mappings[header] = {
                'model': 'Transaction',
                'field': 'status',
                'notes': 'Transaction status',
                'transform': 'Map PAID -> "posted", others as needed'
            }
        elif any(term in h_lower for term in ['mop', 'payment', 'tender']):
            field_mappings[header] = {
                'model': 'TransactionTender',
                'field': 'tender_id',
                'notes': 'Payment method (Tender)',
                'transform': 'Look up Tender by name (CASH, E-WALLET, GCASH, etc.)'
            }
        elif 'product' in h_lower or 'service' in h_lower:
            field_mappings[header] = {
                'model': 'TransactionDetail',
                'field': 'product_id',
                'notes': 'Product/Service',
                'transform': 'Look up Product by name or create if not exists'
            }
        elif any(term in h_lower for term in ['item price', 'amount', 'price']):
            field_mappings[header] = {
                'model': 'TransactionDetail',
                'field': 'amount',
                'notes': 'Item price/amount',
                'transform': 'Convert to float'
            }
        elif 'discount' in h_lower:
            if 'total' not in h_lower:
                field_mappings[header] = {
                    'model': 'Transaction / TransactionDetail',
                    'field': 'discount',
                    'notes': 'Discount amount',
                    'transform': 'Store as positive float (negate if negative in CSV)'
                }
        elif any(term in h_lower for term in ['total', 'order total']):
            field_mappings[header] = {
                'model': 'Calculated',
                'field': 'N/A',
                'notes': 'Order total (calculated from line items)',
                'transform': 'Use for validation, not stored directly'
            }
        elif 'refer' in h_lower:
            field_mappings[header] = {
                'model': 'Transaction',
                'field': 'description',
                'notes': 'Referrer info',
                'transform': 'Store in description or custom field'
            }
        elif 'tag' in h_lower:
            field_mappings[header] = {
                'model': 'Transaction',
                'field': 'description',
                'notes': 'Tags/categories',
                'transform': 'Append to description or use custom field'
            }
        else:
            field_mappings[header] = {
                'model': 'Unknown',
                'field': 'N/A',
                'notes': 'Needs manual mapping',
                'transform': ''
            }

    mapping['field_mappings'] = field_mappings

    # Generate import plan
    import_plan = []

    import_plan.append({
        'step': 1,
        'action': 'Prepare lookup data',
        'details': [
            'Load all existing Customers from database',
            'Load all existing Products from database',
            'Load all Tenders (payment methods) from database',
            'Create dictionaries for quick lookup by name'
        ]
    })

    import_plan.append({
        'step': 2,
        'action': 'Process each CSV row',
        'details': [
            'For each row in CSV:',
            '  a) Find or create Customer',
            '  b) Create Transaction record',
            '  c) Create TransactionDetail for each product/item',
            '  d) Create TransactionTender for payment method',
            '  e) Set Transaction status based on CSV status'
        ]
    })

    import_plan.append({
        'step': 3,
        'action': 'Handle relationships',
        'details': [
            'Transaction.customer_id → Customer.id',
            'TransactionDetail.transaction_id → Transaction.id',
            'TransactionDetail.product_id → Product.id',
            'TransactionTender.transaction_id → Transaction.id',
            'TransactionTender.tender_id → Tender.id'
        ]
    })

    import_plan.append({
        'step': 4,
        'action': 'Validate and commit',
        'details': [
            'Verify all required fields are populated',
            'Check that totals match expected values',
            'Commit to database in batches',
            'Log any errors or skipped rows'
        ]
    })

    mapping['import_plan'] = import_plan

    # Models needed
    mapping['models_needed'] = [
        {
            'model': 'Customer',
            'purpose': 'Store patient/customer information',
            'fields_used': ['id', 'customer_name', 'first_name', 'last_name']
        },
        {
            'model': 'Transaction',
            'purpose': 'Main sales transaction record',
            'fields_used': ['id', 'record_date', 'record_number', 'customer_id', 'status', 'discount']
        },
        {
            'model': 'TransactionDetail',
            'purpose': 'Line items (products/services) in transaction',
            'fields_used': ['id', 'transaction_id', 'product_id', 'amount', 'discount']
        },
        {
            'model': 'TransactionTender',
            'purpose': 'Payment methods used',
            'fields_used': ['id', 'transaction_id', 'tender_id', 'amount']
        },
        {
            'model': 'Product',
            'purpose': 'Products/services catalog',
            'fields_used': ['id', 'product_name']
        },
        {
            'model': 'Tender',
            'purpose': 'Payment methods (CASH, E-WALLET, etc.)',
            'fields_used': ['id', 'tender_name']
        }
    ]

    return mapping


def format_mapping_output(mapping):
    """Format the mapping analysis for display."""
    if 'error' in mapping:
        return f"❌ Error: {mapping['error']}"

    output = []
    output.append("=" * 80)
    output.append(f"📋 CSV TO MODELS MAPPING PLAN")
    output.append("=" * 80)

    output.append(f"\n📄 CSV File: {mapping['csv_file']}")
    output.append(f"📊 Total Rows: {mapping['total_rows']:,}")
    output.append(f"\n🎯 Primary Model: {mapping['primary_model']}")
    output.append(f"📝 Description: {mapping['description']}")

    # Sample data
    output.append(f"\n\n📌 Sample CSV Row:")
    output.append("-" * 80)
    for key, value in list(mapping['sample_row'].items())[:8]:
        output.append(f"  {key}: {value}")
    if len(mapping['sample_row']) > 8:
        output.append(f"  ... and {len(mapping['sample_row']) - 8} more columns")

    # Field mappings
    output.append(f"\n\n🗺️  FIELD MAPPINGS:")
    output.append("=" * 80)

    for csv_col, map_info in mapping['field_mappings'].items():
        output.append(f"\n📍 CSV Column: {csv_col}")
        output.append(f"   → Model: {map_info['model']}")
        output.append(f"   → Field: {map_info['field']}")
        output.append(f"   → Notes: {map_info['notes']}")
        if map_info['transform']:
            output.append(f"   → Transform: {map_info['transform']}")

    # Models needed
    output.append(f"\n\n🏗️  MODELS REQUIRED:")
    output.append("=" * 80)

    for model_info in mapping['models_needed']:
        output.append(f"\n📦 {model_info['model']}")
        output.append(f"   Purpose: {model_info['purpose']}")
        output.append(f"   Fields: {', '.join(model_info['fields_used'])}")

    # Import plan
    output.append(f"\n\n📝 IMPORT PLAN:")
    output.append("=" * 80)

    for step in mapping['import_plan']:
        output.append(f"\n✅ Step {step['step']}: {step['action']}")
        for detail in step['details']:
            output.append(f"   {detail}")

    # Summary
    output.append(f"\n\n💡 SUMMARY:")
    output.append("=" * 80)
    output.append(f"This CSV contains {mapping['total_rows']} transactions that will be imported into:")
    output.append(f"  • {len(mapping['models_needed'])} different database models")
    output.append(f"  • Primary model: {mapping['primary_model']}")
    output.append(f"  • {len(mapping['field_mappings'])} CSV columns mapped to model fields")
    output.append(f"\nNext step: Review the mappings above and implement the import script.")

    output.append("\n" + "=" * 80)

    return '\n'.join(output)


if __name__ == '__main__':
    import io

    # Set UTF-8 encoding for stdout on Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python3 map_to_models.py <csv_file_path>")
        sys.exit(1)

    csv_file = sys.argv[1]
    mapping = analyze_csv_for_mapping(csv_file)
    print(format_mapping_output(mapping))
