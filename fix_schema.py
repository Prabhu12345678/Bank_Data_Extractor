import re

with open('src/extraction/schema.py', 'r') as f:
    content = f.read()

# I will insert total_tax_amount right after total_amount
old_line = 'total_amount: Optional[float] = Field(None, description="Total amount due or closing balance.")'
new_line = '''total_amount: Optional[float] = Field(None, description="Total amount due or closing balance.")
    total_tax_amount: Optional[float] = Field(0.0, description="Total tax amount applied to the invoice, if present.")'''

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('src/extraction/schema.py', 'w') as f:
        f.write(content)
    print("Schema updated successfully.")
else:
    print("Failed to find line.")
