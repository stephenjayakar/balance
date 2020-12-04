import datetime
import requests
import time

URL_BASE = 'https://development.plaid.com'

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
        self.client_id = client_id
        self.secret = secret
        self.access_token = access_token

        request_body = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": self.access_token,
        }
        self.response = requests.post(url=f'{URL_BASE}/accounts/balance/get', json=request_body).json()
        # compute current balance plus account_id
        # assuming the max balance is the current balance
        self._current_balance = 0
        self._account_id = ""
        for account in self.response['accounts']:
            bal = account['balances']['available']
            if bal > self._current_balance:
                self._current_balance = bal
                self._account_id = account['account_id']

    def current_balance(self):
        return self._current_balance

    def balances_over_days(self, num_days):
        # get complete transactions object
        today = get_today()
        start_day = get_x_days_ago(num_days)
        request_body = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": self.access_token,
            "start_date": start_day,
            "end_date": today,
            "options": {
                "count": 500,
            },
        }
        response = requests.post(url=f'{URL_BASE}/transactions/get', json=request_body).json()
        transactions = response['transactions']
        num_transactions = response['total_transactions']
        print(f'Number of transactions: {num_transactions}')
        num_received_transactions = len(transactions)
        # TODO: debug this as I'm not really testing this now
        while num_received_transactions < num_transactions:
            request_body['options']['offset'] = num_received_transactions
            next_response = None
            while not next_response:
                try:
                    next_response = requests.post(url=f'{URL_BASE}/transactions/get', json=request_body).json()
                    num_received_transactions += len(next_response['transactions'])
                    transactions.extend(next_response['transactions'])
                except:
                    time.sleep(1)

        # compute balances over days
        balance = self.current_balance()
        balances = [balance]
        for i in range(num_days):
            day = get_x_days_ago(i)
            balance += self._one_day_of_expenses(day, transactions)
            balances.append(balance)
        return list(reversed(balances))

    def _one_day_of_expenses(self, day, transactions):
        total_expenses = 0
        for txn in transactions:
            if txn['account_id'] != self._account_id or txn['date'] != day:
                continue
            total_expenses += txn['amount']
        return total_expenses
