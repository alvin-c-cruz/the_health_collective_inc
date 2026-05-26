# THE HEALTH COLLECTIVE INC. - FEATURE LIST

**System Overview:** Comprehensive accounting and operations management system for healthcare service business

**Last Updated:** 2026-05-26

---

## 1. DAILY OPERATIONS

### 1.1 Sales Transaction Management
**Purpose:** Record and manage all daily sales activities

**Core Features:**
- ✅ Create new sales transactions with customer, products, and payment details
- ✅ Support 5 transaction types: Walk-in patient, Home service, APE, Dialysis, Tele Consult
- ✅ Multiple payment methods (Cash, Check, Credit Card, etc.)
- ✅ Line item management with discounts
- ✅ Draft → Submit → Approve workflow
- ✅ View transaction details and history
- ✅ Edit and update transactions with change tracking
- ✅ Request and approve cancellations
- ✅ Comprehensive audit trail
- ✅ Date-based transaction browsing
- ✅ Draft transaction management
- ✅ All transactions view (6 categories)

**Key Routes:**
- `/daily_sales/` - Daily sales home
- `/daily_sales/transaction/new` - Create transaction
- `/daily_sales/transaction/<id>/edit` - Edit transaction
- `/daily_sales/transaction/<id>` - View transaction
- `/daily_sales/drafts` - View drafts
- `/daily_sales/all_transactions` - All transaction categories
- `/daily_sales/pending_approval` - Approval queue

### 1.2 Bank Deposit Management
**Purpose:** Record bank deposits and reconcile cash sales

**Core Features:**
- ✅ Create deposits linking cash transactions to bank accounts
- ✅ Record bank reference numbers and dates
- ✅ Handle bank charges and deductions
- ✅ Submit → Approve workflow
- ✅ Request changes to posted deposits
- ✅ Cancellation workflow
- ✅ Deposit audit history
- ✅ Deposit reports

**Key Routes:**
- `/daily_sales/deposit/new` - Record deposit
- `/daily_sales/deposit/view/<id>` - View deposit
- `/daily_sales/deposit/report` - Deposit report

### 1.3 Customer Collections
**Purpose:** Manage customer receivables and payment application

**Core Features:**
- ✅ View outstanding receivables by payment method
- ✅ Apply payments to specific transaction lines
- ✅ Handle collection deductions (bank charges, fees)
- ✅ Link collections to APE batches
- ✅ Submit → Approve workflow
- ✅ Request changes to posted collections
- ✅ Collection history tracking
- ✅ Cancellation workflow

**Key Routes:**
- `/collections/` - Collections dashboard
- `/collections/new` - Record collection
- `/collections/<id>` - View collection
- `/collections/history` - Collection history

### 1.4 Petty Cash Management
**Purpose:** Track small cash disbursements and reimbursements

**Core Features:**
- ✅ Create petty cash vouchers with payee and purpose
- ✅ Draft → Submit → Post workflow
- ✅ Payee master data management
- ✅ Petty cash dashboard with unreimbursed balance
- ✅ Create reimbursement reports (batch processing)
- ✅ Record reimbursements received
- ✅ Voucher history and audit trail
- ✅ Cancel and delete vouchers

**Key Routes:**
- `/daily_sales/petty_cash_management` - Dashboard
- `/daily_sales/petty_cash/voucher/new` - Create voucher
- `/daily_sales/petty_cash/reimbursement_report/create` - Batch reimbursement

### 1.5 Fund Management
**Purpose:** Track cash received from external sources and cash outflows

**Core Features:**
- ✅ Record fund received (cash inflows)
- ✅ Record fund disbursed (cash outflows)
- ✅ Submit → Approve workflow
- ✅ Cancellation request and approval workflow
- ✅ Pending cancellations queue

**Key Routes:**
- `/daily_sales/fund_received/new` - Record inflow
- `/daily_sales/fund_disbursed/new` - Record outflow

### 1.6 APE Batch Management
**Purpose:** Group employee health checkup transactions for billing

**Core Features:**
- ✅ Create APE batches by company and date
- ✅ Link transactions to batches
- ✅ Link collections to batches
- ✅ Generate Statement of Account (SOA)
- ✅ View batch details with totals and outstanding balance
- ✅ Batch API endpoint for integration

**Key Routes:**
- `/ape_batch/` - Batch list
- `/ape_batch/new` - Create batch
- `/ape_batch/<id>` - View batch
- `/ape_batch/<id>/soa` - Generate SOA

---

## 2. ACCOUNTING & BOOKS

### 2.1 Chart of Accounts
**Purpose:** Define and maintain the accounting account structure

**Core Features:**
- ✅ Create and manage general ledger accounts
- ✅ Account numbering system
- ✅ Account type and class classification
- ✅ Approval workflow for accounts
- ✅ Bulk import via CSV/Excel
- ✅ Export account list
- ✅ Auto-complete lookup for forms

**Key Routes:**
- `/account/` - Account list
- `/account/add` - Create account
- `/account_type/` - Manage account types
- `/account_class/` - Manage account classes

### 2.2 Books of Accounts (5 Core Journals)
**Purpose:** Record all accounting transactions in proper journals

**Journals:**
1. **Sales Journal (SJ)** - Revenue and sales entries
2. **Cash Receipt Journal (CR)** - Cash receipts and collections
3. **Accounts Payable Journal (APJ)** - Vendor invoices and obligations
4. **Disbursement Journal (DJ)** - Cash payments
5. **General Journal (GJ)** - Adjustments, transfers, other entries

**Common Features (All Journals):**
- ✅ Create journal entries with debit/credit details
- ✅ Link to customers/vendors
- ✅ Edit and modify entries
- ✅ View entry details
- ✅ Delete draft entries
- ✅ Cancel entries with reason
- ✅ Approval workflow
- ✅ Unlock posted entries (admin)
- ✅ Print journal entries
- ✅ Export to CSV/Excel
- ✅ Date range filtering

**Key Routes (per journal):**
- `/sales/` - Sales journal
- `/receipt/` - Receipt journal
- `/accounts_payable/` - AP journal
- `/disbursement/` - Disbursement journal
- `/general/` - General journal

### 2.3 Books of Accounts Extra (5 Additional Journals)
**Purpose:** Parallel journals with additional flexibility

Same features as core journals with extended customization

**Routes:**
- `/sales_extra/`
- `/receipt_extra/`
- `/accounts_payable_extra/`
- `/disbursement_extra/`
- `/general_extra/`

### 2.4 Financial Reports
**Purpose:** Generate key financial statements and reports

**Core Reports:**

#### Trial Balance
- ✅ View trial balance by date
- ✅ Shows debit/credit balances by account
- ✅ Verify double-entry bookkeeping
- ✅ Export to Excel

**Route:** `/trial_balance/`

#### Ledger
- ✅ Transaction-level detail for each account
- ✅ Running balance calculation
- ✅ Monthly/date range filtering
- ✅ Download individual ledgers

**Route:** `/ledger/`

#### Income Statement (P&L)
- ✅ Revenue and expense summary
- ✅ Net income calculation
- ✅ Period-based reporting
- ✅ Export to Excel

**Route:** `/income_statement/`

#### Balance Sheet
- ✅ Assets, liabilities, equity summary
- ✅ As-of-date reporting
- ✅ Export capabilities

**Route:** `/balance_sheet/`

---

## 3. MASTER DATA MANAGEMENT

### 3.1 Customer Management
**Purpose:** Maintain customer information

**Core Features:**
- ✅ Create and manage customer records
- ✅ Name, TIN, address, business style, birthday, sex
- ✅ Link to salesman
- ✅ Approval workflow
- ✅ Bulk import via CSV/Excel
- ✅ Auto-complete lookup
- ✅ Search and filter

**Route:** `/customer/`

### 3.2 Product Management
**Purpose:** Maintain products and services catalog

**Core Features:**
- ✅ Create and manage products
- ✅ Product type classification
- ✅ Approval workflow
- ✅ Bulk import
- ✅ Auto-complete lookup

**Routes:**
- `/product/` - Product list
- `/product_type/` - Product types

### 3.3 Vendor Management
**Purpose:** Maintain supplier information

**Core Features:**
- ✅ Create and manage vendors
- ✅ Vendor name, TIN
- ✅ Approval workflow
- ✅ Bulk import

**Route:** `/vendor/`

### 3.4 Company Management
**Purpose:** Manage multiple companies/divisions

**Core Features:**
- ✅ Create and manage company records
- ✅ Contact person, contact number, address, TIN
- ✅ Active/inactive flag
- ✅ Approval workflow

**Route:** `/company/`

### 3.5 Payment Method (Tender) Management
**Purpose:** Define payment methods and currencies

**Core Features:**
- ✅ Create and manage tenders
- ✅ Tender name, symbol
- ✅ Transaction type mapping
- ✅ Receivable flag for collections
- ✅ Reorder/sort tenders
- ✅ Bulk import

**Route:** `/tender/`

### 3.6 Bank Account Management
**Purpose:** Maintain list of bank accounts

**Core Features:**
- ✅ Create and manage bank accounts
- ✅ Bank name, account number, account name
- ✅ Quick-add functionality (popup)
- ✅ Active/inactive flag

**Route:** `/bank_account/`

### 3.7 Supporting Master Data
**Purpose:** Additional classification data

**Modules:**
- ✅ **Measure** - Units of measurement (`/measure/`)
- ✅ **Sex** - Gender classification (`/sex/`)
- ✅ **Payee** - Petty cash payees (`/payee/`)
- ✅ **Transaction Type** - Sales transaction categorization (`/transaction_type/`)

All support:
- Create, edit, delete
- Approval workflow
- Bulk import (where applicable)

---

## 4. USER MANAGEMENT & SECURITY

### 4.1 Authentication
**Purpose:** Control system access

**Core Features:**
- ✅ User registration with email and username
- ✅ Login with username/password
- ✅ Logout
- ✅ Password change (admin)
- ✅ Session management
- ✅ Inactive user handling

**Key Routes:**
- `/user/register` - Create account
- `/user/login` - Authenticate
- `/user/logout` - End session
- `/user/change_password` - Reset password

### 4.2 Authorization & Role Management
**Purpose:** Control what users can do

**Core Features:**
- ✅ Role-based access control (RBAC)
- ✅ Module-level permissions
- ✅ User flags: superuser, admin, staff, view-only, active
- ✅ Dynamic menu based on user roles
- ✅ Role assignment interface
- ✅ Protect core admin account
- ✅ Auto-assign all roles to superadmin

**Available Roles:**
- Daily Sales, Collections, Bank Account, APE Batch, Transaction Type
- Books of Accounts (Sales, Receipt, AP, Disbursement, General)
- Books of Accounts Extra (5 journals)
- Account, Account Type, Account Class
- Trial Balance, Ledger, Income Statement, Balance Sheet
- Customer, Product, Product Type, Vendor, Company, Tender, Measure, Sex, Payee

**Key Routes:**
- `/user/list` - User list
- `/user/user_group/<id>` - Assign roles
- `/user/user_management` - Role management dashboard
- `/user/toggle_*` - Toggle user flags

---

## 5. DASHBOARD & REPORTING

### 5.1 Dashboard
**Purpose:** Provide at-a-glance business overview

**Core Features:**
- ✅ Date-aware statistics
- ✅ Sales by transaction type (MTD and YTD)
- ✅ Product type summary (horizontal cards)
- ✅ Cash position analysis
- ✅ Quick access to key functions
- ✅ Transaction counts and amounts
- ✅ Date range selection

**Route:** `/` (home)

### 5.2 Operational Reports
**Purpose:** Support daily business operations

**Available Reports:**
- ✅ Daily Sales Report - Daily summary with cash on hand
- ✅ Sales Summary Report - Detailed sales metrics
- ✅ Accountabilities Report - Individual accountability tracking
- ✅ Deposit Report - Bank deposit status
- ✅ Collection History - Customer collection tracking
- ✅ APE Batch SOA - Statement of account for batches

---

## 6. SYSTEM FEATURES

### 6.1 Audit & Compliance
**Purpose:** Track all changes and maintain data integrity

**Core Features:**
- ✅ Comprehensive audit logging for all transactions
- ✅ Field-level change tracking (old value → new value)
- ✅ User attribution (who, when)
- ✅ Reason and notes for changes
- ✅ IP address tracking (optional)
- ✅ Audit history views per record
- ✅ Change request workflow with approval
- ✅ Cancellation workflow with reasons

**Models:**
- `AuditLog` - Complete change history
- `ChangeRequest` - Change approval workflow

### 6.2 Workflow Management
**Purpose:** Control data lifecycle and approvals

**Common Workflows:**
1. **Draft → Submit → Approve → Post**
   - Used in: Transactions, Deposits, Collections, Journals

2. **Request Change → Review → Approve/Reject**
   - Used in: Posted transactions, deposits, collections

3. **Request Cancellation → Approve/Reject**
   - Used in: All major transaction types

4. **Lock/Unlock**
   - Admin can unlock posted records for corrections

### 6.3 Data Import/Export
**Purpose:** Facilitate bulk data operations

**Core Features:**
- ✅ CSV/Excel bulk import for master data
- ✅ Import templates download
- ✅ Export reports to Excel
- ✅ Export account lists
- ✅ Export journal entries
- ✅ Download templates for data import

### 6.4 Search & Auto-complete
**Purpose:** Improve user experience with quick lookups

**Core Features:**
- ✅ Customer search with auto-complete
- ✅ Account lookup with auto-complete
- ✅ Product search with auto-complete
- ✅ AJAX-powered search endpoints
- ✅ Filter and sort capabilities

### 6.5 Design System
**Purpose:** Consistent UI/UX across application

**Core Features:**
- ✅ Design system tokens for colors, spacing, typography
- ✅ Consistent component library
- ✅ Responsive layouts
- ✅ Bootstrap 5 integration
- ✅ Bootstrap Icons
- ✅ Custom fonts: Playfair Display (headings), Inter (body), DM Mono (numbers)

### 6.6 System Configuration
**Purpose:** Application settings and metadata

**Core Features:**
- ✅ Company name configuration
- ✅ Version display in UI
- ✅ Philippine timezone support
- ✅ Date picker with locale formatting
- ✅ Currency formatting (Philippine Peso)

---

## 7. INTEGRATION & DATA FLOW

### 7.1 Cross-Module Integrations

**Daily Sales ↔ Collections**
- Transaction tenders create receivables
- Collections apply against outstanding tenders
- Outstanding balance calculation

**Daily Sales ↔ Banks**
- Cash transactions link to deposits
- Deposits reconcile to bank accounts

**Daily Sales ↔ Accounting**
- Transactions post to Sales Journal
- Deposits post to Receipt Journal
- Funds post to General Journal
- Petty cash posts to General Journal

**Daily Sales ↔ APE Batches**
- Transactions link to APE batches
- Collections group by batch
- Batch SOA generation

**Collections ↔ Tenders**
- Only receivable tenders appear in collections
- Tender-based filtering

**Master Data Dependencies**
- Customer → Transactions, Journal entries
- Product → Transaction line items
- Vendor → AP and Disbursement journals
- Company → APE batches
- Account → All journal entries, reports

---

## 8. KEY STATISTICS

### Module Count
- **15** main functional modules
- **10** journal types (5 core + 5 extra)
- **4** financial reports
- **10** master data types
- **6** transaction categories

### Transaction Types
- **Sales:** Walk-in patient, Home service, APE, Dialysis, Tele Consult
- **Deposits:** Bank deposit transactions
- **Collections:** Customer collections
- **Accountabilities:** Fund received and disbursed
- **Petty Cash Expenses:** Expense vouchers
- **Petty Cash Reimbursements:** Reimbursement reports

### Workflow States
- Draft, Submitted, Posted, Approved, Cancelled
- Pending (for change requests)
- For Reimbursement, Reimbursed (petty cash)

### User Roles
- **System:** superuser, admin, staff, view-only, active
- **Operations:** ~15 operational roles
- **Accounting:** ~20 accounting roles
- **Register:** ~10 master data roles

---

## 9. TECHNOLOGY STACK

### Backend
- **Flask 3.1.0** - Web framework
- **SQLAlchemy 2.0.36** - ORM
- **Flask-Migrate 4.1.0** - Database migrations
- **SQLite** - Database
- **Jinja2** - Templating engine

### Frontend
- **Bootstrap 5** - UI framework (local)
- **Bootstrap Icons** - Icon library
- **CSS Variables** - Design system tokens
- **Vanilla JavaScript** - Interactions
- **Tom Select** - Enhanced select dropdowns

### Typography
- **Playfair Display** - Headings
- **Inter** - Body text
- **DM Mono** - Numbers

---

## 10. FEATURE SUMMARY TABLE

| Feature Category | Count | Status |
|---|---|---|
| **Operations Modules** | 8 | ✅ Complete |
| **Accounting Modules** | 13 | ✅ Complete |
| **Master Data Types** | 10 | ✅ Complete |
| **Financial Reports** | 4 | ✅ Complete |
| **Journal Types** | 10 | ✅ Complete |
| **Transaction Categories** | 6 | ✅ Complete |
| **Workflow States** | 8 | ✅ Complete |
| **User Role Types** | 4 | ✅ Complete |
| **Import/Export Features** | 12+ | ✅ Complete |
| **Audit Features** | 5 | ✅ Complete |

---

## NOTES

- All major transactions have comprehensive audit trails
- All workflows support multi-step approval processes
- All master data supports bulk import/export
- All modules follow consistent design patterns
- All features use design system tokens for consistency
- System supports multiple user roles with granular permissions
- Complete integration between operations and accounting modules

---

**Document Version:** 1.0
**Last Updated:** 2026-05-26
**System Version:** thci (current)
