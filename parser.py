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

def convert_ocbc_statement(pdf_path, html_path, csv_path):
    convert_pdf_to_html(pdf_path, html_path)
    convert_html_to_csv(html_path, csv_path)

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

    # TODO: splice together the results from get_data and get the final row objects needed.
    # TODO: maybe decide whether it is withdrawal or deposit depending on balance change
    # decided against using groupby because the top padding doesn't always align
    soup = read_html_to_soup(html_path)

    transaction_date = get_data('transaction date', soup)
    value_date = get_data('value date', soup)
    description = get_data('description', soup)
    withdrawal = get_data('withdrawal', soup)
    deposit = get_data('deposit', soup)
    balance = get_data('balance', soup)

    rows = []
    rows.append(DataRow('test transaction date','test value date','test description','test cheque','test withdrawal','test deposit','test balance'))
    rows.append(DataRow('test transaction date2','test value date2','test description2','test cheque2','test withdrawal2','test deposit2','test balance2'))

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f,fieldnames=rows[0].__dict__.keys())
        rows = map(lambda x: x.__dict__, rows)
        writer.writeheader()
        writer.writerows(rows)

def read_html_to_soup(html_path):
    """Takes a html document and puts it into a beautifulsoup object"""

    html_text = ''

    with open(html_path, 'r') as f:
        html_text = f.read()

    return BeautifulSoup(html_text, 'html.parser')

def get_data(option, soup):
    """Get the data based on left padding, from observation. 
    
    Values are hard coded based on the generated html file."""

    match option:
        # range mainly depends on number of digits per tx
        case 'transaction date':
            return find_data('(43|44|45|46)',soup)
        case 'value date':
            return find_data('(91|92|93|94|95|96)',soup)
        case 'description':
            return find_data('(136)',soup)
        case 'cheque':
            # don't have this case in the documents currently
            return ''
        case 'withdrawal':
            return find_data('(321|323|324|325|326|327|328)',soup) 
        case 'deposit':
            return find_data('(406|407|408|409|410|411|412)',soup)
        case 'balance':
            return find_data('(502)',soup)

def find_data(left_padding,soup):
    """Finds the data given specified parameters"""
    print('finding in soup')
    text_list = soup.find_all('div', attrs={'style':re.compile('left:'+str(left_padding)+'px;')})
    for result in text_list:
        print(result.get_text())
    return text_list

# set file paths here to the files you want to check against
pdf_path = 'test.pdf'
html_path = 'output_pdfminer.html'
csv_path = 'result.csv'

convert_html_to_csv(html_path,csv_path)

# convert_ocbc_statement(pdf_path, html_path, csv_path)