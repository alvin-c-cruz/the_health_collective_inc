"""
Create Excel testing checklist for Daily Sales
"""
import pandas as pd
from datetime import datetime

# Testing checklist data
test_cases = {
    'Category': [],
    'Test Case ID': [],
    'Test Case Description': [],
    'Steps to Test': [],
    'Expected Result': [],
    'Status': [],
    'Tested By': [],
    'Date Tested': [],
    'Notes': []
}

# 1. Basic Transaction Flow
category = "1. Basic Transaction Flow"
tests = [
    {
        'id': 'TC-001',
        'desc': 'Create new transaction (draft)',
        'steps': '1. Navigate to Daily Sales\n2. Click "New Transaction"\n3. Fill in patient, date, record number\n4. Click "Save Draft"',
        'expected': 'Transaction saved as draft, shows in draft list with "Draft" badge'
    },
    {
        'id': 'TC-002',
        'desc': 'Add products to transaction',
        'steps': '1. Open transaction\n2. Select product from dropdown\n3. Enter amount\n4. Click "Save Draft"',
        'expected': 'Product appears in transaction details, total calculates correctly'
    },
    {
        'id': 'TC-003',
        'desc': 'Add multiple products',
        'steps': '1. Add product 1 with amount\n2. Add product 2 with amount\n3. Save draft',
        'expected': 'All products saved, totals sum correctly'
    },
    {
        'id': 'TC-004',
        'desc': 'Add payment methods (tenders)',
        'steps': '1. Select tender (Cash/Credit/etc)\n2. Enter amount\n3. Save draft',
        'expected': 'Payment method saved, balance calculated (total - payment)'
    },
    {
        'id': 'TC-005',
        'desc': 'Add line-level discount',
        'steps': '1. Add product\n2. Enter discount amount\n3. Save',
        'expected': 'Discount applied to product line, net amount = amount - discount'
    },
    {
        'id': 'TC-006',
        'desc': 'Add transaction-level discount',
        'steps': '1. Add products\n2. Enter transaction discount\n3. Save',
        'expected': 'Discount applied to total, final total reduced'
    },
    {
        'id': 'TC-007',
        'desc': 'Edit draft transaction',
        'steps': '1. Open draft transaction\n2. Modify fields\n3. Save',
        'expected': 'Changes saved, audit log shows update'
    },
    {
        'id': 'TC-008',
        'desc': 'Delete draft transaction',
        'steps': '1. Open draft\n2. Click Delete\n3. Confirm',
        'expected': 'Transaction removed from list'
    },
    {
        'id': 'TC-009',
        'desc': 'Submit transaction for approval',
        'steps': '1. Open draft\n2. Click "Save & Submit"\n3. Confirm',
        'expected': 'Status changes to "Submitted", shows submitted date, appears in pending approvals'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 2. Approval Workflow
category = "2. Approval Workflow"
tests = [
    {
        'id': 'TC-101',
        'desc': 'View pending approvals (Admin)',
        'steps': '1. Login as Admin\n2. Navigate to Pending Approvals',
        'expected': 'All submitted transactions appear in list'
    },
    {
        'id': 'TC-102',
        'desc': 'Approve transaction',
        'steps': '1. View pending transaction\n2. Click "Approve"\n3. Confirm',
        'expected': 'Status changes to "Approved", badge shows green, removed from pending list, audit log updated'
    },
    {
        'id': 'TC-103',
        'desc': 'Disapprove transaction (return to draft)',
        'steps': '1. View submitted transaction\n2. Click "Return to Draft"\n3. Enter reason\n4. Submit',
        'expected': 'Status returns to "Draft", reason recorded in description, audit log shows return with reason'
    },
    {
        'id': 'TC-104',
        'desc': 'Staff sees disapproval reason',
        'steps': '1. Login as staff\n2. Open returned transaction\n3. Check description',
        'expected': 'Description shows disapproval reason with timestamp and admin name'
    },
    {
        'id': 'TC-105',
        'desc': 'Unapprove transaction (Superuser only)',
        'steps': '1. Login as Superuser\n2. Open approved transaction\n3. Click "Unapprove"',
        'expected': 'Transaction returned to submitted status, approval removed'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 3. Cancellation Workflow
category = "3. Cancellation Workflow"
tests = [
    {
        'id': 'TC-201',
        'desc': 'Request cancellation (Staff)',
        'steps': '1. Login as Staff\n2. View submitted transaction\n3. Click "Request Cancellation"\n4. Enter reason\n5. Submit',
        'expected': 'Badge shows "Cancellation Requested", reason saved, admin notified'
    },
    {
        'id': 'TC-202',
        'desc': 'Approve cancellation request (Admin)',
        'steps': '1. Login as Admin\n2. View transaction with cancellation request\n3. Read reason\n4. Click "Approve Cancellation"',
        'expected': 'Transaction status changes to "Cancelled", cancellation date recorded, audit log updated'
    },
    {
        'id': 'TC-203',
        'desc': 'Reject cancellation request (Admin)',
        'steps': '1. View transaction with cancellation request\n2. Click "Reject Cancellation"',
        'expected': 'Cancellation request cleared, transaction remains submitted, audit log shows rejection'
    },
    {
        'id': 'TC-204',
        'desc': 'Cannot edit cancelled transaction',
        'steps': '1. Open cancelled transaction\n2. Check available actions',
        'expected': 'Edit button not available, transaction is read-only'
    },
    {
        'id': 'TC-205',
        'desc': 'Un-cancel transaction (draft only)',
        'steps': '1. Cancel draft transaction\n2. Click "Un-cancel"',
        'expected': 'Transaction returns to draft status, can be edited'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 4. Audit Trail
category = "4. Audit Trail & History"
tests = [
    {
        'id': 'TC-301',
        'desc': 'View audit history',
        'steps': '1. Open any transaction\n2. Click "View History" button',
        'expected': 'Audit history page opens showing timeline of all changes'
    },
    {
        'id': 'TC-302',
        'desc': 'Verify creation logged',
        'steps': '1. Create new transaction\n2. View history',
        'expected': 'Shows "created" action with user and timestamp'
    },
    {
        'id': 'TC-303',
        'desc': 'Verify update logged',
        'steps': '1. Edit transaction\n2. Change fields\n3. Save\n4. View history',
        'expected': 'Shows "updated" action with changed fields (old → new values)'
    },
    {
        'id': 'TC-304',
        'desc': 'Verify submit logged',
        'steps': '1. Submit transaction\n2. View history',
        'expected': 'Shows "submitted" action with user and timestamp'
    },
    {
        'id': 'TC-305',
        'desc': 'Verify approval logged',
        'steps': '1. Approve transaction\n2. View history',
        'expected': 'Shows "approved" action with admin user and timestamp'
    },
    {
        'id': 'TC-306',
        'desc': 'Verify return to draft logged',
        'steps': '1. Return transaction to draft\n2. View history',
        'expected': 'Shows "returned_to_draft" action with reason'
    },
    {
        'id': 'TC-307',
        'desc': 'Verify cancellation request logged',
        'steps': '1. Request cancellation\n2. View history',
        'expected': 'Shows "cancellation_requested" action with reason'
    },
    {
        'id': 'TC-308',
        'desc': 'Verify cancellation approval logged',
        'steps': '1. Approve cancellation\n2. View history',
        'expected': 'Shows "cancellation_approved" action'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 5. Patient Management
category = "5. Patient Management"
tests = [
    {
        'id': 'TC-401',
        'desc': 'Add new patient via popup',
        'steps': '1. In transaction form\n2. Click "Add New" next to Patient\n3. Fill Last Name, First Name, Middle Name\n4. Click Save',
        'expected': 'Patient added to system, appears in dropdown as "Last Name, First Name Middle Name"'
    },
    {
        'id': 'TC-402',
        'desc': 'Search patient by name',
        'steps': '1. In Patient dropdown\n2. Type patient name\n3. Check results',
        'expected': 'Autocomplete shows matching patients, searches across all name fields'
    },
    {
        'id': 'TC-403',
        'desc': 'Patient name displays correctly',
        'steps': '1. Select patient\n2. Save transaction\n3. View in list',
        'expected': 'Patient name shows as "Last Name, First Name Middle Name" format'
    },
    {
        'id': 'TC-404',
        'desc': 'Add patient with sex',
        'steps': '1. Add new patient\n2. Select sex from dropdown\n3. Save',
        'expected': 'Sex saved and displays correctly'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 6. Navigation & UI
category = "6. Navigation & UI"
tests = [
    {
        'id': 'TC-501',
        'desc': 'Return URL from Daily Sales',
        'steps': '1. Navigate to transaction from Daily Sales\n2. Click Cancel or Save\n3. Check redirect',
        'expected': 'Returns to Daily Sales page'
    },
    {
        'id': 'TC-502',
        'desc': 'Return URL from Drafts',
        'steps': '1. Navigate to transaction from Drafts page\n2. Click Cancel or Save\n3. Check redirect',
        'expected': 'Returns to Drafts page'
    },
    {
        'id': 'TC-503',
        'desc': 'View drafts page',
        'steps': '1. Click "Drafts" from dashboard or daily sales',
        'expected': 'Shows all draft transactions regardless of date'
    },
    {
        'id': 'TC-504',
        'desc': 'Filter by date',
        'steps': '1. On Daily Sales page\n2. Select different date\n3. Check results',
        'expected': 'Shows transactions for selected date plus all drafts'
    },
    {
        'id': 'TC-505',
        'desc': 'Status badges display correctly',
        'steps': '1. View transactions in different statuses\n2. Check badge colors',
        'expected': 'Draft=yellow, Submitted=blue, Approved=green, Cancelled=red, Cancellation Requested=orange'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# 7. Edge Cases & Validation
category = "7. Edge Cases & Validation"
tests = [
    {
        'id': 'TC-601',
        'desc': 'Cannot submit empty transaction',
        'steps': '1. Create new transaction\n2. Leave all fields empty\n3. Click Submit',
        'expected': 'Validation error, transaction not submitted'
    },
    {
        'id': 'TC-602',
        'desc': 'Cannot have negative amounts',
        'steps': '1. Enter negative amount in product line\n2. Save',
        'expected': 'Validation error or amount converted to positive'
    },
    {
        'id': 'TC-603',
        'desc': 'Discount cannot exceed amount',
        'steps': '1. Enter amount = 100\n2. Enter discount = 150\n3. Save',
        'expected': 'Validation error, discount cannot be greater than amount'
    },
    {
        'id': 'TC-604',
        'desc': 'Balance calculation correct',
        'steps': '1. Add products totaling 1000\n2. Add discount 100\n3. Add payment 500\n4. Check balance',
        'expected': 'Balance = (1000 - 100) - 500 = 400'
    },
    {
        'id': 'TC-605',
        'desc': 'Cannot edit submitted transaction (non-admin)',
        'steps': '1. Login as staff\n2. Open submitted transaction\n3. Check available actions',
        'expected': 'Edit button not available, can only request cancellation'
    },
    {
        'id': 'TC-606',
        'desc': 'Cannot delete submitted transaction',
        'steps': '1. Open submitted transaction\n2. Check for delete button',
        'expected': 'Delete button not available'
    },
]

for test in tests:
    test_cases['Category'].append(category)
    test_cases['Test Case ID'].append(test['id'])
    test_cases['Test Case Description'].append(test['desc'])
    test_cases['Steps to Test'].append(test['steps'])
    test_cases['Expected Result'].append(test['expected'])
    test_cases['Status'].append('Not Tested')
    test_cases['Tested By'].append('')
    test_cases['Date Tested'].append('')
    test_cases['Notes'].append('')

# Create DataFrame
df = pd.DataFrame(test_cases)

# Create Excel writer with formatting
filename = f'Daily_Sales_Testing_Checklist_{datetime.now().strftime("%Y%m%d")}.xlsx'
writer = pd.ExcelWriter(filename, engine='xlsxwriter')

# Write data
df.to_excel(writer, sheet_name='Test Cases', index=False)

# Get workbook and worksheet objects
workbook = writer.book
worksheet = writer.sheets['Test Cases']

# Define formats
header_format = workbook.add_format({
    'bold': True,
    'bg_color': '#1a6473',
    'font_color': 'white',
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True
})

category_format = workbook.add_format({
    'bold': True,
    'bg_color': '#e6f3f5',
    'border': 1,
    'text_wrap': True,
    'valign': 'top'
})

cell_format = workbook.add_format({
    'border': 1,
    'text_wrap': True,
    'valign': 'top'
})

status_format = workbook.add_format({
    'border': 1,
    'text_wrap': True,
    'valign': 'top',
    'align': 'center',
    'bg_color': '#fff8e1'
})

# Set column widths
worksheet.set_column('A:A', 30)  # Category
worksheet.set_column('B:B', 12)  # Test Case ID
worksheet.set_column('C:C', 35)  # Description
worksheet.set_column('D:D', 50)  # Steps
worksheet.set_column('E:E', 50)  # Expected Result
worksheet.set_column('F:F', 15)  # Status
worksheet.set_column('G:G', 20)  # Tested By
worksheet.set_column('H:H', 15)  # Date Tested
worksheet.set_column('I:I', 40)  # Notes

# Apply header format
for col_num, value in enumerate(df.columns.values):
    worksheet.write(0, col_num, value, header_format)

# Apply cell formats
for row_num in range(1, len(df) + 1):
    worksheet.write(row_num, 0, df.iloc[row_num-1]['Category'], category_format)
    worksheet.write(row_num, 1, df.iloc[row_num-1]['Test Case ID'], cell_format)
    worksheet.write(row_num, 2, df.iloc[row_num-1]['Test Case Description'], cell_format)
    worksheet.write(row_num, 3, df.iloc[row_num-1]['Steps to Test'], cell_format)
    worksheet.write(row_num, 4, df.iloc[row_num-1]['Expected Result'], cell_format)
    worksheet.write(row_num, 5, df.iloc[row_num-1]['Status'], status_format)
    worksheet.write(row_num, 6, df.iloc[row_num-1]['Tested By'], cell_format)
    worksheet.write(row_num, 7, df.iloc[row_num-1]['Date Tested'], cell_format)
    worksheet.write(row_num, 8, df.iloc[row_num-1]['Notes'], cell_format)

# Set row heights
worksheet.set_row(0, 30)  # Header row
for row_num in range(1, len(df) + 1):
    worksheet.set_row(row_num, 60)  # Data rows

# Add summary sheet
summary_data = {
    'Category': [
        '1. Basic Transaction Flow',
        '2. Approval Workflow',
        '3. Cancellation Workflow',
        '4. Audit Trail & History',
        '5. Patient Management',
        '6. Navigation & UI',
        '7. Edge Cases & Validation',
        'TOTAL'
    ],
    'Total Tests': [9, 5, 5, 8, 4, 5, 6, 42],
    'Passed': [0, 0, 0, 0, 0, 0, 0, 0],
    'Failed': [0, 0, 0, 0, 0, 0, 0, 0],
    'Not Tested': [9, 5, 5, 8, 4, 5, 6, 42],
    'Pass %': ['0%', '0%', '0%', '0%', '0%', '0%', '0%', '0%']
}

df_summary = pd.DataFrame(summary_data)
df_summary.to_excel(writer, sheet_name='Summary', index=False)

# Format summary sheet
summary_sheet = writer.sheets['Summary']
summary_sheet.set_column('A:A', 30)
summary_sheet.set_column('B:F', 15)

for col_num, value in enumerate(df_summary.columns.values):
    summary_sheet.write(0, col_num, value, header_format)

for row_num in range(1, len(df_summary) + 1):
    for col_num in range(len(df_summary.columns)):
        summary_sheet.write(row_num, col_num, df_summary.iloc[row_num-1, col_num], cell_format)

# Save
writer.close()

print(f"Testing checklist created: {filename}")
print()
print(f"Total test cases: {len(df)}")
print()
print("Categories:")
print(df.groupby('Category').size())
print()
print("Excel file ready for testing!")
