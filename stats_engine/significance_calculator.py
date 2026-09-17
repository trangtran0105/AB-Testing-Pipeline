from scipy import stats
import numpy as np
import psycopg2
import os

DB_HOST = os.getenv("DBT_HOST", "localhost")

def get_data_from_db(experiment_id="checkout_button_color"):
    conn = psycopg2.connect(
        host=DB_HOST, dbname="ab_testing", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT variant, total_users, total_conversions FROM fct_experiment_results
        WHERE experiment_id = %s
    """, (experiment_id,))
    rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    cur.close()
    conn.close()
    return rows.get("control"), rows.get("treatment")


def calculate_significance(control_conversions, control_total, treatment_conversions, treatment_total, confidence=0.95):
    p_control = control_conversions / control_total
    p_treatment = treatment_conversions / treatment_total

    p_pool = (control_conversions + treatment_conversions) / (control_total + treatment_total)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/control_total + 1/treatment_total))
    z_score = (p_treatment - p_control) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    relative_lift = (p_treatment - p_control) / p_control
    se_diff = np.sqrt(
        (p_control * (1 - p_control) / control_total) +
        (p_treatment * (1 - p_treatment) / treatment_total)
    )
    z_crit = stats.norm.ppf(1 - (1 - confidence) / 2)
    ci_lower = (p_treatment - p_control) - z_crit * se_diff
    ci_upper = (p_treatment - p_control) + z_crit * se_diff

    return {
        "control_rate": p_control,
        "treatment_rate": p_treatment,
        "relative_lift_pct": relative_lift * 100,
        "p_value": p_value,
        "is_significant": p_value < (1 - confidence),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


def save_result(experiment_id, result):
    conn = psycopg2.connect(
        host=DB_HOST, dbname="ab_testing", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO significance_results
        (experiment_id, control_rate, treatment_rate, relative_lift_pct, p_value, is_significant, ci_lower, ci_upper)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        experiment_id,
        float(result["control_rate"]),
        float(result["treatment_rate"]),
        float(result["relative_lift_pct"]),
        float(result["p_value"]),
        bool(result["is_significant"]),
        float(result["ci_lower"]),
        float(result["ci_upper"]),
    ))
    conn.commit()
    cur.close()
    conn.close()


def run_significance_check():
    experiment_id = "checkout_button_color"
    control, treatment = get_data_from_db(experiment_id)
    control_total, control_conversions = control
    treatment_total, treatment_conversions = treatment

    result = calculate_significance(control_conversions, control_total, treatment_conversions, treatment_total)

    print("=== A/B Test Result ===")
    for key, value in result.items():
        print(f"{key}: {value}")

    save_result(experiment_id, result)


if __name__ == "__main__":
    run_significance_check()