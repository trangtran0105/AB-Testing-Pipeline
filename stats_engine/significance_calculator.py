from scipy import stats
import numpy as np

def calculate_significance(
    control_conversions, control_total,
    treatment_conversions, treatment_total,
    confidence=0.95
):
    p_control = control_conversions / control_total
    p_treatment = treatment_conversions / treatment_total

    # Two-proportion z-test — kiểm tra sự khác biệt giữa 2 tỷ lệ
    p_pool = (control_conversions + treatment_conversions) / (control_total + treatment_total)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/control_total + 1/treatment_total))
    z_score = (p_treatment - p_control) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    # Confidence interval cho khoảng chênh lệch (lift)
    relative_lift = (p_treatment - p_control) / p_control
    se_diff = np.sqrt(
        (p_control * (1 - p_control) / control_total) +
        (p_treatment * (1 - p_treatment) / treatment_total)
    )
    z_crit = stats.norm.ppf(1 - (1 - confidence) / 2)
    ci_lower = (p_treatment - p_control) - z_crit * se_diff
    ci_upper = (p_treatment - p_control) + z_crit * se_diff

    return {
        "control_rate": round(p_control, 4),
        "treatment_rate": round(p_treatment, 4),
        "relative_lift_pct": round(relative_lift * 100, 2),
        "p_value": round(p_value, 5),
        "is_significant": p_value < (1 - confidence),
        "confidence_interval_abs_diff": [round(ci_lower, 4), round(ci_upper, 4)],
    }


if __name__ == "__main__":
    result = calculate_significance(
        control_conversions=2426,
        control_total=24957,
        treatment_conversions=2888,
        treatment_total=25043,
    )

    print("=== A/B Test Result ===")
    for key, value in result.items():
        print(f"{key}: {value}")