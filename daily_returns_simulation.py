import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
pd.options.plotting.backend = "plotly"

# parameters
mu = 0.05/252             # bps
sig = 0.10/np.sqrt(252)         # volatility % p.a. np.sqrt(252)
n_days = 25                     # number of days
n_months = 12                   # number of months
n_funds = 50                    # number of funds
max_DD = 0.08                   # number of funds
notional = 10**6                # notional for each manager
AUM_1L = notional       # 1L AUM
lev = 10                         # leverage


# initialize managers PNL
managers_PNL = pd.DataFrame(np.zeros(n_funds)).transpose()
managers_PNL.columns = ["fund " + str(x+1) for x in range(n_funds)]

# initialize managers returns
managers_ret = pd.DataFrame(np.zeros(n_funds)).transpose()
managers_ret.columns = ["fund " + str(x+1) for x in range(n_funds)]

# initialize managers notionals
managers_not = pd.DataFrame(np.ones(n_funds)*notional*lev).transpose()
managers_not.columns = ["fund " + str(x+1) for x in range(n_funds)]

# initialize 1L PNL
pnl_monthly_1L = list()

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
    append_not[append_not > notional*lev] = notional*lev

    return pd.concat([managers_not, append_not])

# simulation loop
for i in range(n_months):

    # generate daily returns
    fund_returns = generateDailyReturns(mu, sig, n_days, n_funds, max_DD)

    # append new returns
    managers_ret = pd.concat([managers_ret, fund_returns.diff()[1:]])

    # append new daily pnl
    pnl = pd.DataFrame(np.multiply(fund_returns.diff()[1:].values, managers_not[-1:].values))
    pnl.columns = ["fund " + str(x + 1) for x in range(n_funds)]
    managers_PNL = pd.concat([managers_PNL, pnl])

    # append new notionals
    managers_not = updateNotional(fund_returns, managers_not)

    pnl_1L = pnl[-1:].values - (managers_not[:1].values - managers_not[-1:].values)
    pnl_1L = pd.DataFrame(pnl_1L).fillna(0)
    pnl_1L[pnl_1L < 0] = 0
    pnl_monthly_1L.append(pnl_1L.sum().sum())


    # fund_returns.plot()



# initialize 1L PNL
pnl_monthly_1L = pd.DataFrame(pnl_monthly_1L, columns = ["1L_pnl"])
pnl_monthly_1L = pd.concat([pd.DataFrame(data={"1L_pnl":0}, index=[0]), pnl_monthly_1L])
pnl_monthly_1L.index = [0] + [(i+1)*n_days for i in range(n_months)]
pnl_monthly_1L_cum = pnl_monthly_1L.cumsum()

# reindexing
managers_not.index = range(n_months+1)
managers_PNL.index = range(n_days*n_months+1)
managers_ret.index = range(n_days*n_months+1)
managers_cum_PNL = managers_PNL.cumsum()

df_toplot = managers_cum_PNL.join(pnl_monthly_1L_cum)
df_toplot = df_toplot.fillna(method='ffill')

fig = df_toplot.plot.line()
fig.show()
print(pnl_monthly_1L)
print((pnl_monthly_1L/AUM_1L)*100)
