"""
Master cleanup script - Clear all test data from database

This script runs all individual cleanup scripts in the correct order
to prepare the database for fresh testing data.

Usage:
    python clear_all_test_data.py

What gets cleared:
    - All daily sales transactions and related data
    - All collections data
    - All deposits and fund management data
    - All petty cash vouchers and reimbursements
    - All test customers/patients and products
    - All test companies, APE batches, and bank accounts

What gets preserved:
    - User accounts (admin, staff)
    - Master data (tenders, transaction types, fund categories)
    - Reference data (sex, account master data)
"""
import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """Run a cleanup script and report results"""
    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print(f"{'='*70}")

    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"ERROR in {script_name}:")
        print(result.stderr)
        return False

    return True

def main():
    """Run all cleanup scripts in the correct order"""

    print("\n" + "="*70)
    print("DATABASE CLEANUP - PREPARING FOR TESTING")
    print("="*70)
    print("\nThis will delete ALL test data from the database.")
    print("User accounts and master data will be preserved.")

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\nCleanup cancelled.")
        return

    # List of cleanup scripts in order
    scripts = [
        'clear_daily_sales_data.py',      # Transactions, deposits, funds, petty cash
        'clear_collections_data.py',       # Collections and collection details
        'clear_additional_data.py',        # Companies, APE batches, bank accounts
        'clear_patients_products.py',      # Customers, products, product types
    ]

    success_count = 0
    failed_scripts = []

    for script in scripts:
        if Path(script).exists():
            if run_script(script):
                success_count += 1
            else:
                failed_scripts.append(script)
        else:
            print(f"\nWARNING: Script not found: {script}")
            failed_scripts.append(script)

    # Summary
    print("\n" + "="*70)
    print("CLEANUP SUMMARY")
    print("="*70)
    print(f"Scripts run successfully: {success_count}/{len(scripts)}")

    if failed_scripts:
        print(f"\nFailed or missing scripts:")
        for script in failed_scripts:
            print(f"  - {script}")
        print("\nPlease review the errors above and try again.")
    else:
        print("\n[OK] All cleanup scripts completed successfully!")
        print("\nDatabase is now clean and ready for fresh test data.")
        print("\nNext steps:")
        print("  1. Create test customers/patients")
        print("  2. Create test products and product types")
        print("  3. Create test transactions")
        print("  4. Test the complete workflow")

if __name__ == "__main__":
    main()
