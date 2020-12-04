# balance

This readme is basically for myself.

`balance` is a small program I wrote to calculate my bank account's balance over time.  I didn't really test a lot of stuff, there are some questionable design decisions, and this isn't batteries included.  A basic setup guide:

1. Get the `client_id`, `secret`, and `access_token` by creating a Plaid account and using the Quickstart in the development environment on your own bank account.
2. Plug them into the `balances_over_days` method and have fun!
