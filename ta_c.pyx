cimport cython
import numpy as np
from numpy cimport ndarray, int_t, float64_t, long_t

cdef extern from "math.h":
    double sqrt(double m)


#cd C:\Users\tomyi\Anaconda\envs\py3\Lib\site-packages\yzhang
#python setup.py build_ext --inplace

@cython.boundscheck(False)
def cyOptStdDev(ndarray[float64_t, ndim=1] a not None):
#https://notes-on-cython.readthedocs.io/en/latest/std_dev.html
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef double m = 0.0
    for i in range(n):
        m += a[i]
    m /= n
    cdef double v = 0.0
    for i in range(n):
        v += (a[i] - m)**2
    return sqrt(v / n)

def cyOptMean(ndarray[float64_t, ndim=1] a not None):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef double m = 0.0
    for i in range(n):
        m += a[i]
    m /= n
    return m

@cython.boundscheck(False)
@cython.wraparound(False)
def zigzag_c(ndarray[long_t, ndim=1]  ts_date, ndarray[float64_t, ndim=1] ts_high, 
             ndarray[float64_t, ndim=1]  ts_low, ndarray[float64_t, ndim=1]  ts_close, 
             str how , double reverse_pct, 
             Py_ssize_t window , double percent_std ):
    


# any s_* variables are numpy arrays.
# how = static / dyanmic
    
    
  
    # Sanity check    
    
    if len(ts_date) <= window * 1.5:
        raise Exception('Input data length too short.')
        
    
    # Set up key parameters
        
    cdef ndarray[int_t, ndim=1] ts_index #This one cannot be Py_ssize_t, it has to be int_t
    cdef int_t state_trend
    
    ts_index = np.array(range(len(ts_close)))
    state_trend = 9

    
    # Decide sensitivity parameters and Set up other parameters
    
    cdef Py_ssize_t state_last_index   #ok
    cdef double state_last_price
    cdef list o_index
    cdef list o_ts
    cdef list o_std
    cdef list o_trend
    

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
        o_std = [reverse_pct]
        o_trend = [0]


    # Loop
        
    cdef double up_state_trend
    cdef double down_state_trend
    cdef Py_ssize_t i_index  #ok
    cdef double i_high
    cdef double i_low
    
    cdef Py_ssize_t len_ts_index = len(ts_index) 
      
    cdef Py_ssize_t i
    
    for i in range(len_ts_index):
        
        i_index, i_high, i_low = ts_index[i], ts_high[i], ts_low[i]   
            
        # Update reverse_pct if dynamic
        
        if how == 'dynamic':
            
            if i_index < window-1:
                continue
            
            reverse_pct = cyOptStdDev(ts_close[i_index-window+1:i_index+1]) / cyOptMean(ts_close[i_index-window+1:i_index+1]) * 100 * percent_std
            
            up_state_trend = 1 + reverse_pct / 100
            down_state_trend = 1 - reverse_pct / 100
                        
        else:
            
            up_state_trend = 1 + reverse_pct / 100
            down_state_trend = 1 - reverse_pct / 100
    
        
        # No initial trend
        if state_trend == 9:
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
                o_std.append(reverse_pct)
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
                o_std.append(reverse_pct)
                o_trend.append(-1)

                state_trend, state_last_index, state_last_price = 1, i_index, i_high


    # Extrapolate the current state_trend
    cdef Py_ssize_t len_o_index = len(o_index) ##############3
    
    
    if o_index[len_o_index-1] != ts_index[len_ts_index-1]:
        o_index.append(ts_index[len_ts_index-1])
        len_o_index += 1
        
        if state_trend == 9:
            o_ts.append(ts_close[o_index[len_o_index-1]])
        elif state_trend == 1:
            o_ts.append(ts_high[o_index[len_o_index-1]])
            o_trend.append(1)
        else:
            o_ts.append(ts_low[o_index[len_o_index-1]])
            o_trend.append(-1)
    
    # format and shapes
            
    cdef ndarray[float64_t, ndim=2] o_ts_np
    cdef ndarray[int_t, ndim=2] o_trend_np
    
    o_ts_np = np.array(o_ts).reshape((len(o_ts),1))
    o_trend_np = np.array(o_trend).reshape((len(o_trend),1))
    
    
    return ts_date[o_index].reshape((len(ts_date[o_index]),1)), o_ts_np, o_trend_np ,o_std
    


@cython.boundscheck(False)
@cython.wraparound(False)
def sr_point_c(ndarray[long_t, ndim=1]  ts_date, ndarray[float64_t, ndim=1] ts_high, 
             ndarray[float64_t, ndim=1]  ts_low, ndarray[float64_t, ndim=1]  ts_close,              
             str how = 'static' , double reverse_pct = 5, 
             int_t window = 50, double percent_std = 0.3, double percent_range = 0.1,
             str type = 'peak', int_t extrema_lookback = 12,
             double breakout = 1.7):

    
    # Step 0 - Define output dict
    
    cdef dict o_dic = {'identified':[],'sr_high': None, 'sr_low': None, 'sr_high_breakout': None, 'sr_low_breakout': None}
    cdef dict o_debug = {i: '' for i in range(20)}

    
    # Step 2 - Get zigzag
    
    cdef ndarray[long_t, ndim=2] zigzag_ts
    cdef ndarray[float64_t, ndim=2] zigzag_price
    cdef ndarray[int_t, ndim=2] zigzag_trend
    
    try:
        zigzag_ts, zigzag_price, zigzag_trend,_ = zigzag_c(ts_date, ts_high, ts_low, ts_close, 
                                                        window = window, how = how, percent_std = percent_std, reverse_pct=reverse_pct)
    except Exception as e:
        if str(e) == 'Input data length too short.':
            return o_dic, o_debug
        else:
            raise Exception(e)
    
    if len(zigzag_ts) < 10:
        return o_dic, o_debug
    
    
    
    # Step 3 - Scrub zigzag line segments
    
    cdef list t_current_trend 
    
    t_current_trend = [zigzag_ts[len(zigzag_ts)-1], zigzag_price[len(zigzag_price)-1], zigzag_trend[len(zigzag_trend)-1]]
    
    zigzag_ts =  zigzag_ts[len(zigzag_ts)-extrema_lookback-1:len(zigzag_ts)-1]
    zigzag_price = zigzag_price[len(zigzag_price)-extrema_lookback-1:len(zigzag_price)-1]
    zigzag_trend = zigzag_trend[len(zigzag_trend)-extrema_lookback-1:len(zigzag_trend)-1]
    
    cdef ndarray[float64_t, ndim=1] t_peak_price
    cdef ndarray[float64_t, ndim=1] t_trough_price
    cdef ndarray[long_t, ndim=1] t_peak_ts
    cdef ndarray[long_t, ndim=1] t_trough_ts
    
    t_peak_price = zigzag_price[zigzag_trend == 1]
    t_trough_price = zigzag_price[zigzag_trend == -1]
    t_peak_ts = zigzag_ts[zigzag_trend == 1]
    t_trough_ts = zigzag_ts[zigzag_trend == -1]
    
       
    
    # Step 4 - Output
    
    
    
    cdef Py_ssize_t len_p = len(t_peak_price)
    cdef Py_ssize_t len_t = len(t_trough_price)
    cdef Py_ssize_t len_ts = len(ts_high)
    
    cdef double t_tolerance = (ts_high[len_ts-window:len_ts].max() - ts_low[len_ts-window:len_ts].min()) / \
                                ts_close[len_ts-1] * percent_range  
        
    
    # Check SR levels by High 
            
    
    if ((np.sort(np.absolute(t_peak_price[len_p-4:len_p-2]-t_peak_price[len_p-1]))[:1].sum() + \
        abs(t_peak_price[len_p-2]-t_peak_price[len_p-1])) / t_peak_price[len_p-1] < t_tolerance) & \
        ((np.absolute(t_peak_price[len_p-4:len_p-2]-t_peak_price[len_p-1])).max() / \
        t_peak_price[len_p-1] < t_tolerance):
        
        o_dic['sr_high'] = [t_peak_ts[len_p-1], t_peak_price[len_p-1], [t_peak_price]]
        o_dic['identified'] = o_dic['identified'] + ['sr_high']
        
    else:
        o_debug[0] = t_tolerance
        o_debug[1] = (np.sort(np.absolute(t_peak_price[len_p-4:len_p-2]-t_peak_price[len_p-1]))[:1].sum() + \
                      abs(t_peak_price[len_p-2]-t_peak_price[len_p-1])) / t_peak_price[len_p-1]
        o_debug[2] = (np.absolute(t_peak_price[len_p-4:len_p-2]-t_peak_price[len_p-1])).max() / \
                      t_peak_price[len_p-1] 
    
    
    # Check SR levels by Low
        
        
    if ((np.sort(np.absolute(t_trough_price[len_t-4:len_t-2]-t_trough_price[len_t-1]))[:1].sum() + \
        abs(t_trough_price[len_t-2] - t_trough_price[len_t-1])) / t_trough_price[len_t-1] < t_tolerance) & \
        ((np.absolute(t_trough_price[len_t-4:len_t-2]-t_trough_price[len_t-1])).max() / \
        t_trough_price[len_t-1] < t_tolerance):
        
        o_dic['sr_low'] = [t_trough_ts[len_p-1], t_trough_price[len_p-1], [t_trough_price]]
        o_dic['identified'] = o_dic['identified'] + ['sr_low']
        
    else:
        o_debug[10] = [t_tolerance, len_t, len(t_trough_price) ]
        o_debug[11] = (np.sort(np.absolute(t_trough_price[len_t-4:len_t-2]-t_trough_price[len_t-1]))[:1].sum() + \
                      abs(t_trough_price[len_t-2] - t_trough_price[len_t-1])) / t_trough_price[len_t-1]
        o_debug[12] = (np.absolute(t_trough_price[len_t-4:len_t-2]-t_trough_price[len_t-1])).max() / \
                      t_trough_price[len_t-1]
        o_debug[13] = t_trough_price
        o_debug[14] = np.sort(np.absolute(t_trough_price[len_t-4:len_t-2]-t_trough_price[len_t-1]))[:1].sum()
        o_debug[15]  = abs(t_trough_price[len_t-2] - t_trough_price[len_t-1])
    
    # Find meaningful upward breakouts
    cdef double t_avg_line_segment1 = (abs(t_peak_price[len_p-1] - t_trough_price[len_p-1]) + 
                                abs(t_trough_price[len_p-2] - t_peak_price[len_p-1]) + 
                                abs(t_peak_price[len_p-2] - t_trough_price[len_p-2]) + 
                                abs(t_trough_price[len_p-3] - t_peak_price[len_p-2]) ) / 4.0 

    
    # if (t_current_trend[2] == 1
    #     )&(
    #     abs(t_current_trend[1] - t_trough_price[len_p-1]) > t_avg_line_segment1 * breakout
    #     )&(
    #     (np.absolute(t_peak_price[len_p-3:len_p-1]-t_peak_price[len_p-1])).sum() / t_peak_price[len_p-1]< t_tolerance*3
    #     )&(
    #     (np.absolute(t_trough_price[len_p-3:len_p-1]-t_trough_price[len_p-1])).sum() / t_trough_price[len_p-1]< t_tolerance*5
    #     )&(
    #     abs(t_current_trend[1] - t_peak_price[len_p-1]) > t_avg_line_segment1 * 0.3
    #     ):
    # current line segment > average line segments * breakout
    # sum of past peak deviation < tolerance * 3
    # sum of past trough deviation < tolerance * 5
    # current line segment passes previous peak by average segment * 0.3
    
    if  (t_current_trend[2] == 1
        )&(
        (t_current_trend[1] - t_trough_price[len_t-1]) * 0.25 < t_current_trend[1]-t_peak_price[len_p-3:len_p].max() 
        )&(
        abs(t_peak_price[len_p-1] - t_peak_price[len_p-2]) < (t_current_trend[1] - t_trough_price[len_t-1]) * 0.3
        )&(
        abs(t_trough_price[len_p-1] - t_trough_price[len_p-2]) < (t_current_trend[1] - t_trough_price[len_t-1]) * 0.3
        ):
        
        # current price over max peak > 0.25 current line segment
        # peak differences < 0.3 * current line segment
        # trough difference < 0.3 * current line segment
                    
        o_dic['sr_high_breakout'] = t_current_trend
            
    o_debug[0] = [0 < t_current_trend[1]-t_peak_price[len_p-3:len_p].max() < (t_current_trend[1] - t_trough_price[len_t-1]) * 0.6,
                  abs(t_peak_price[len_p-1] - t_peak_price[len_p-2]) < (t_current_trend[1] - t_trough_price[len_t-1]) * 0.2 ,
                  abs(t_trough_price[len_p-1] - t_trough_price[len_p-2]) < (t_current_trend[1] - t_trough_price[len_t-1]) * 0.25 ,
                  t_current_trend[1], t_peak_price[len_p-3:len_p].max(), (t_current_trend[1] - t_trough_price[len_t-1]) ]
                  
                  
    
    # Find meaningful downward breakouts
    cdef double t_avg_line_segment2 = (abs(t_peak_price[len_p-1] - t_trough_price[len_p-1]) + 
                                abs(t_trough_price[len_p-1] - t_peak_price[len_p-2]) + 
                                abs(t_peak_price[len_p-2] - t_trough_price[len_p-2]) + 
                                abs(t_trough_price[len_p-2] - t_peak_price[len_p-3]) ) / 4.0             
            
    # if (t_current_trend[2] == -1
    #     )&(
    #     abs(t_current_trend[1] - t_peak_price[len_p-1]) > t_avg_line_segment2 * breakout
    #     )&(
    #     (np.absolute(t_trough_price[len_p-3:len_p-1]-t_trough_price[len_p-1])).sum() / t_trough_price[len_p-1]< t_tolerance*5
    #     )&(
    #     abs(t_current_trend[1] - t_trough_price[len_p-1]) > t_avg_line_segment2 * 0.3
    #     ):            
    # current line segment > average line segments
    # sum of past trough deviation < tolerance * 5
    # current line segment passes previous trough by average segment * 0.3             
    
                
    if  (t_current_trend[2] == -1
        )&(
        (- t_current_trend[1] + t_peak_price[len_t-1]) * 0.25 < - t_current_trend[1] + t_trough_price[len_t-3:len_t].max() 
        )&(
        abs(t_peak_price[len_p-1] - t_peak_price[len_p-2]) < (- t_current_trend[1] + t_trough_price[len_t-1]) * 0.3
        )&(
        abs(t_trough_price[len_p-1] - t_trough_price[len_p-2]) < (- t_current_trend[1] + t_trough_price[len_t-1]) * 0.3
        ):
                
        # current price over min trough > 0.25 current line segment
        # peak differences < 0.3 * current line segment
        # trough difference < 0.3 * current line segment                
        
                
        o_dic['sr_low_breakout'] = t_current_trend
            
    o_debug[1] = [abs(t_current_trend[1] - t_peak_price[len_p-1]) > t_avg_line_segment2 * 1.2,
                          (np.absolute(t_trough_price[len_p-3:len_p-1]-t_trough_price[len_p-1])).sum() / t_trough_price[len_p-1]< t_tolerance*5,
                          t_current_trend[1] - t_trough_price[len_p-1] > t_avg_line_segment2 * 0.3,
                          t_current_trend[1], 
                          t_peak_price[len_p-1],
                          t_avg_line_segment2,]
    
    return o_dic, o_debug
