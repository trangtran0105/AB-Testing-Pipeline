from scipy.stats import chisquare
import psycopg2
import os

DB_HOST = os.getenv("DBT_HOST", "localhost")

def get_counts_from_db(experiment_id="checkout_button_color"):
    conn = psycopg2.connect(
        host=DB_HOST, dbname="ab_testing", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT variant, total_users FROM fct_experiment_results
        WHERE experiment_id = %s
    """, (experiment_id,))
    rows = dict(cur.fetchall())
    cur.close()
    conn.close()
    return rows.get("control", 0), rows.get("treatment", 0)


def check_srm(control_count, treatment_count, expected_ratio=0.5):
    total = control_count + treatment_count
    expected = [total * expected_ratio, total * (1 - expected_ratio)]
    observed = [control_count, treatment_count]
    chi2, p_value = chisquare(observed, expected)
    is_srm = p_value < 0.01
    return chi2, p_value, is_srm


def save_result(experiment_id, control_count, treatment_count, p_value, is_srm):
    conn = psycopg2.connect(
        host=DB_HOST, dbname="ab_testing", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO srm_check_results (experiment_id, control_count, treatment_count, p_value, srm_detected)
        VALUES (%s, %s, %s, %s, %s)
    """, (experiment_id, control_count, treatment_count, float(p_value), bool(is_srm)))
    conn.commit()
    cur.close()
    conn.close()


def run_srm_check():
    experiment_id = "checkout_button_color"
    control_count, treatment_count = get_counts_from_db(experiment_id)

    chi2, p_value, is_srm = check_srm(control_count, treatment_count)

    print(f"Control: {control_count}, Treatment: {treatment_count}")
    print(f"Chi2: {chi2:.4f}, P-value: {p_value:.5f}, SRM detected: {is_srm}")

    save_result(experiment_id, control_count, treatment_count, p_value, is_srm)

    if is_srm:
        raise ValueError("SRM detected! Stopping pipeline — do not trust downstream results.")


if __name__ == "__main__":
    run_srm_check()