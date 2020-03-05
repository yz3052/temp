from __future__ import division

from functools import wraps

import numpy as np
from pandas import DataFrame, Series




def series_indicator(col):
    def inner_series_indicator(f):
        @wraps(f)
        def wrapper(s, *args, **kwargs):
            if isinstance(s, DataFrame):
                s = s[col]
            return f(s, *args, **kwargs)
        return wrapper
    return inner_series_indicator


def _wilder_sum(s, n):
    s = s.dropna()

    nf = (n - 1) / n
    ws = [np.nan]*(n - 1) + [s[n - 1] + nf*sum(s[:n - 1])]

    for v in s[n:]:
        ws.append(v + ws[-1]*nf)

    return Series(ws, index=s.index)


@series_indicator('high')
def hhv(s, n):
    
    return s.rolling(n).max()


@series_indicator('low')
def llv(s, n):
    return s.rolling(n).min()


@series_indicator('close')
def ema(s, n, wilder=False):
    span = n if not wilder else 2*n - 1
    return s.ewm(span = span).mean()


@series_indicator('close')
def macd(s, nfast=12, nslow=26, nsig=9, percent=True):
    fast, slow = ema(s, nfast), ema(s, nslow)

    if percent:
        macd = 100*(fast / slow - 1)
    else:
        macd = fast - slow

    sig = ema(macd, nsig)
    hist = macd - sig

    return DataFrame(dict(macd=macd, signal=sig, hist=hist,
                          fast=fast, slow=slow))


@series_indicator('close')
def rsi(s, n=14):
    diff = s.diff()
    which_dn = diff < 0

    up, dn = diff, diff*0
    up[which_dn], dn[which_dn] = 0, -up[which_dn]

    emaup = ema(up, n, wilder=True)
    emadn = ema(dn, n, wilder=True)


    return 100 * emaup/(emaup + emadn)



    return DataFrame(dict(fastk=fastk, fullk=fullk, fulld=fulld))


@series_indicator('close')
def dtosc(s, nrsi=13, nfastk=8, nfullk=5, nfulld=3):
    srsi = stoch(rsi(s, nrsi), nfastk, nfullk, nfulld)
    return DataFrame(dict(fast=srsi.fullk, slow=srsi.fulld))


def atr(s, n=14):
    cs = s.close.shift(1)
    tr = s.high.combine(cs, max) - s.low.combine(cs, min)

    return ema(tr, n, wilder=True)


def cmf(s, n=20):
    clv = (2*s.close - s.high - s.low) / (s.high - s.low)
    vol = s.volume

    return (clv*vol).rolling(n).sum() / vol.rolling(n).sum()


def force(s, n=2):
    return ema(s.close.diff()*s.volume, n)


@series_indicator('close')
def kst(s, r1=10, r2=15, r3=20, r4=30, n1=10, n2=10, n3=10, n4=15, nsig=9):
    
    rocma1 = (s / s.shift(r1) - 1).rolling(n1).mean()
    rocma2 = (s / s.shift(r2) - 1).rolling(n2).mean()
    rocma3 = (s / s.shift(r3) - 1).rolling(n3).mean()
    rocma4 = (s / s.shift(r4) - 1).rolling(n4).mean()

    kst = 100*(rocma1 + 2*rocma2 + 3*rocma3 + 4*rocma4)
    sig = kst.rolling(nsig).mean()    

    return DataFrame(dict(kst=kst, signal=sig))


def ichimoku(s, n1=9, n2=26, n3=52):
    conv = (hhv(s, n1) + llv(s, n1)) / 2
    base = (hhv(s, n2) + llv(s, n2)) / 2

    spana = (conv + base) / 2
    spanb = (hhv(s, n3) + llv(s, n3)) / 2

    return DataFrame(dict(conv=conv, base=base, spana=spana.shift(n2),
                          spanb=spanb.shift(n2), lspan=s.close.shift(-n2)))


def ultimate(s, n1=7, n2=14, n3=28):
    cs = s.close.shift(1)
    bp = s.close - s.low.combine(cs, min)
    tr = s.high.combine(cs, max) - s.low.combine(cs, min)

    avg1 = bp.rolling(n1).sum() / tr.rolling(n1).sum()
    avg2 = bp.rolling(n2).sum() / tr.rolling(n2).sum()
    avg3 = bp.rolling(n3).sum() / tr.rolling(n3).sum()

    return 100*(4*avg1 + 2*avg2 + avg3) / 7


def auto_envelope(s, nema=22, nsmooth=100, ndev=2.7):
    sema = ema(s.close, nema)
    mdiff = s[['high','low']].sub(sema, axis=0).abs().max(axis=1)
    csize = mdiff.ewm(nsmooth).std()*ndev
    
    

    return DataFrame(dict(ema=sema, lenv=sema - csize, henv=sema + csize))


@series_indicator('close')
def bbands(s, n=20, ndev=2):
    
    mavg = s.rolling(n).mean()
    mstd = s.rolling(n).std()

    hband = mavg + ndev*mstd
    lband = mavg - ndev*mstd

    return DataFrame(dict(ma=mavg, lband=lband, hband=hband))




def sar(s, af=0.02, amax=0.2):
    high, low = s.high, s.low

    # Starting values
    sig0, xpt0, af0 = True, high[0], af
    sar = [low[0] - (high - low).std()]

    for i in range(1, len(s)):
        sig1, xpt1, af1 = sig0, xpt0, af0

        lmin = min(low[i - 1], low[i])
        lmax = max(high[i - 1], high[i])

        if sig1:
            sig0 = low[i] > sar[-1]
            xpt0 = max(lmax, xpt1)
        else:
            sig0 = high[i] >= sar[-1]
            xpt0 = min(lmin, xpt1)

        if sig0 == sig1:
            sari = sar[-1] + (xpt1 - sar[-1])*af1
            af0 = min(amax, af1 + af)

            if sig0:
                af0 = af0 if xpt0 > xpt1 else af1
                sari = min(sari, lmin)
            else:
                af0 = af0 if xpt0 < xpt1 else af1
                sari = max(sari, lmax)
        else:
            af0 = af
            sari = xpt0

        sar.append(sari)

    return Series(sar, index=s.index)


def adx(s, n=14):
    cs = s.close.shift(1)
    tr = s.high.combine(cs, max) - s.low.combine(cs, min)
    trs = _wilder_sum(tr, n)

    up = s.high - s.high.shift(1)
    dn = s.low.shift(1) - s.low

    pos = ((up > dn) & (up > 0)) * up
    neg = ((dn > up) & (dn > 0)) * dn

    dip = 100 * _wilder_sum(pos, n) / trs
    din = 100 * _wilder_sum(neg, n) / trs

    dx = 100 * np.abs((dip - din)/(dip + din))
    adx = ema(dx, n, wilder=True)

    return DataFrame(dict(adx=adx, dip=dip, din=din))


def chandelier(s, position, n=22, npen=3):
    if position == 'long':
        return hhv(s, n) - npen*atr(s, n)
    else:
        return llv(s, n) + npen*atr(s, n)


def vortex(s, n=14):
    ss = s.shift(1)

    tr = s.high.combine(ss.close, max) - s.low.combine(ss.close, min)
    trn = tr.rolling(n).sum()    

    vmp = np.abs(s.high - ss.low)
    vmm = np.abs(s.low - ss.high)

    vip = vmp.rolling(n).sum() / trn    
    vin = vmm.rolling(n).sum() / trn

    return DataFrame(dict(vin=vin, vip=vip))


@series_indicator('close')
def gmma(s, nshort=[3, 5, 8, 10, 12, 15],
         nlong=[30, 35, 40, 45, 50, 60]):
    short = {str(n): ema(s, n) for n in nshort}
    long = {str(n): ema(s, n) for n in nlong}

    return DataFrame(short), DataFrame(long)



def zigzag(ts_date, ts_high, ts_low, ts_close, how = 'static', pct=5, window = 50, percent_std = 0.3, ):
# any s_* variables are numpy arrays.
# how = static / dyanmic
    
        
    # Sanity check    
    
    if len(ts_date) <= window * 1.5:
        raise Exception('Input data length too short.')
    
    
    # Set up key parameters
    
    ts_index = list(range(len(ts_close)))
    state_trend = None

    
    # Decide sensitivity parameters and Set up other parameters

    if how == 'dynamic':        
    
        state_last_index = ts_index[window-1]
        state_last_price = ts_close[state_last_index]
        o_index = [state_last_index]
        o_ts = [state_last_price]
        o_std = [np.std(ts_close[:window]) / np.mean(ts_close[:window]) * 100 * percent_std]
        o_trend= [0]
                
    else:
        
        state_last_index = ts_index[0]
        state_last_price = ts_close[state_last_index]
        o_index = [state_last_index]
        o_ts = [state_last_price]
        o_std = [pct]
        o_trend = [0]


    # Loop

    for i_index, i_high, i_low in zip(ts_index, ts_high, ts_low):
        
        # Update pct if dynamic
        
        if how == 'dynamic':
            
            if i_index < window-1:
                continue
            
            pct = np.std(ts_close[i_index-window+1:i_index+1]) / np.mean(ts_close[i_index-window+1:i_index+1]) * 100 * percent_std
            
            up_state_trend = 1 + pct / 100
            down_state_trend = 1 - pct / 100
                        
        else:
            
            up_state_trend = 1 + pct / 100
            down_state_trend = 1 - pct / 100
    
        
        # No initial trend
        if state_trend is None:
            if i_high / state_last_price > up_state_trend:
                state_trend = 1
            elif i_low / state_last_price < down_state_trend:
                state_trend = -1
        
        # state_trend is up
        elif state_trend == 1:
            # New high
            if i_high > state_last_price:
                state_last_index, state_last_price = i_index, i_high
            # Reversal
            elif i_low / state_last_price < down_state_trend:
                o_index.append(state_last_index)
                o_ts.append(state_last_price)
                o_std.append(pct)
                o_trend.append(1)

                state_trend, state_last_index, state_last_price = -1, i_index, i_low
        
        # state_trend is down
        else:
            # New low
            if i_low < state_last_price:
                state_last_index, state_last_price = i_index, i_low
            # Reversal
            elif i_high / state_last_price > up_state_trend:
                o_index.append(state_last_index)
                o_ts.append(state_last_price)
                o_std.append(pct)
                o_trend.append(-1)

                state_trend, state_last_index, state_last_price = 1, i_index, i_high

    # Extrapolate the current state_trend
    if o_index[-1] != ts_index[-1]:
        o_index.append(ts_index[-1])

        if state_trend is None:
            o_ts.append(ts_close[o_index[-1]])
        elif state_trend == 1:
            o_ts.append(ts_high[o_index[-1]])
            o_trend.append(1)
        else:
            o_ts.append(ts_low[o_index[-1]])
            o_trend.append(0)
    
    # format and shapes
    o_ts = np.array(o_ts).reshape((len(o_ts),1))
    o_trend = np.array(o_trend).reshape((len(o_trend),1))
    
    
    return ts_date[o_index].reshape((len(ts_date[o_index]),1)), o_ts, o_trend ,o_std



def sr_point (ts_date, ts_high, ts_low, ts_close, tolerance=0.005, type = 'peak', extrema_lookback = 12, how = 'static', pct=5, window = 50, percent_std = 0.3,):
    
    # Step 0 - Sanity check
   
    if len(ts_date) <= window * 1.5:
        return None, None, None
    
    
    # Step 1 - Get zigzag
    
    pivot_ts, pivot_price, pivot_trend,_ = zigzag(ts_date, ts_high, ts_low, ts_close, window = window, how = how, percent_std = percent_std)
    
    if len(pivot_ts) < 10:
        return None, None, None
    
    # Step 2 - Normalize zigzag
    
    #pivot_price = (pivot_price - ts_close.mean()) / ts_close.std()
    
    # Step 3 - Evaluate if the selected extrema are SR
    
    t_current_trend = [pivot_ts[-1], pivot_price[-1], pivot_trend[-1]]
    
    pivot_ts, pivot_price, pivot_trend = pivot_ts[-extrema_lookback:-1], pivot_price[-extrema_lookback:-1], pivot_trend[-extrema_lookback:-1]
    
    t_peak_price = pivot_price[pivot_trend == 1]
    t_trough_price = pivot_price[pivot_trend == -1]
    t_peak_ts = pivot_ts[pivot_trend == 1]
    t_trough_ts = pivot_ts[pivot_trend == -1]
    
       
    
    # Step 4 - Output
    
    if type == 'peak':
        if (np.sort(np.absolute(t_peak_price[:-2]-t_peak_price[-1]))[:2].sum() + np.absolute(t_peak_price[-2]-t_peak_price[-1])) / t_peak_price[-1] < tolerance:
            
            #t_peak_price = t_peak_price * ts_close.std() + ts_close.mean()
            #t_trough_price = t_trough_price * ts_close.std() + ts_close.mean()
            
            return t_peak_ts[-1], t_peak_price[-1], [t_peak_price]
        else:
            return None, None, None
        
    elif type == 'trough':
        if (np.sort(np.absolute(t_trough_price[:-2]-t_trough_price[-1]))[:2].sum() + np.absolute(t_trough_price[-2] - t_trough_price[-1])) / t_trough_price[-1] < tolerance:
            
            #t_peak_price = t_peak_price * ts_close.std() + ts_close.mean()
            #t_trough_price = t_trough_price * ts_close.std() + ts_close.mean()
            
            return t_trough_ts[-1], t_trough_price[-1], [t_trough_price]
        else:
            return None, None, None

