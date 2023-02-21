import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# parameters
mu = 0/10000                    # bps
sig = 0.006                     # volatility % p.a. np.sqrt(252)
n_days = 25                     # number of days
n_months = 12                   # number of months
n_funds = 10                    # number of funds
max_DD = 0.08                   # number of funds
notional = 10**6                # notional for each manager
AUM_1L = notional*n_funds       # 1L AUM


# initialize managers PNL
managers_PNL = pd.DataFrame(np.zeros(n_funds)).transpose()
managers_PNL.columns = ["fund " + str(x+1) for x in range(n_funds)]

# initialize managers notionals
managers_not = pd.DataFrame(np.ones(n_funds)*notional).transpose()
managers_not.columns = ["fund " + str(x+1) for x in range(n_funds)]


# generate simulated daily returns
def generateDailyReturns(mu, sig, n_days, n_funds, max_DD):
    # initialize fund daily returns
    fund_returns = pd.DataFrame(np.ones(n_funds)).transpose()
    fund_returns.columns = ["fund " + str(x+1) for x in range(n_funds)]
    for i in range(n_days):

        dailies_rand = pd.DataFrame(data=np.random.normal(loc= mu,
                                                          scale=sig,
                                                          size=n_funds)+1
                                    ).transpose()

        dailies_rand.columns = fund_returns.columns

        fund_returns = pd.concat([fund_returns, dailies_rand])

    # reindexing and calculate cumulative returns
    fund_returns.index = range(n_days+1)
    fund_returns = fund_returns.cumprod()

    # loop that insert na if fund was stopped
    for j in range(len(fund_returns.columns)):
        tau = fund_returns["fund " + str(j+1)][fund_returns["fund " + str(j+1)] < (1 - max_DD)].index.min()
        if tau is not np.nan:
            fund_returns["fund " + str(j + 1)][tau:] = np.nan

    return fund_returns

def updateNotional(fund_returns, managers_not):
    # notional reduction
    monthly_loss = fund_returns[-1:].values-1
    monthly_loss[monthly_loss > 0] = 0
    append_not = np.multiply((1 + monthly_loss * 10), managers_not[-1:]) # reduce notional by x10 loss

    # notional refill
    monthly_gain = fund_returns[-1:].values-1
    monthly_gain[monthly_gain <= 0] = 0
    append_not = np.multiply((1 + monthly_gain * 10), append_not)

    # max notional at initial level
    append_not[append_not > notional] = notional

    return pd.concat([managers_not, append_not])

for i in range(n_months):

    # generate daily returns
    fund_returns = generateDailyReturns(mu, sig, n_days, n_funds, max_DD)

    # append new daily pnl
    pnl = pd.DataFrame(np.multiply(fund_returns.diff()[1:].values, managers_not[-1:].values))
    pnl.columns = ["fund " + str(x + 1) for x in range(n_funds)]
    managers_PNL = pd.concat([managers_PNL, pnl])

    # append new notionals
    managers_not = updateNotional(fund_returns, managers_not)

    # fund_returns.plot()

# reindexing
managers_not.index = range(n_months+1)
managers_PNL.index = range(n_days*n_months+1)
managers_cum_PNL = managers_PNL.cumsum()


