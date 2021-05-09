from __future__ import division, absolute_import, print_function

import numpy as np
import pandas as pd
import scipy as sp
import scipy.signal


def _ensure_list(data):
    if type(data) is not list:
        data = [data]
    return data


'''
PEAKS
'''


def find_peaks(data, distance, inv=False):
    if inv:
        peaks, _ = sp.signal.find_peaks(1./data, distance=distance)
    else:
        peaks, _ = sp.signal.find_peaks(data, distance=distance)
    return peaks


def find_peaks_savgol(data, distance, inv=False, polyorder=3):
    # distance needs to be an odd int
    if distance % 2 == 0:
        distance = distance + 1
    # smooth data
    if inv:
        s = scipy.signal.savgol_filter(1/data, distance, polyorder)
    else:
        s = scipy.signal.savgol_filter(data, distance, polyorder)
    # get peaks
    peaks = scipy.signal.argrelmax(s)[0]
    return peaks


'''
SUPPORT RESISTANCE
'''


def support_resistance(ltp, n):
    '''
    This function takes a numpy array of last traded price
    and returns a list of support and resistance levels
    respectively. n is the number of entries to be scanned.

    Params:
        - ltp: list with data (close)
        - n: smooth period (distance)

    Returns:
        - support: Support levels
        - resistance: Resistance levels
    '''
    from scipy.signal import savgol_filter as smooth

    # converting n to a nearest even number
    if n % 2 != 0:
        n += 1

    n_ltp = ltp.shape[0]
    # smoothening the curve
    ltp_s = smooth(ltp, int(n+1), 3)

    # taking a simple derivative
    ltp_d = np.zeros(n_ltp)
    ltp_d[1:] = np.subtract(ltp_s[1:], ltp_s[:-1])

    resistance = []
    support = []

    for i in range(n_ltp - n):
        arr_sl = ltp_d[i:int(i+n)]
        first = arr_sl[:int(n/2)]  # first half
        last = arr_sl[int(n/2):]   # second half

        r_1 = np.sum(first > 0)
        r_2 = np.sum(last < 0)

        s_1 = np.sum(first < 0)
        s_2 = np.sum(last > 0)

        # local maxima detection
        if (r_1 == (n/2)) and (r_2 == int(n/2)):
            resistance.append(ltp[i+(int(n/2)-1)])

        # local minima detection
        if (s_1 == int(n/2)) and (s_2 == int(n/2)):
            support.append(ltp[i+(int(n/2)-1)])

    return support, resistance


'''
TRENDY TRENDS
'''


def segtrends(x, segments=2):
    '''
    Turn minitrends to iterative process more easily adaptable to
    implementation in simple trading systems; allows backtesting functionality.

    Arguments:
    x -- One-dimensional data set
    segments -- (Default 2)

    Example:
    import matplotlib.pyplot as plt

    x_maxima, maxima, x_minima, minima = segtrends(x, segments=segments)
    plt.plot(x)
    plt.grid(True)
    for i in range(0, segments - 1):
        maxslope = ((maxima[i + 1] - maxima[i])
                    / (x_maxima[i + 1] - x_maxima[i]))
        a_max = maxima[i] - (maxslope * x_maxima[i])
        b_max = maxima[i] + (maxslope * (len(x) - x_maxima[i]))
        maxline = np.linspace(a_max, b_max, len(x))

        minslope = ((minima[i + 1] - minima[i])
                    / (x_minima[i+1] - x_minima[i]))
        a_min = minima[i] - (minslope * x_minima[i])
        b_min = minima[i] + (minslope * (len(x) - x_minima[i]))
        minline = np.linspace(a_min, b_min, len(x))
        plt.plot(maxline, "g")
        plt.plot(minline, "r")
    plt.show()
    '''
    x = np.array(x)

    # Implement trendlines
    segments = int(segments)
    segsize = int(len(x) / segments)
    maxima = np.ones(segments)
    minima = np.ones(segments)
    x_maxima = np.ones(segments)
    x_minima = np.ones(segments)
    for i in range(1, segments + 1):
        ind2 = i * segsize
        ind1 = ind2 - segsize
        maxima[i-1] = max(x[ind1:ind2])
        minima[i-1] = min(x[ind1:ind2])
        x_maxima[i-1] = np.where(x[ind1:ind2] == maxima[i-1])[0][0] + ind1
        x_minima[i-1] = np.where(x[ind1:ind2] == minima[i-1])[0][0] + ind1

    for i in range(1, segments+1):
        ind2 = i * segsize
        ind1 = ind2 - segsize

    return x_maxima, maxima, x_minima, minima


def gentrends(x, window=1/3.0):
    '''
    Returns a Pandas dataframe with support and resistance lines.

    Arguments:
    x -- One-dimensional data set
    window -- How long the trendlines should be. If window < 1, then
              it will be taken as a percentage of the size of the
              data (Default 1/3.)

    Example:
    import matplotlib.pyplot as plt

    trends, maxslope, minslope = gentrends(x, window=window)
    plt.plot(trends)
    plt.grid()
    plt.show()
    '''

    x = np.array(x)

    if window < 1:
        window = int(window * len(x))

    max1 = np.where(x == max(x))[0][0]  # find the index of the abs max
    min1 = np.where(x == min(x))[0][0]  # find the index of the abs min

    # First the max
    if max1 + window >= len(x):
        max2 = max(x[0:max(1, (max1 - window))])
    else:
        max2 = max(x[(max1 + window):])

    # Now the min
    if min1 - window < 0:
        min2 = min(x[(min1 + window):])
    else:
        min2 = min(x[0:max(1, (min1 - window))])

    # Now find the indices of the secondary extrema
    max2 = np.where(x == max2)[0][0]  # find the index of the 2nd max
    min2 = np.where(x == min2)[0][0]  # find the index of the 2nd min

    # Create & extend the lines

    # slope between max points
    if max1 - max2 != 0:
        maxslope = (x[max1] - x[max2]) / (max1 - max2)
    else:
        maxslope = x[max1] - x[max2]
    # slope between min points
    if min1 - min2 != 0:
        minslope = (x[min1] - x[min2]) / (min1 - min2)
    else:
        minslope = x[min1] - x[min2]
    aMax = x[max1] - (maxslope * max1)  # y-intercept for max trendline
    aMin = x[min1] - (minslope * min1)  # y-intercept for min trendline
    bMax = x[max1] + (maxslope * (len(x) - max1))  # extend to last data pt
    bMin = x[min1] + (minslope * (len(x) - min1))  # extend to last data point
    maxline = np.linspace(
            aMax,
            bMax,
            len(x),
            endpoint=False)  # Y values between max's
    minline = np.linspace(
            aMin,
            bMin,
            len(x),
            endpoint=False)  # Y values between min's

    trends = np.transpose(np.array((x, maxline, minline)))
    trends = pd.DataFrame(trends, index=np.arange(0, len(x)),
                          columns=["Data", "Max Line", "Min Line"])

    return trends, maxslope, minslope


def minitrends(x, window=20):
    '''
    Turn minitrends to iterative process more easily adaptable to
    implementation in simple trading systems; allows backtesting
    functionality.

    Arguments:
    x -- One-dimensional data set
    window -- How long the trendlines should be. If window < 1, then
              it will be taken as a percentage of the size of the
              data (Default 20)

    Example:
    import matplotlib.pyplot as plt

    trends, maxslope, minslope = gentrends(x, window=window)
    plt.plot(trends)
    plt.grid()
    plt.show()
    '''

    y = np.array(x)
    if window < 1:  # if window is given as fraction of data length
        window = float(window)
        window = int(window * len(y))
    x = np.arange(0, len(y))
    dy = y[window:] - y[:-window]
    crit = dy[:-1] * dy[1:] < 0

    xmax = np.array([])
    xmin = np.array([])

    # Find whether max's or min's
    for i, val in enumerate(crit):
        if val is True:
            if (y[i] - y[i + window] > 0) and (y[i] - y[i - window] > 0):
                xmax = np.append(xmax, i)
            if (y[i] - y[i + window] < 0) and (y[i] - y[i - window] < 0):
                xmin = np.append(xmin, i)
    xmax = xmax.astype(int)
    xmin = xmin.astype(int)

    # See if better max or min in region
    yMax = np.array([])
    xMax = np.array([])
    for i in xmax:
        indx = np.where(xmax == i)[0][0] + 1
        try:
            Y = y[i:xmax[indx]]
            yMax = np.append(yMax, Y.max())
            xMax = np.append(xMax, np.where(y == yMax[-1])[0][0])
        except Exception:
            pass
    yMin = np.array([])
    xMin = np.array([])
    for i in xmin:
        indx = np.where(xmin == i)[0][0] + 1
        try:
            Y = y[i:xmin[indx]]
            yMin = np.append(yMin, Y.min())
            xMin = np.append(xMin, np.where(y == yMin[-1])[0][0])
        except Exception:
            pass
    if y[-1] > yMax[-1]:
        yMax = np.append(yMax, y[-1])
        xMax = np.append(xMax, x[-1])
    if y[0] not in yMax:
        yMax = np.insert(yMax, 0, y[0])
        xMax = np.insert(xMax, 0, x[0])
    if y[-1] < yMin[-1]:
        yMin = np.append(yMin, y[-1])
        xMin = np.append(xMin, x[-1])
    if y[0] not in yMin:
        yMin = np.insert(yMin, 0, y[0])
        xMin = np.insert(xMin, 0, x[0])

    # Return arrays of critical points
    return xMin, yMin, xMax, yMax


def iterlines(x, window=20):
    '''
    Turn minitrends to iterative process more easily adaptable to
    implementation in simple trading systems; allows backtesting functionality.

    Arguments:
    x -- One-dimensional data set
    window -- How long the trendlines should be. If window < 1, then
              it will be taken as a percentage of the size of the
              data (Default 20)

    Example:
    import matplotlib.pyplot as plt

    sigs, xMin, yMin, xMax, yMax = iterlines(x, window=window)

    plt.plot(x)
    plt.plot(xMin, yMin, "ro")
    plt.plot(xMax, yMax, "go")
    plt.grid(True)
    plt.show()
    '''
    x = np.array(x)
    n = len(x)
    if window < 1:
        window = int(window * n)
    sigs = np.zeros(n, dtype=float)

    i = window
    while i != n:
        if x[i] > max(x[i-window:i]):
            sigs[i] = 1
        elif x[i] < min(x[i-window:i]):
            sigs[i] = -1
        i += 1

    xMin = np.where(sigs == -1.0)[0]
    xMax = np.where(sigs == 1.0)[0]
    yMin = x[xMin]
    yMax = x[xMax]

    return sigs, xMin, yMin, xMax, yMax


'''
PIVOT POINTS
'''


def pivot_points(highList, lowList, closeList):
    '''
    Returns the standard pivot points, three support levels (s1,s2 and s3)
    and three resistance levels (r1, r2 and r3) of the
    given data series.
    These values for a given day are calculated based on the day before
    so expect n values as output for a given list of n days.

    Standard Pivot Points begin with a base Pivot Point. This is a simple
    average of the high, low and close. The middle Pivot Point is shown as
    a solid line between the support and resistance pivots. Keep in mind that
    the high, low and close are all from the prior period.

    Params:
            - highList: list of high values
            - lowList: list of low values
            - closeList: list of closing values
    Returns:
            - p: pivot point
            - s1: support first point
            - s2: support second point
            - s3: support third point
            - r1: resistance first point
            - r2: resistance second point
            - r3: resistence third point
    '''
    # ensure np array is being used
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))
    closeList = np.array(_ensure_list(closeList))

    # calculation
    p = (highList + lowList + closeList) / 3
    s1 = (2 * p) - highList
    s2 = p - highList + lowList
    s3 = s1 - highList + lowList
    r1 = (2 * p) - lowList
    r2 = p + highList - lowList
    r3 = r1 + highList - lowList

    # return lists with results
    return p, s1, s2, s3, r1, r2, r3


def tom_demark_points(openList, highList, lowList, closeList):
    '''
    Returns the Tom Demark points, the predicted low and highs
    of the period.
    These values for a given day are calculated based on the day before
    so expect n values as output for a given list of n days.

    Demark Pivot Points start with a different base and use different
    formulas for support and resistance. These Pivot Points are conditional
    on the relationship between the close and the open.

    If Close < Open, then X = High + (2 x Low) + Close
    If Close > Open, then X = (2 x High) + Low + Close
    If Close = Open, then X = High + Low + (2 x Close)

    Pivot Point (P) = X/4
    Support 1 (S1) = X/2 - High
    Resistance 1 (R1) = X/2 - Low

    Params:
            - openList: list of open values
            - highList: list of high values
            - lowList: list of low values
            - closeList: list of closing values
    Returns:
            - p: Pivot point
            - r1: Resistance 1
            - s1: Support 1
    '''
    # ensure np array is being used
    openList = np.array(_ensure_list(openList))
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))
    closeList = np.array(_ensure_list(closeList))

    # calculation
    p = []
    s1 = []
    r1 = []
    for o, h, l, c in np.nditer([openList, highList, lowList, closeList]):
        if c < o:
            x = h + (2 * l) + c
        elif c > o:
            x = (2 * h) + l + c
        elif c == o:
            x = h + l + (2 * c)
        p.append(x / 4)
        s1.append((x / 2) - h)
        r1.append((x / 2) - l)

    # return lists with results
    return p, s1, r1


def woodies_points(highList, lowList, closeList):
    '''
    Returns the Woodies points: pivot, supports (s1 and s2) and
    resistance values (r1 and r2).
    These values for a given day are calculated based on the day before
    so expect n values as output for a given list of n days.
     *         - p: pivot value.
     *
    Params:
            - highList: list of high values
            - lowList: list of low values
            - closeList: list of closing values
    Returns:
            - pl: pivot level
            - s1: support (s1)
            - s2: secondary support (s2)
            - r1: resistance (r1)
            - r2: secondary resistance (r2)
    '''
    # ensure np array is being used
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))
    closeList = np.array(_ensure_list(closeList))

    # calculation
    p = (highList + lowList + 2 * closeList) / 4
    s1 = (2 * p) - highList
    s2 = p - highList + lowList
    r1 = (2 * p) - lowList
    r2 = p + highList - lowList

    # return lists with results
    return p, s1, s2, r1, r2


def camarilla_points(highList, lowList, closeList):
    '''
    Returns the Camarilla points: supports (s1,s2,3 and s4)) and
    resistance values (r1, r2, r3 and r4).

    Params:
            - highList: list of high values
            - lowList: list of low values
            - closeList: list of closing values
    Returns:
            - s1: s1 support
            - s2: s2 support
            - s3: s3 support
            - s4: s4 support
            - r1: r1 resistance
            - r2: r2 resistance
            - r3: r3 resistance
            - r4: r4 resistance
    '''
    # ensure np array is being used
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))
    closeList = np.array(_ensure_list(closeList))

    # calculation
    diff = highList - lowList
    s1 = closeList - (diff * 1.1 / 12)
    s2 = closeList - (diff * 1.1 / 6)
    s3 = closeList - (diff * 1.1 / 4)
    s4 = closeList - (diff * 1.1 / 2)
    r1 = ((diff * 1.1) / 12) + closeList
    r2 = ((diff * 1.1) / 6) + closeList
    r3 = ((diff * 1.1) / 4) + closeList
    r4 = ((diff * 1.1) / 2) + closeList

    # return lists with results
    return s1, s2, s3, s4, r1, r2, r3, r4


def fibanocci_points(highList, lowList, closeList):
    '''
    Returns the fibanocci points: supports (s1,s2,3)) and
    resistance values (r1, r2, r3).

    Params:
            - highList: list of high values
            - lowList: list of low values
            - closeList: list of closing values
    Returns:
            - p: pivot point
            - s1: s1 support
            - s2: s2 support
            - s3: s3 support
            - r1: r1 resistance
            - r2: r2 resistance
            - r3: r3 resistance
    '''
    # ensure np array is being used
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))
    closeList = np.array(_ensure_list(closeList))

    # calculation
    p = (highList + lowList + closeList) / 3
    s1 = p - (0.382 * (highList - lowList))
    s2 = p - (0.618 * (highList - lowList))
    s3 = p - (1.0 * (highList - lowList))
    r1 = p + (0.382 * (highList - lowList))
    r2 = p + (0.618 * (highList - lowList))
    r3 = p + (1.0 * (highList - lowList))

    # return lists with results
    return p, s1, s2, s3, r1, r2, r3


def fibonacci_retracements(highList, lowList):
    '''
    Returns the fibanocci retracements.

    Params:
            - highList: list of high values
            - lowList: list of low values
    Returns:
            - upTrend
            - downTrend
    '''
    # ensure np array is being used
    highList = np.array(_ensure_list(highList))
    lowList = np.array(_ensure_list(lowList))

    # calculation
    retracements = [1, 0.618, 0.5, 0.382, 0.236, 0]
    diff = highList - lowList
    upTrend = []
    downTrend = []

    for d, h, l in np.nditer([diff, highList, lowList]):
        up = h - d * retracements
        do = l + d * retracements
        upTrend.append(up)
        downTrend.append(do)

    # return lists with results
    return upTrend, downTrend
