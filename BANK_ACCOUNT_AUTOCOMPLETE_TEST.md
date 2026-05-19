# Bank Account Autocomplete - Testing Guide

## What Was Implemented

The bank account search box in the deposit form now automatically updates with newly created bank accounts, matching the customer autocomplete functionality from the transaction form.

---

## Files Modified

### 1. **views.py** - Bank Account Views
**Location:** `application/blueprints/operations/bank_account/views.py`

**Changes:**
- Added `render_template_string` import
- Modified `add()` function to:
  - Detect `popup=1` query parameter
  - Send `postMessage` to parent window after saving
  - Auto-close popup window
  - Return popup parameter to template
- Modified `edit()` function to pass `popup=False` to template

### 2. **form.html** - Bank Account Form
**Location:** `application/blueprints/operations/bank_account/pages/bank_account/form.html`

**Changes:**
- Updated form action to preserve `popup=1` parameter in URL when submitting

### 3. **record_deposit.html** - Deposit Form
**Location:** `application/blueprints/operations/daily_sales/pages/daily_sales/record_deposit.html`

**Changes:**
- Added `.bank-ac-add` CSS class for styling
- Enhanced autocomplete to include "+ Add Bank Account" button at top
- Added `window.addEventListener('message', ...)` to receive postMessage
- Auto-updates options array and input value when new bank account is added

---

## How to Test

### Test Case 1: Basic Autocomplete Search
1. Navigate to: `http://192.168.8.116:9000/daily_sales/deposit/new`
2. Click on the "Bank / Account" input field
3. **Expected:** Dropdown should show existing bank accounts with a "+ Add Bank Account" button at the top

### Test Case 2: Search Filtering
1. In the "Bank / Account" field, type a partial bank name (e.g., "BDO")
2. **Expected:** Dropdown should filter to show only matching bank accounts with highlighted search terms in bold

### Test Case 3: Keyboard Navigation
1. Click the "Bank / Account" field
2. Press Arrow Down key multiple times
3. **Expected:** Selection should move through the list items
4. Press Enter on a selected item
5. **Expected:** Field should populate with the selected bank account

### Test Case 4: Add New Bank Account (Main Test)
**This tests the postMessage functionality (#7 and #8)**

1. Navigate to: `http://192.168.8.116:9000/daily_sales/deposit/new`
2. Click on "Bank / Account" field
3. Click "+ Add Bank Account" in the dropdown
4. **Expected:** Popup window opens showing the bank account form
5. Fill in the form:
   - Bank Name: "TEST BANK"
   - Account Name: "Test Account"
   - Account Number: "1234567890"
   - Leave "Active" checked
6. Click "Save"
7. **Expected Results:**
   - Popup window closes automatically
   - Main window's "Bank / Account" field now shows "TEST BANK — 1234567890"
   - Field is automatically populated with the new bank account

### Test Case 5: Verify New Bank Account in List
1. Clear the "Bank / Account" field
2. Click on it again to open the dropdown
3. **Expected:** The newly created "TEST BANK — 1234567890" should appear in the list

---

## Troubleshooting

### Issue: Popup doesn't close after saving
**Possible Causes:**
- Browser popup blocker is interfering
- JavaScript errors in console

**Debug Steps:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Look for "postMessage" being sent in Network tab

### Issue: Field doesn't populate with new bank account
**Possible Causes:**
- postMessage not being received
- JavaScript listener not attached

**Debug Steps:**
1. Open browser console (F12)
2. Add console.log in the message listener:
```javascript
window.addEventListener('message', function(e) {
  console.log('Received message:', e.data);  // Add this line
  if (e.data && e.data.type === 'bank_account_added') {
    // ... rest of code
  }
});
```
3. Check if message is being logged when popup closes

### Issue: "+ Add Bank Account" button doesn't appear
**Possible Causes:**
- Template not rendering correctly
- JavaScript not initializing

**Debug Steps:**
1. View page source and check if `initBankAccountAutocomplete()` function exists
2. Check if function is being called in DOMContentLoaded
3. Verify `BANK_ACCOUNT_OPTIONS` array is defined

---

## Code Flow Diagram

```
User clicks "Bank / Account" field
    ↓
Dropdown shows with "+ Add Bank Account" button
    ↓
User clicks "+ Add Bank Account"
    ↓
Popup opens: /bank_account/add?popup=1
    ↓
User fills form and clicks Save
    ↓
POST to /bank_account/add?popup=1
    ↓
Backend saves bank account
    ↓
Backend detects popup=1 parameter
    ↓
Backend returns HTML with postMessage script
    ↓
postMessage sent: {type: "bank_account_added", bank_account_name: "TEST BANK — 1234567890"}
    ↓
Parent window receives message
    ↓
JavaScript adds to BANK_ACCOUNT_OPTIONS array
    ↓
JavaScript sets input field value
    ↓
Popup window closes automatically
    ↓
User sees new bank account in field ✓
```

---

## Key Implementation Details

### 1. Popup Parameter Preservation
The `popup=1` parameter is preserved through the form submission by including it in the form's action URL:

```html
<form action="{{ url_for('bank_account.add', popup=1) if popup else url_for('bank_account.add') }}" method="post">
```

### 2. postMessage Format
The backend sends this exact format:
```javascript
{
  type: "bank_account_added",
  bank_account_name: "BANK NAME — ACCOUNT NUMBER"
}
```

### 3. Message Listener
The parent window listens for messages and updates the field:
```javascript
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'bank_account_added') {
    const bankAccountName = e.data.bank_account_name;
    BANK_ACCOUNT_OPTIONS.push(bankAccountName);
    const input = document.getElementById('bank-account-input');
    if (input) input.value = bankAccountName;
  }
});
```

---

## Expected Console Output (When Working Correctly)

When you add a new bank account, you should NOT see any errors in the console. If debugging is enabled, you might see:
- "postMessage sent" (from popup)
- "Message received" (from parent window)
- The new bank account name in the console

---

## Verification Checklist

- [ ] Popup opens when clicking "+ Add Bank Account"
- [ ] Form allows input of bank details
- [ ] Save button works in popup
- [ ] Popup closes automatically after save
- [ ] Parent window field populates with new bank account
- [ ] New bank account appears in dropdown list
- [ ] No JavaScript errors in console
- [ ] Regular add bank account (non-popup) still works

---

## If It Still Doesn't Work

### Check these specific things:

1. **Is the popup parameter being passed?**
   - Check the URL in the popup: should be `/bank_account/add?popup=1`

2. **Is the postMessage HTML being returned?**
   - Add a debug statement in views.py before the return
   - Check if the condition `if popup:` is being entered

3. **Is window.opener available?**
   - In the popup window console, type: `window.opener`
   - Should return the parent window object, not null

4. **Is the message listener attached?**
   - In parent window console, type: `getEventListeners(window)`
   - Should show 'message' event listener

5. **Check browser compatibility:**
   - postMessage is supported in all modern browsers
   - Popup blockers might interfere

---

## Success Indicators

✅ **The implementation is working when:**
1. Clicking "+ Add Bank Account" opens a popup window
2. Filling and saving the form closes the popup automatically
3. The parent window's "Bank / Account" field automatically fills with the new bank account name
4. The new bank account appears in the dropdown when you click the field again

❌ **The implementation is NOT working if:**
1. Popup doesn't open (check popup blocker)
2. Popup doesn't close after saving (check JavaScript console for errors)
3. Field doesn't populate (check postMessage is being sent/received)
4. New bank account doesn't appear in list (check array is being updated)
