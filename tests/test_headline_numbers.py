"""Guard every number quoted in README.md and reports/report.md.

These recompute the headline results from data/processed/cell_counts.csv, the
committed aggregate of the raw Kaggle file. If an analysis change moves a
number, the test fails and the prose has to be updated with it.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest

CELLS = Path(__file__).resolve().parents[1] / "data" / "processed" / "cell_counts.csv"


@pytest.fixture(scope="module")
def cells():
    return pd.read_csv(CELLS)


@pytest.fixture(scope="module")
def totals(cells):
    g = cells.groupby("test group")[["n_users", "n_converted", "n_impressions"]].sum()
    return {
        "n_ad": int(g.loc["ad", "n_users"]), "c_ad": int(g.loc["ad", "n_converted"]),
        "n_ps": int(g.loc["psa", "n_users"]), "c_ps": int(g.loc["psa", "n_converted"]),
        "imp_ad": int(g.loc["ad", "n_impressions"]),
    }


@pytest.fixture(scope="module")
def standardized(cells):
    """Direct standardization of ad cell rates onto the PSA day x hour weights."""
    idx = ["most ads day", "most ads hour"]
    ad = cells[cells["test group"] == "ad"].set_index(idx)
    ps = cells[cells["test group"] == "psa"].set_index(idx)
    j = ad[["n_users", "n_converted"]].join(
        ps[["n_users", "n_converted"]], how="outer", lsuffix="_ad", rsuffix="_ps"
    ).fillna(0)

    usable = j[j["n_users_ad"] > 0]
    w = usable["n_users_ps"] / usable["n_users_ps"].sum()
    rate_ad = usable["n_converted_ad"] / usable["n_users_ad"]
    p_ps = usable["n_converted_ps"].sum() / usable["n_users_ps"].sum()

    std_ad = float((w * rate_ad).sum())
    var = float((w**2 * rate_ad * (1 - rate_ad) / usable["n_users_ad"]).sum())
    se = np.sqrt(var + p_ps * (1 - p_ps) / usable["n_users_ps"].sum())
    return {"std_ad": std_ad, "p_ps": float(p_ps), "lift": std_ad - float(p_ps),
            "se": float(se), "n_cells": len(j), "n_usable": len(usable)}


def test_group_counts(totals):
    assert (totals["n_ad"], totals["c_ad"]) == (564_577, 14_423)
    assert (totals["n_ps"], totals["c_ps"]) == (23_524, 420)
    assert totals["n_ad"] + totals["n_ps"] == 588_101


def test_conversion_rates(totals):
    assert totals["c_ad"] / totals["n_ad"] == pytest.approx(0.025547, abs=5e-7)
    assert totals["c_ps"] / totals["n_ps"] == pytest.approx(0.017854, abs=5e-7)


def test_raw_lift_and_significance(totals):
    p_ad = totals["c_ad"] / totals["n_ad"]
    p_ps = totals["c_ps"] / totals["n_ps"]
    z, pval = proportions_ztest([totals["c_ad"], totals["c_ps"]],
                                [totals["n_ad"], totals["n_ps"]], alternative="larger")
    se = np.sqrt(p_ad * (1 - p_ad) / totals["n_ad"] + p_ps * (1 - p_ps) / totals["n_ps"])

    assert z == pytest.approx(7.3701, abs=5e-5)
    assert pval == pytest.approx(8.526e-14, rel=1e-3)
    assert (p_ad - p_ps) * 100 == pytest.approx(0.7692, abs=5e-5)      # pp
    assert (p_ad - p_ps - 1.96 * se) * 100 == pytest.approx(0.5951, abs=5e-5)
    assert (p_ad - p_ps + 1.96 * se) * 100 == pytest.approx(0.9434, abs=5e-5)
    assert (p_ad / p_ps - 1) * 100 == pytest.approx(43.09, abs=5e-3)   # relative


def test_standardization_uses_every_cell(standardized):
    assert standardized["n_cells"] == 168
    assert standardized["n_usable"] == 168


def test_standardized_lift_and_interval(standardized):
    s = standardized
    assert s["lift"] * 100 == pytest.approx(0.7767, abs=5e-5)
    assert (s["lift"] - 1.96 * s["se"]) * 100 == pytest.approx(0.6023, abs=5e-5)
    assert (s["lift"] + 1.96 * s["se"]) * 100 == pytest.approx(0.9510, abs=5e-5)
    assert (s["std_ad"] / s["p_ps"] - 1) * 100 == pytest.approx(43.50, abs=5e-3)


def test_exposure_and_incremental_conversions(totals, standardized):
    assert totals["imp_ad"] == 14_014_701
    assert totals["imp_ad"] / totals["n_ad"] == pytest.approx(24.82, abs=5e-3)

    incremental = standardized["lift"] * totals["n_ad"]
    assert round(incremental) == 4_385
    assert totals["imp_ad"] / incremental == pytest.approx(3196, abs=1)


def test_mid_range_roi_is_negative(totals, standardized):
    """CPM 5, value 15 — the cell the report leads with."""
    cost = totals["imp_ad"] / 1_000 * 5.0
    gain = standardized["lift"] * totals["n_ad"] * 15.0
    assert (gain - cost) / cost * 100 == pytest.approx(-6.1, abs=0.05)
    assert cost / (standardized["lift"] * totals["n_ad"]) == pytest.approx(15.98, abs=5e-3)


def test_experiment_sizing(totals):
    baseline = totals["c_ad"] / totals["n_ad"]
    h = proportion_effectsize(baseline + 0.005, baseline)
    n = NormalIndPower().solve_power(effect_size=h, power=0.80, alpha=0.05,
                                     ratio=1.0, alternative="two-sided")
    assert round(n) == 17_083
