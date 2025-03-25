from fpdf import FPDF

# Create a PDF object
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Add content to the PDF
content = """
**Rules:**

1. Customer ID length  must be between 6 to 12 characters.

2. Transaction Amount must be a positive number. The range depends on the Account_Type:
   - If Account_Type is 'Savings', the amount must be between $100 and $1,500.
   - For other account types, the amount must be between $100 and $1,000,000.

3. Transaction_Date must be in YYYY-MM-DD format.

4. Field 'Capital_Adequacy_Ratio' must be above 8.

5. Field 'Account_Type' must be one of the following: Savings, Checking, or Loan.

6. Field 'Transaction_Type' must be one of the following: Deposit, Withdrawal, or Transfer.

7. Field Permanent Account Number must be a 10 characters.

8. Total amount for a customer must not exceed $1500.

"""

# Write the content to the PDF
pdf.multi_cell(0, 10, content)
pdf.output("regulatory_document_latest.pdf")