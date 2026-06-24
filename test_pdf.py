import pdfplumber
import sys
import os

path = r'D:\PDF novos\LINGUA_PORTUGUESA\AF\3_BIMESTRE\6_ANO\1644534.pdf'
if not os.path.exists(path):
    print(f"File not found: {path}")
    sys.exit(1)

try:
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text()
        print("--- FIRST PAGE ---")
        print(text)
except Exception as e:
    print(e)
