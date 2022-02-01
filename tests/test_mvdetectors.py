import pytest
import pandas as pd
import numpy as np

from tsod.mvdetectors import MVRangeDetector


def test_mv_range_detector():
    n_obs = 15
    normal_data = pd.DataFrame(np.random.uniform(size=[3, n_obs]))
    normal_data.iloc[2, [2, 8]] = np.nan
    abnormal_data = pd.DataFrame(np.random.uniform(size=[3, n_obs]))
    abnormal_data.iloc[0, [2, 3, 7]] = 5
    abnormal_data.iloc[1, [2, 12]] = 2
    abnormal_data.iloc[0, [8]] = np.nan
    abnormal_data.iloc[2, [8, 9]] = np.nan

    detector = MVRangeDetector(min_value=0.0, max_value=1.0)
    expected_anomalies = pd.Series(
        [False, False, True, True, False, False, False, True, False, False, False, False, True, False, False],
        index=pd.Int64Index(np.arange(n_obs), dtype='int64'))
    detected_anomalies = detector.detect(abnormal_data)
    pd.testing.assert_series_equal(expected_anomalies, detected_anomalies)

    detected_anomalies = detector.detect(normal_data)
    assert not any(detected_anomalies)
