from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import io
import csv
import re
from bs4 import BeautifulSoup

class DataRow:
    def __init__(self, transaction_date, value_date, description, cheque, withdrawal, deposit, balance):
        self.transaction_date = transaction_date
        self.value_date = value_date
        self.description = description
        self.cheque = cheque
        self.withdrawal = withdrawal
        self.deposit = deposit
        self.balance = balance

def convert_pdf_to_html(pdf_path, html_path):
    """Creates a html that can be read by the code to get data, including column information."""

    output_html = io.BytesIO()
    with open(pdf_path, 'rb') as pdf_file:
        extract_text_to_fp(pdf_file, output_html, laparams=LAParams(), output_type='html')
    html_content = output_html.getvalue().decode('utf-8')

    with open(html_path, 'w') as html_file:
        html_file.write(html_content)

def convert_html_to_csv(html_path, csv_path):
    """Creates the CSV using information from the html file generated."""

    rows = []
    rows.append(DataRow('test transaction date','test value date','test description','test cheque','test withdrawal','test deposit','test balance'))
    rows.append(DataRow('test transaction date2','test value date2','test description2','test cheque2','test withdrawal2','test deposit2','test balance2'))


    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f,fieldnames=rows[0].__dict__.keys())
        rows = map(lambda x: x.__dict__, rows)
        writer.writeheader()
        writer.writerows(rows)

def get_data(option, html_path):

    """Get the data based on left padding, from observation"""
    match option:
        case 'transaction date':
            # 43-46
            return find_data(43)
        case 'value date':
            # 91-96
            return find_data(96)
        case 'description':
            return find_data(136)
        case 'cheque':
            # don't have this case in the documents currently
            return ''
        case 'withdrawal':
            # 323-326
            if find_data(323):
                return 
            else:
                return ''
            
        case 'deposit':
            # 408-410
            return find_data(408)
        case 'balance':
            return find_data(502)

def find_data(left_padding):
    """Finds the data given specified parameters"""
    print('finding in soup')
    # print(soup.find_all('div'))
    print(soup.find_all('div', attrs={'style':re.compile('left:'+str(left_padding)+'px;')}))

    return

pdf_path = 'test.pdf'
html_path = 'output_pdfminer.html'
csv_path = 'result.csv'

# set global variable
html_text = ''
with open(html_path, 'r') as f:
    html_text = f.read()

soup = BeautifulSoup(html_text, 'html.parser')

find_data('136')

# convert_pdf_to_html(pdf_path, html_path)
# get_data('deposit','output_pdfminer.html')
# convert_html_to_csv(html_path, csv_path)