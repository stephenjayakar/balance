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
        self._asset_report_response = None

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
        account_id = _account_id if _account_id else self._max_account_id()
        # caching solution as an asset_report includes all account_ids for an item
        if not self._asset_report_response:
            pl = self.plaid_client

            # generate assets report
            asset_report_create_response = pl.AssetReport.create(
                [self.access_token],
                num_days,
            )
            asset_report_token = asset_report_create_response['asset_report_token']
            # get / wait for asset report
            response = None
            while True:
                try:
                    response = pl.AssetReport.get(asset_report_token)
                    break
                except:
                    print("sleeping as asset report isn't ready")
                    time.sleep(0.5)
            self._asset_report_response = response

        response = self._asset_report_response
        all_account_info = response['report']['items'][0]['accounts']
        # select account info for the correct account
        account = None
        for acct in all_account_info:
            if acct['account_id'] == account_id:
                account = acct
                break
        if account == None:
            raise Exception('something went wrong')
        historical_balances = account['historical_balances']
        ret_balances = []
        for balance in historical_balances:
            ret_balances.append(balance['current'])
        return list(reversed(ret_balances))
