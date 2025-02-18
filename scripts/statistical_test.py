from scipy.stats import fisher_exact, mannwhitneyu, rankdata
from scipy.stats.contingency import odds_ratio

"""
The Fisher Exact Test

Return: the p value, the estimated odds ratio (conditional), the confidence interval of the odds ratio, and the estimated odds ratio (unconditional)
"""


def fisher_exact_test(contingency_table, alternative='two-sided', CI_level=0.95, verbose=True):
    prior_odds_ratio, p = fisher_exact(contingency_table, alternative=alternative)

    # Effective size: the odds ratio
    odds_ratio_results = odds_ratio(contingency_table, kind='conditional')
    # CI is a named tuple
    odds_ratio_CI = odds_ratio_results.confidence_interval(confidence_level=CI_level)

    if verbose:
        print('The Fisher Exact Test')
        print('The contingency table:\n{}'.format(contingency_table))
        print('p value: {}\nodds ratio: {} with the confidence interval ({}, {}) at level {}'.format(
            p, odds_ratio_results.statistic, odds_ratio_CI.low, odds_ratio_CI.high, CI_level))

    return p, odds_ratio_results.statistic, odds_ratio_CI.low, odds_ratio_CI.high


"""
The Mann-Whitney U Test

Return: the p value, the Vargha and Delaney's A12 statistics, , CI, U1, U2, the rank sum of treatment, and the rank sum of control
"""


def mann_whitney_u_test(treatment, control, alternative='two-sided', verbose=True):
    m = len(treatment)
    n = len(control)
    assert m == n

    U1, p = mannwhitneyu(treatment, control, alternative=alternative, method='exact')
    U2 = n * m - U1

    # Effective size: A12
    rank_results = rankdata(treatment + control)
    r1 = sum(rank_results[0:m])
    r2 = sum(rank_results[m:m+n])
    # A = (r1/m - (m+1)/2)/n # formula (14) in Vargha and Delaney, 2000
    # equivalent formula to avoid accuracy errors
    A_12 = (2 * r1 - m * (m + 1)) / (2 * n * m)

    if verbose:
        print('The Mann-Whitney U Test')
        print('p value: {}\nA12: {}'.format(p, A_12))

    return p, A_12, U1, U2, r1, r2
