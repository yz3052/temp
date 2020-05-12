# -*- coding: utf-8 -*-
"""
Created on Sat May  9 16:06:10 2020

@author: tomyi
"""
import inspect

import pandas as pd
import numpy as np

import pickle


class Backtest(object):
    
    def __init__(self, strat_func, pv_mkt_data, signals, str_from_ymd, str_to_ymd, bar_cache):
        # pv_mkt_data ['raw','beta']
        # str_from_ymd, str_to_ymd 'YYYY-MM-DD'
        
        # cdates
        if isinstance(str_from_ymd, str) & isinstance(str_to_ymd, str) &\
            len(str_from_ymd)==10 & len(str_to_ymd)==10 &\
            ('-' in str_from_ymd) & ('-' in str_to_ymd):
            self.cdates = pd.date_range(start=str_from_ymd, end=str_to_ymd).tolist()
        elif str_from_ymd == '' or str_from_ymd is None or str_to_ymd == '' or str_to_ymd is None:
            self.cdates = pd.date_range(start='2010-06-01', end='2019-11-10').tolist()
        else:
            raise Exception('Date format incorrect.')
        
        
        # market data: cc, co
        if 'beta' in pv_mkt_data.lower():
            self.pv_cc_ret = pd.read_parquet(r"C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\pv_beta_adj_cc_ret.p")
            self.pv_co_ret = pd.read_parquet(r"C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\pv_beta_adj_co_ret.p")
            
        elif 'raw' in pv_mkt_data.lower():
            self.pv_cc_ret = pd.read_parquet(r"C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\pv_cc_raw_ret_spx.p")
            self.pv_co_ret = pd.read_parquet(r"C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\pv_co_raw_ret_spx.p")
            
        self.pv_cc_ret = self.pv_cc_ret.reindex(index = self.cdates)
        self.pv_co_ret = self.pv_co_ret.reindex(index = self.cdates)
        
        # market data: volume
        self.pv_vD = pd.read_parquet(r"C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\pv_vD_spx.p")
        self.pv_vD  = self.pv_vD.reindex(index = self.cdates)
        
        if self.pv_vD.columns.tolist() != self.pv_cc_ret.columns.tolist():
            raise Exception('Volume columns different from ret columns.')
        
        
        # tk uni
        self.tk = sorted(self.pv_cc_ret.columns.tolist())

        # first bar
        if bar_cache is None or bar_cache == '':
            self.first_bar = 30
        elif ~isinstance(bar_cache, int):
            raise Exception('bar_cache must be an int.')
        else:
            self.first_bar = bar_cache


    
        
        # signals
        self.pv_signals = signals.reindex(index = self.cdates, columns = self.tk)        
        
        # earnings date
            
        # any other matrices 
            
        
        # strat
        self.strat_func = strat_func
        
        
        # strat variables        
        self.pv_pstD_bo = self.h_create_zero_pv()
        self.pv_pstD_bc = self.h_create_zero_pv()
        self.pv_pstS_bo = self.h_create_zero_pv()
        self.pv_pstS_bc = self.h_create_zero_pv()
        
        self.pv_pstD_unfilled = self.h_create_zero_pv()
        
        self.pv_ordD_bo = self.h_create_zero_pv()
        self.pv_ordD_bc = self.h_create_zero_pv()
        self.pv_ordS_bo = self.h_create_zero_pv()
        self.pv_ordS_bc = self.h_create_zero_pv()
        
        self.pv_pnlD = self.h_create_zero_pv()
        
        self.pv_barsheld_since_pst_open = self.h_create_zero_pv() - 1
        self.pv_tbarsheld_since_pst_open = self.h_create_zero_pv() - 1
        
        self.pv_curr_pst_pnlD = self.h_create_zero_pv()
        
        self.vc_vD_quota = self.h_create_zero_vc()
        
        # state matrix
        self.dic_state = {}
        
        # reporting
        self.dic_report = {}
        
    def h_create_zero_pv(self):
        t0 = np.zeros([len(self.cdates),len(self.tk)])
        return pd.DataFrame(t0, index = self.cdates, columns = self.tk)
    def h_create_zero_vc(self):
        t0 = np.zeros(len(self.tk))
        return t0
    
    # ----- loop over strat -----
    def main(self):
        
        for row, num in self.pv_cc_ret.iterrows():
            
            # skip over the first few bars
            if num < self.first_bar:
                continue
            
            # carry on unfilled order from the previous bar
            self.pv_pstD_unfilled.loc[num,:] = self.pv_pstD_unfilled.loc[num-1,:]
            
            
            # carry on pst from the previous bar
            self.pv_pstD_bo.loc[num,:] = self.pv_pstD_bc.loc[num-1,:]
            
            # setup vD quota before filling orders
            
            self.vc_vD_quota = np.nan_to_num(self.pv_vD.loc[num,:]) * 0.02
            
            # fill ord @ bo
            #     update pst @ bo: yerterday bc pst + unfilled order + new ord             
            t_ord_bo = self.pv_ordD_bo.loc[num-1,:]+self.pv_pstD_unfilled.loc[num-1,:]
            t_abs_ord_bo = np.abs(t_ord_bo)
            t_allowed_abs_ord_bo = np.minimum(t_abs_ord_bo, self.vc_vD_quota)
            t_allowed_ord_bo = np.multiply(t_allowed_abs_ord_bo,np.sign(t_ord_bo))
            
            self.pv_pstD_bo.loc[num,:] = self.pv_pstD_bo.loc[num,:] + t_allowed_ord_bo
            
            #     update unfilled orders after market open
            self.pv_pstD_unfilled.loc[num,:] = t_ord_bo - t_allowed_ord_bo
            
            # update vD quota after bo ord
            self.vc_vD_quota = self.vc_vD_quota - t_allowed_abs_ord_bo

            # fill ord @ bc
            #     updte pst @ bc: today bo pst + unfilled order + new ord
            t_ord_bc = self.pv_ordD_bc.loc[num-1,:]+self.pv_pstD_unfilled.loc[num,:]
            t_abs_ord_bc = np.abs(t_ord_bc)
            t_allowed_abs_ord_bc = np.minimum(t_abs_ord_bc, self.vc_vD_quota)
            t_allowed_ord_bc = np.multiply(t_allowed_abs_ord_bc,np.sign(t_ord_bc))            
            
            self.pv_pstD_bc.loc[num,:] = self.pv_pstD_bo.loc[num,:] + t_allowed_ord_bc
            
            #     update unfilled orders after mc
            self.pv_pstD_unfilled.loc[num,:] = t_ord_bc - t_allowed_ord_bc
            
            # update vD quota after bo ord
            self.vc_vD_quota = self.vc_vD_quota - t_allowed_ord_bc
            
            # calc pnl for the pst opened @ bo
            self.pv_pnlD.loc[num,:] = self.pv_pnlD.loc[num,:] +\
                np.multiply(self.pv_pstD_bo.loc[num,:] - self.pv_pstD_bc.loc[num-1,:],\
                            self.pv_co_ret.loc[num,:])
                                            
            
            # calc pnl for the pst from yesterday
            self.pv_pnlD.loc[num,:] = self.pv_pnlD.loc[num,:] +\
                np.multiply(self.pv_pstD_bc.loc[num-1,:], self.pv_cc_ret.loc[num,:])
            
            # new or held pst / update curr pst pnl
            cond_new_or_held_pst = self.pv_pstD_bc.loc[num,:]!=0
            self.pv_curr_pst_pnlD.loc[num, cond_new_or_held_pst ] = \
                                        self.pv_curr_pst_pnlD.loc[num-1, cond_new_or_held_pst] +\
                                        self.pv_pnlD.loc[num, cond_new_or_held_pst ]
            
            # closed pst / clear curr pst pnl
            cond_closed_pst = (self.pv_pstD_bc.loc[num-1,:]!=0) & (self.pv_pstD_bc.loc[num,:]==0)
            self.pv_curr_pst_pnlD.loc[num, cond_closed_pst] = 0
            
            self.pv_curr_pst_pnlD = np.nan_to_num(self.pv_curr_pst_pnlD)
            
            # no. of calendar bars since holding pst
            cond_new_pst = (self.pv_pstD_mc.loc[num,:]!=0) & (self.pv_pstD_mc.loc[num-1,:]== 0)
            cond_new_pst = cond_new_pst  | \
                        (np.multiply(self.pv_pstD_mc.loc[num,:], self.pv_pstD_mc.loc[num-1,:])<0)
            self.pv_barsheld_since_pst_open.loc[num, cond_new_pst]  = 1
            
            cond_existing_pst = np.multiply(self.pv_pstD_mc.loc[num,:], self.pv_pstD_mc.loc[num-1,:])>0
            self.pv_barsheld_since_pst_open.loc[num, cond_existing_pst] = \
                                        self.pv_barsheld_since_pst_open.loc[num, cond_existing_pst] +1
            
            # no. of trading bars since holding pst
            self.pv_tbarsheld_since_pst_open.loc[num, cond_new_pst] = 1
            
            cond_existing_pst_and_v_notnan = cond_existing_pst & (~np.isnan(self.pv_vD.loc[num,:]))
            cond_existing_pst_and_v_isnan = cond_existing_pst & (np.isnan(self.pv_vD.loc[num,:]))
            self.pv_tbarsheld_since_pst_open.loc[num, cond_existing_pst_and_v_notnan ] = \
                self.pv_tbarsheld_since_pst_open.loc[num-1, cond_existing_pst_and_v_notnan] + 1
            self.pv_tbarsheld_since_pst_open.loc[num, cond_existing_pst_and_v_isnan ] = \
                self.pv_tbarsheld_since_pst_open.loc[num-1, cond_existing_pst_and_v_isnan]
            
            
            # days to earnings
            
            # strategy
            
            self.strat_func(self, num)
    
    def reporting(self):
        
        ####??? when reporting ... get rid of weekends!
        ####??? when reporting also consider getting rid of days when there are no trades
        
        self.pv_pnlD = self.pv_pnlD.fillna(0)
        
        # strat source code
        self.dic_report['sourcecode'] = inspect.source(self.strat_func)
        self.dic_report['params'] = locals()
        
        # pnl
        self.dic_report['pnl_tk'] = self.pv_pnlD
        self.dic_report['pnl_ptf'] = self.pv_pnlD.sum(axis = 1)
        
        self.dic_report['cumpnl_tk'] = self.pv_pnlD.cumsum(axis = 0)
        self.dic_report['cumpnl_ptf'] = self.pv_pnlD.cumsum(axis = 0).sum(axis = 1)
        
        # pst
        self.dic_report['pst_bo'] = self.pv_pstD_bo
        self.dic_report['pst_bc'] = self.pv_pstD_bc
        
        # sharpe
        self.dic_report['sharpe_tk'] = self.pv_pnlD.mean(axis = 0) / self.pv_pnlD.std(axis = 0) * np.sqrt(250)
        self.dic_report['sharpe_ptf'] = self.pv_pnlD.sum(axis = 1).mean(axis = 0) / self.pv_pnlD.sum(axis = 1).std(axis = 0) * np.sqrt(250)
        
        # plot
        self.dic_report['cumpnl_ptf'].plot()
        
        # print key results
        print(self.dic_report['sharpe_ptf'])
        
        # save results as bz'ed pickles
        pickle.dump(self.dic_report,open(r'C:\Users\tomyi\Desktop\Sync\1. Trading\7. Backtest and Trading Platform\syncere\log'))
        
        return self.dic_report
            
        
