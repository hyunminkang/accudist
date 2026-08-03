import numpy as np
import pytest
from scipy import stats

import accudist as ad


@pytest.mark.scipy_gap
def test_poisson_upper_log_tail_remains_finite_where_scipy_underflows():
    got = ad.ppois(200, 0.1, lower_tail=False, log=True)
    assert got == pytest.approx(-1331.4544, abs=1e-3)
    assert np.isneginf(stats.poisson.logsf(200, 0.1))

