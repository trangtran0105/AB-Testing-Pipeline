from scipy.stats import chisquare

def check_srm(control_count, treatment_count, expected_ratio=0.5):
    """
    Sample Ratio Mismatch (SRM) check.

    Verifies whether the observed split between control and treatment
    groups matches the expected randomization ratio (e.g. 50/50).
    A significant mismatch suggests a bug in the assignment logic,
    tracking issues, or bot traffic — and means the experiment
    results should NOT be trusted until the root cause is fixed.
    """
    total = control_count + treatment_count
    expected = [total * expected_ratio, total * (1 - expected_ratio)]
    observed = [control_count, treatment_count]

    chi2, p_value = chisquare(observed, expected)

    # Common threshold for SRM checks: p_value < 0.01
    # (stricter than the usual 0.05, since this is a "safety guard"
    # step — we want high confidence before raising an alarm)
    is_srm = p_value < 0.01

    return {
        "control_count": control_count,
        "treatment_count": treatment_count,
        "expected_control": round(expected[0], 1),
        "expected_treatment": round(expected[1], 1),
        "chi2_statistic": round(chi2, 4),
        "p_value": round(p_value, 5),
        "srm_detected": is_srm,
    }


if __name__ == "__main__":
    # Using the real numbers from fct_experiment_results
    result = check_srm(
        control_count=24957,
        treatment_count=25043,
    )

    print("=== SRM Check Result ===")
    for key, value in result.items():
        print(f"{key}: {value}")

    if result["srm_detected"]:
        print("\n⚠️  WARNING: Sample Ratio Mismatch detected — do NOT trust this A/B test result!")
    else:
        print("\n✅ Group split looks normal, statistical results can be trusted.")