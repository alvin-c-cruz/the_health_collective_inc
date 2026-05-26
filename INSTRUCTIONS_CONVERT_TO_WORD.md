# Instructions: Converting Proposals to Microsoft Word

## Files to Convert

1. `PROPOSAL_THEIDI_WORD.md` - Theidi Construction Corporation
2. `PROPOSAL_ZHIYUAN_WORD.md` - Zhiyuan Construction Corp.

These are simplified versions optimized for Microsoft Word conversion.

---

## Method 1: Direct Paste into Word (Easiest)

### Step-by-Step:

1. **Open the Markdown file**
   - Right-click on `PROPOSAL_THEIDI_WORD.md`
   - Open with Notepad or any text editor

2. **Select all content**
   - Press `Ctrl + A` to select all
   - Press `Ctrl + C` to copy

3. **Open Microsoft Word**
   - Create a new blank document

4. **Paste the content**
   - Press `Ctrl + V` to paste
   - Word will automatically format headings and lists

5. **Clean up formatting**
   - Adjust heading styles (Heading 1, Heading 2, etc.)
   - Format the table properly
   - Add page breaks where needed
   - Set margins and fonts as desired

6. **Fill in placeholders**
   - Replace `[INSERT YOUR EMAIL]` with your email
   - Replace `[INSERT YOUR PHONE]` with your phone number
   - Replace `[INSERT YOUR WEBSITE]` with your website
   - Replace `[INSERT PRICING HERE]` with actual pricing

7. **Save as Word document**
   - File → Save As
   - Choose "Word Document (*.docx)"
   - Name: `PROPOSAL_THEIDI_CONSTRUCTION.docx`

8. **Repeat for Zhiyuan**
   - Follow same steps for `PROPOSAL_ZHIYUAN_WORD.md`
   - Save as: `PROPOSAL_ZHIYUAN_CONSTRUCTION.docx`

---

## Method 2: Using Pandoc (Advanced)

If you have Pandoc installed:

```bash
# Convert Theidi proposal
pandoc PROPOSAL_THEIDI_WORD.md -o PROPOSAL_THEIDI_CONSTRUCTION.docx

# Convert Zhiyuan proposal
pandoc PROPOSAL_ZHIYUAN_WORD.md -o PROPOSAL_ZHIYUAN_CONSTRUCTION.docx
```

Then open in Word and fill in placeholders.

---

## Method 3: Online Converter

1. Go to: https://www.markdowntoword.com/
2. Upload `PROPOSAL_THEIDI_WORD.md`
3. Download the converted `.docx` file
4. Open in Word and fill in placeholders
5. Repeat for Zhiyuan proposal

---

## What to Fill In

### Contact Information Section:

```
**Email:** [INSERT YOUR EMAIL]
**Phone:** [INSERT YOUR PHONE]
**Website:** [INSERT YOUR WEBSITE]
```

Replace with:
```
**Email:** youremail@example.com
**Phone:** +63 XXX XXX XXXX
**Website:** www.yourcompany.com
```

### Pricing Section:

```
**[INSERT PRICING HERE]**
```

Replace with your actual pricing, for example:
```
**PHP 250,000** (One-time license fee)

or

**PHP 200,000** (Initial license)
Plus PHP 50,000 for installation and training
```

---

## Formatting Tips for Word

### Recommended Styles:

- **Title (First line):** Title style, 18pt, Bold
- **Section Headers (#):** Heading 1, 16pt, Bold
- **Subsection Headers (##):** Heading 2, 14pt, Bold
- **Sub-subsection (###):** Heading 3, 12pt, Bold
- **Body text:** Normal, 11pt
- **Bullets:** Use built-in bullet formatting
- **Table:** Apply Table Style "Grid Table 1 Light"

### Page Layout:

- **Margins:** 1 inch (2.54 cm) all sides
- **Font:** Calibri or Arial for body, Arial for headings
- **Line spacing:** 1.15 or 1.5
- **Page breaks:** Add before each major section

### Professional Touches:

1. **Add Header:**
   - Left: Company logo
   - Right: "Proposal for [Company Name]"

2. **Add Footer:**
   - Left: "The Health Collective Inc."
   - Center: Page number
   - Right: Date

3. **Cover Page:**
   - Add a professional cover page before the proposal
   - Include: Title, Client name, Your company name, Date

4. **Table of Contents:**
   - Insert after cover page
   - References → Table of Contents → Automatic

---

## Final Checklist

Before sending the proposal, verify:

- [ ] All placeholders filled in (email, phone, website, pricing)
- [ ] Company name correct throughout (Theidi or Zhiyuan)
- [ ] Date is current
- [ ] Contact information is accurate
- [ ] Pricing is finalized
- [ ] Formatting is consistent
- [ ] Table is properly formatted
- [ ] No typos or errors
- [ ] PDF version created (File → Save As → PDF)
- [ ] File named appropriately

---

## Recommended File Names

**For Theidi:**
- Word: `PROPOSAL_THEIDI_CONSTRUCTION_2026-05-26.docx`
- PDF: `PROPOSAL_THEIDI_CONSTRUCTION_2026-05-26.pdf`

**For Zhiyuan:**
- Word: `PROPOSAL_ZHIYUAN_CONSTRUCTION_2026-05-26.docx`
- PDF: `PROPOSAL_ZHIYUAN_CONSTRUCTION_2026-05-26.pdf`

---

## Sending the Proposal

### Email Subject:
```
Proposal: Construction Accounting Management System for [Company Name]
```

### Email Body (Template):
```
Dear [Contact Person],

Please find attached our proposal for the Construction Accounting Management
System for [Company Name].

This comprehensive solution includes:
- 5 essential accounting journals
- 4 financial reports
- Complete chart of accounts management
- Multi-user system with role-based access
- Comprehensive audit trails
- 4-week implementation timeline

We would be delighted to schedule a demonstration and discuss how our system
can transform your financial management processes.

Please feel free to contact us with any questions.

Best regards,
[Your Name]
[Your Title]
The Health Collective Inc.
[Your Phone]
[Your Email]
```

### Attachments:
1. Main proposal (PDF preferred)
2. MARKETING_CONSTRUCTION.md (as detailed feature list)

---

## Support

If you encounter any issues during conversion, the markdown files are designed to be:
- Clean and simple
- Easy to copy/paste
- Compatible with Word's auto-formatting
- Ready for manual cleanup

Good luck with your proposals!
