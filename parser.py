from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import io
import csv
import re
from bs4 import BeautifulSoup

class DataRow:
    '''
    A class representing each row of transaction in the OCBC bank statement.
    
    For ease of use
    '''

    def __init__(self, transaction_date, value_date, description, cheque, withdrawal, deposit, balance):
        self.transaction_date = transaction_date
        self.value_date = value_date
        self.description = description
        self.cheque = cheque
        self.withdrawal = withdrawal
        self.deposit = deposit
        self.balance = balance

def convert_ocbc_statement_multi(pdf_paths):
    for path in pdf_paths:
        convert_ocbc_statement(path)

def convert_ocbc_statement(pdf_path):
    pdf_filename = pdf_path.split('.')[-2]
    html_path = pdf_filename + '.html'
    csv_path = pdf_filename + '.csv'
    convert_pdf_to_html(pdf_path, html_path)
    convert_html_to_csv(html_path, csv_path)

def convert_pdf_to_html(pdf_path, html_path):
    '''Creates a html that can be read by the code to get data, including column information.'''

    output_html = io.BytesIO()
    with open(pdf_path, 'rb') as pdf_file:
        extract_text_to_fp(pdf_file, output_html, laparams=LAParams(), output_type='html')
    html_content = output_html.getvalue().decode('utf-8')

    with open(html_path, 'w') as html_file:
        html_file.write(html_content)

def convert_html_to_csv(html_path, csv_path):
    '''Creates the CSV using information from the html file generated.'''

    # decided against using groupby for description because the top padding doesn't always align
    soup = read_html_to_soup(html_path)

    # picks up some non-date values, so strip them away
    transaction_date = [row for row in get_data('transaction date', soup) if len(row) == 6]
    value_date = [row for row in get_data('value date', soup) if len(row) == 6]

    # remove opening and closing balance words
    description = [row for row in get_data('description', soup) if 
                   re.match(
                       '^(?!(BALANCE (B|C)/F|Description|Total Withdrawals/Deposits|Total Interest Paid This Year|Average Balance)$).*$',
                         row)]

    # GIRO, COMM, PAYMENT, TRANSFER, CHARGE, PURCHASE captures most of the data I need
    description_header = [row for row in description if 
                          re.match(
                              '.*GIRO|.*TRANSFER|PAYMENT|COMM|FAST|.*CHARGE|.*PURCHAS|.*FEE',
                                                row)]
    
    # remove last item as it is total withdrawals
    withdrawal = [row for row in get_data('withdrawal', soup) if not has_words(row)][0:-1]

    # remove last item as it is average balance
    deposit = [row for row in get_data('deposit', soup) if not has_words(row)][0:-1]
    
    # picks up the starting and ending balance, so remove ending balance
    # don't remove starting balance as it's needed for the first tx
    balance = get_data('balance', soup)[:-1]

    # sanity check to ensure all txs are picked up
    len_balance = len(balance)
    len_value_date = len(value_date)
    len_transaction_date = len(transaction_date)
    len_description_header = len(description_header)
    len_withdrawal = len(withdrawal)
    len_deposit = len(deposit)

    if((len_balance - 1) == len_value_date == len_transaction_date == len_description_header == (len_withdrawal + len_deposit)):
        print('Tests passed')
    else:
        print('Tests failed')
        print('Total balance excluding last balance: ', len_balance-1)
        print('Total value date: ', len_value_date)
        print('Total transaction date: ', len_transaction_date)
        print('Total description header: ', len_description_header)
        print('Total withdrawals: ', len_withdrawal)
        print('Total deposits: ', len_deposit)

        return
    
    rows = []
    deposit_index = 0
    withdrawal_index = 0
    len_description = len(description)
    description_index = 1

    for i, tx in enumerate(transaction_date):

        tx_description = ''
        description_list = []
        description_list.append(description_header[i])

        if(i == len_transaction_date - 1):
            while(description_index < len_description):
                description_list.append(description[description_index])
                description_index += 1

        else:
            while(description[description_index] != description_header[i+1]):
                description_list.append(description[description_index])
                description_index += 1
            
            # have to +1 again to move past the next header
            description_index += 1

        tx_description = '\n'.join(description_list)

        # note that len(balance) is the same as len(transaction_date) + 1
        # since we keep the final balance
        if (balance[i] < balance[i+1]):
            rows.append(
                DataRow(
                    tx,
                    value_date[i],
                    tx_description,
                    '',
                    '',
                    deposit[deposit_index],
                    balance[i+1]
                    ))
            deposit_index += 1
        else:
            rows.append(
                DataRow(
                    tx,
                    value_date[i],
                    tx_description,
                    '',
                    withdrawal[withdrawal_index],
                    '',
                    balance[i+1]
                    ))
            withdrawal_index+=1

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

    text_list = soup.find_all('div', attrs={'style':re.compile('left:'+str(left_padding)+'px;')})
    
    # return a list of string
    text_list_string = list(map(lambda x: x.get_text().strip(), text_list))

    return text_list_string

def has_words(input):
    return re.findall('[a-zA-Z]',input)

# set file paths here to the files you want to check against
pdf_paths = ['test.pdf']
convert_ocbc_statement_multi(pdf_paths)