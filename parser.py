from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import io
import csv
import re
import glob
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

    description_header = []
    cash_rebate_flag = False
    for i, row in enumerate(description):
        if (re.match(
            '.*GIRO|.*TRANSFER|PAYMENT|COMM|FAST|.*CHARGE|.*PURCHASE|.* FEE|.*REBATE|BILL|DEBIT CREDIT|CHEQUE DEPOSIT',
            row)):

            # CASH REBATE repeats itself in the description unlike others
            if cash_rebate_flag and row == 'CASH REBATE':
                cash_rebate_flag = False
                continue
            
            description_header.append(row)

            cash_rebate_flag = row == 'CASH REBATE'


    # remove last item as it is total withdrawals
    withdrawal = [row for row in get_data('withdrawal', soup) if not has_words_or_zero(row)][0:-1]

    # remove last item as it is average balance
    deposit = [row for row in get_data('deposit', soup) if not has_words_or_zero(row)][0:-1]

    cheque = get_data('cheque', soup)
    
    # picks up the starting and ending balance, so remove ending balance
    # don't remove starting balance as it's needed for the first tx
    balance = get_data('balance', soup)[:-1]

    # debugging statements
    # print(balance)
    # print(value_date)
    # print(transaction_date)
    # print(description_header)
    # print(withdrawal)
    # print(deposit)
    # print(cheque)

    # sanity check to ensure all txs are picked up
    len_balance = len(balance)
    len_value_date = len(value_date)
    len_transaction_date = len(transaction_date)
    len_description_header = len(description_header)
    len_withdrawal = len(withdrawal)
    len_deposit = len(deposit)
    len_cheque = len(cheque)

    if((len_balance - 1) == len_value_date == len_transaction_date == len_description_header == (len_withdrawal + len_deposit)):
        print('Tests passed')
    else:
        print('Tests failed')
        print('Total balances excluding start balance: ', len_balance-1)
        print('Total value date: ', len_value_date)
        print('Total transaction date: ', len_transaction_date)
        print('Total description header: ', len_description_header)
        print('Total withdrawals: ', len_withdrawal)
        print('Total deposits: ', len_deposit)
        print('Total cheques: ', len_cheque)

        return
    
    rows = []
    deposit_index = 0
    withdrawal_index = 0
    cheque_index = 0
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
        # since we keep the start balance

        if (float(balance[i].replace(',','')) < float(balance[i+1].replace(',',''))):
            if(description_header[i] == 'CHEQUE DEPOSIT'):
                rows.append(
                    DataRow(
                    tx,
                    value_date[i],
                    tx_description,
                    cheque[cheque_index],
                    '',
                    deposit[deposit_index],
                    balance[i+1]
                    ))
                cheque_index += 1
                deposit_index += 1
            else:
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
            return find_data('(248)',soup)
        case 'withdrawal':
            return find_data('(321|323|324|325|326|327|328|329)',soup) 
        case 'deposit':
            return find_data('(406|407|408|409|410|411|412|413)',soup)
        case 'balance':
            return find_data('(502|503|504|505|506|507|508|509|510)',soup)

def find_data(left_padding,soup):
    """Finds the data given specified parameters"""

    text_list = soup.find_all('div', attrs={'style':re.compile('left:'+str(left_padding)+'px;')})

    # re-order according to top
    # sometimes it's jumbled up
    # TODO: use this somehow to make the descriptions easier
    ordered_text_list = []
    for i, text in enumerate(text_list):
        order = re.search('top:(.*?)px;',text['style']).group(1)
        actual_text = text.get_text().strip()

        ordered_text_list.append([int(order), actual_text])

    ordered_text_list.sort(key=lambda x: x[0])

    return list(map(lambda x: x[1], ordered_text_list))

def has_words_or_zero(input):
    return re.findall('[a-zA-Z]|^0\\.00$',input)

# example if you have a 'data' folder with the statements
pdf_folder = glob.glob('data/*.pdf')

convert_ocbc_statement_multi(pdf_folder)