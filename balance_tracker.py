import datetime
import plaid
import time

def day_format(dt):
    return str(dt).split()[0]
def get_today():
    return day_format(datetime.datetime.today())
def get_x_days_ago(x):
    today = datetime.datetime.today()
    other_day = today - datetime.timedelta(days=x)
    return day_format(other_day)

class BalanceTracker:
    def __init__(self, client_id, secret, access_token):
        self.plaid_client = plaid.Client(client_id, secret, 'development')
        self.access_token = access_token
        self._response = self.plaid_client.Accounts.balance.get(access_token)

    def print_account_information(self):
        for account in self._response['accounts']:
            print(account['account_id'], account['name'], account['balances']['available'])

    def account_id_from_offset(self, i: int):
        account = self._response['accounts'][i]
        return account['account_id']

    def _max_account_id(self):
        account_id = None
        balance = 0
        for account in self._response['accounts']:
            bal = account['balances']['available']
            if bal > balance:
                balance = bal
                account_id = account['account_id']
        return account_id

    def current_balance(self, account_id):
        balance = 0
        for account in self._response['accounts']:
            if account['account_id'] == account_id:
                return account['balances']['available']

    def balances_over_days(self, num_days, _account_id=None):
        # get complete transactions object
        today = get_today()
        start_day = get_x_days_ago(num_days)
        response = self.plaid_client.Transactions.get(self.access_token, start_day, today, count=500)

        transactions = response['transactions']
        num_transactions = response['total_transactions']
        print(f'Number of transactions: {num_transactions}')
        num_received_transactions = len(transactions)
        while num_received_transactions < num_transactions:
            offset = num_received_transactions
            next_response = None
            while not next_response:
                try:
                    next_response = self.plaid_client.Transactions.get(self.access_token, start_day, today, count=500, offset=offset)
                    num_received_transactions += len(next_response['transactions'])
                    transactions.extend(next_response['transactions'])
                except:
                    time.sleep(1)

        # if no account id is provided, use the one with the max balance by default
        account_id = _account_id if _account_id else self._max_account_id()
        # compute balances over days
        balance = self.current_balance(account_id)
        balances = [balance]
        for i in range(num_days):
            day = get_x_days_ago(i)
            balance += self._one_day_of_expenses(day, transactions, account_id)
            balances.append(balance)
        return list(reversed(balances))

    def _one_day_of_expenses(self, day, transactions, account_id):
        total_expenses = 0
        for txn in transactions:
            if txn['account_id'] != account_id or txn['date'] != day:
                continue
            total_expenses += txn['amount']
        return total_expenses
