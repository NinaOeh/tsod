import numpy as np

'''
GAUSSIAN_SCALE_FACTOR = k = 1/Phi^(-1)(3/4)
Choosing 3/4 as argument makes +-MAD cover 50% of the standard normal cumulative distribution function.
'''
GAUSSIAN_SCALE_FACTOR = 1.4826


def median_absolute_deviation(x):
    """ Calculate median absolute deviation (MAD) from the window's median. """
    return np.median(np.abs(x - np.median(x)))


def filter(time_series, window_size=5, threshold=3, k=GAUSSIAN_SCALE_FACTOR):
    """ Detect and filter out outliers using the Hampel filter.
        Based on https://github.com/MichaelisTrofficus/hampel_filter

    Parameters
    ----------
    threshold : float
        threshold, default is 3 (Pearson's rule)
    window_size : int
        total window size will be computed as 2*window_size + 1
    time_series : pd.Series
    k : float
        Constant scale factor dependent on distribution. Default is normal distribution.
    """

    validate_arguments(window_size, threshold)

    time_series_clean = time_series.copy()
    is_outlier, outlier_indices, rolling_median = detect(time_series_clean, window_size, threshold, k)
    time_series_clean[list(outlier_indices)] = rolling_median[list(outlier_indices)]

    return is_outlier, outlier_indices, time_series_clean


def detect(time_series, window_size, threshold, k=GAUSSIAN_SCALE_FACTOR):
    """ Detect outliers using the Hampel filter. """
    rolling_ts = time_series.rolling(window_size * 2, center=True)
    rolling_median = rolling_ts.median().fillna(method='bfill').fillna(method='ffill')
    rolling_sigma = k * (rolling_ts.apply(median_absolute_deviation).fillna(method='bfill').fillna(method='ffill'))
    is_outlier = np.abs(time_series - rolling_median) >= (threshold * rolling_sigma)
    outlier_indices = np.array(np.where(is_outlier)).flatten()
    return is_outlier, outlier_indices, rolling_median


def validate_arguments(window_size, threshold):
    if type(window_size) != int:
        raise ValueError("Window size must be an integer.")
    else:
        if window_size <= 0:
            raise ValueError("Window size must be nonnegative.")

    if type(threshold) != int:
        raise ValueError("Threshold must be an integer.")
    else:
        if threshold < 0:
            raise ValueError("Threshold must be positive.")


from numba import jit
import pandas as pd


@jit(nopython=True)
def hampel_filter_numba(time_series, window_size, threshold=3, k=GAUSSIAN_SCALE_FACTOR):
    """
    Hampel filter implementation that works on numpy arrays, implemented with numba. Snatched from this implementation:
    https://github.com/erykml/medium_articles/blob/master/Machine%20Learning/outlier_detection_hampel_filter.ipynb

    Parameters
    ----------
    time_series: numpy.ndarray
    window_size: int
        The window range is from [(i - window_size):(i + window_size)], so window_size is half of the
        window, counted in number of array elements (as opposed to specify a time span, which is not
        supported by this implementation)
    threshold: float
        The threshold for marking an outlier. A low threshold "narrows" the band within which values are deemed as
        outliers. n_sigmas
    k

    Returns
    -------
    new_series: numpy.ndarray
        series with outliers replaced by rolling median
    indices: list
        List of indices with detected outliers
    """

    time_series_clean = time_series.copy()
    outlier_indices = []
    is_outlier = [False] * len(time_series)

    for t in range(window_size, (len(time_series) - window_size)):
        time_series_window = time_series[(t - window_size):(t + window_size)]
        median_in_window = np.nanmedian(time_series_window)
        mad_in_window = k * np.nanmedian(np.abs(time_series_window - median_in_window))
        absolute_deviation_from_median = np.abs(time_series[t] - median_in_window)
        is_outlier[t] = absolute_deviation_from_median > threshold * mad_in_window
        if is_outlier[t]:
            outlier_indices.append(t)
            time_series_clean[t] = median_in_window

    return is_outlier, outlier_indices, time_series_clean


def hampel_filter_numba(time_series, window_size=7, t0=3):
    """
    Wraps the numba implementation of the Hampel filter to work on dataframes with datetime index.

    Parameters
    ----------
    df : pandas.DataFrame
        pandas series of values from which to remove outliers. The dataframe must have 'date' as index
        and one column named 'value'
    window_size : int
        size of window (including the sample; 7 is equal to 3 on either side of value)
    t0 : float
        The threshold for marking an outlier. A low threshold "narrows" the band within which values are deemed as
        outliers.

    Returns
    -------
    df_outliers : pandas.DataFrame
        Series containing only the outliers
    df_clean : pandas.DataFrame
        Series with outliers replaced by rolling median
    """
    window_size = int(window_size / 2)
    outlier_indices, time_series_clean = hampel_filter_numba(time_series.to_numpy(), window_size, t0)

    return time_series[outlier_indices], time_series_clean
