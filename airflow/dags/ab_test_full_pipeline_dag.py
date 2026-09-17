from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import json
import psycopg2

def load_raw_events():
    with open("/data/raw_events.json") as f:
        events = json.load(f)

    conn = psycopg2.connect(host="postgres", dbname="ab_testing", user="postgres", password="postgres")
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE raw_events;")

    for e in events:
        cur.execute("""
            INSERT INTO raw_events (user_id, experiment_id, variant, event_type, event_value, event_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            e["user_id"], e["experiment_id"], e["variant"], e["event_type"],
            e.get("event_value"), e["event_timestamp"]
        ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(events)} events into raw_events table")


with DAG(
    "ab_test_full_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ab_testing"],
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_events",
        python_callable=load_raw_events,
    )

    dbt_task = BashOperator(
        task_id="dbt_run",
        bash_command="dbt run --project-dir /opt/airflow/dbt_project --profiles-dir /opt/airflow/dbt_project",
    )

    srm_task = BashOperator(
        task_id="srm_check",
        bash_command="python /opt/airflow/quality_checks/srm_check.py",
    )

    significance_task = BashOperator(
        task_id="significance_check",
        bash_command="python /opt/airflow/stats_engine/significance_calculator.py",
    )

    ingest_task >> dbt_task >> srm_task >> significance_task