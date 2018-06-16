import numpy as np
from scipy import optimize
from scipy import interpolate
from matplotlib import pyplot as plt

def getPeaksOf(y,num_peaks,x_threshold):
    indices = np.argpartition(y,len(y) - num_peaks)[-num_peaks:]
    indices = np.sort(indices)
    trimmed = []
    trimmed.append(indices[0])
    for i in indices:
        if i - trimmed[-1] < x_threshold:
            if y[trimmed[-1]] > y[i]: pass
            else: trimmed[-1] = i
        else: trimmed.append(i)
    return np.array(trimmed)

def get_exact_peaks(y,num_peaks,x_threshold):
    print("New impl")
    indices = np.argsort(y)[::-1]
#    indices = np.sort(indices)
    trimmed = []
    trimmed.append(indices[0])
    i = 1
    while len(trimmed) < num_peaks and i < len(y):
        flag = True
        for peak in trimmed:
            if abs(peak - indices[i]) < x_threshold:
                flag = False
        if flag:
            trimmed.append(indices[i])
        i += 1
    return np.array(trimmed)

def get_peaks_above(y,x_threshold,y_threshold):
    print("New impl")
    indices = np.argsort(y)[::-1]
#    indices = np.sort(indices)
    trimmed = []
    trimmed.append(indices[0])
    i = 1
    f1 = True
    while f1 and i < len(y):
        flag = True
        for peak in trimmed:
            if abs(peak - indices[i]) < x_threshold:
                flag = False
        if flag:
            if y[indices[i]] > y_threshold:
                trimmed.append(indices[i])
            else:
                f1 = False
        i += 1
    return np.array(trimmed)

def findCorrespondingPeaks(peaks1,x,y,window=3):
    peaks2 = np.zeros_like(peaks1)
    for i in range(len(peaks1)):
        ind = peaks1[i]
        a = max(ind-window,0)
        b = min(ind+window,len(y)-1)
        s = interpolate.UnivariateSpline(x,-y)
        s.set_smoothing_factor(0)
        maxx = optimize.brent(s,brack=(x[a],x[b]))
        peaks2[i] = np.searchsorted(x,[maxx])
    return peaks2

def plot_maxes(xx,yy,inds):
    for ind in inds:
        x = xx[ind]
        y = yy[ind]
        plt.plot(x,y,'+',markersize=20.0)

def get_all(curves,num_peaks,r_ratio,engine,radius,plotting = True):
    counter = 1
    ret = []
    for curve in curves:
        ret.append(getDiffs(curve,num_peaks,radius,engine,r_ratio,plotting))
        if plotting:
            plt.title('Curve' + str(counter))
        counter += 1
    return ret

def getDiffs(curve,num_peaks,radius,engine,r_ratio,with_plotting = True):
    x,y1 = curve.plottable('uas')
    xv = x.value
    qpts = curve.query_points
    y2 = eng.query_line(qpts,radius*r_ratio)
    x_threshold = int(3/(xv[1]-xv[0]))
    peaks1 = getPeaksOf(y1,num_peaks,x_threshold)
    peaks2 = findCorrespondingPeaks(peaks1,xv,y2)
    if with_plotting:
        plt.figure()
        plt.plot(x,y1)
        plt.plot(x,y2)
        plot_maxes(xv,y1,peaks1)
        plot_maxes(xv,y2,peaks2)
    diffs = np.ones_like(peaks1,dtype=float)
    for i in range(len(peaks1)):
        diffs[i] = xv[peaks1[i]] - xv[peaks2[i]]
    return diffs

def peak_find(retmp,filenames,x_threshold=300,y_threshold=8):
    for file in filenames:
        data = np.load(file)
        x = np.arange(0,data.shape[1])
        peaks = get_peaks_above(data[0],x_threshold,y_threshold)
        num_peaks = len(peaks)
        ret_list = []
        for i in range(0,data.shape[0]):
            peaks = get_exact_peaks(data[i],num_peaks,x_threshold)
            sortp = np.sort(peaks)
            ret_list.append(sortp)
        retmp[file] = ret_list

def sortByHeightAtIndex(indices,y):
    indices = np.sort(indices)
    keys = np.arange(0,len(indices),dtype=np.int32)
    for i in range(len(indices)):
        for j in range(i,len(indices)):
            if y[indices[i]] < y[indices[j]]:
                tmp = indices[i]
                indices[i] = indices[j]
                indices[j] = tmp
                tmp2 = keys[i]
                keys[i] = keys[j]
                keys[j] = tmp2
    return keys