# A/B Testing Data Pipeline

An end-to-end, automated A/B testing pipeline built with Airflow, dbt, and PostgreSQL — from raw event ingestion to statistical significance testing, with a built-in data quality gate (Sample Ratio Mismatch detection) and a Metabase dashboard.

The entire pipeline runs as a single Airflow DAG. Triggering one run automatically ingests data, transforms it, validates data quality, and computes the statistical result — no manual steps in between.

## Architecture

```
Synthetic Event Generator (Python)
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│              Airflow DAG: ab_test_full_pipeline           │
│                                                             │
│  ingest_events → dbt_run → srm_check → significance_check │
└─────────────────────────────────────────────────────────┘
       │              │            │               │
       ▼              ▼            ▼               ▼
  raw_events    fct_experiment  srm_check_    significance_
  (Postgres)    _results (dbt)  results        results
                                                     │
                                                     ▼
                                          Metabase Dashboard
```

If the SRM check detects an abnormal control/treatment split, it raises an exception and the pipeline stops — the significance step never runs on data that can't be trusted.

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow 2.9 |
| Data Warehouse | PostgreSQL 15 |
| Transformation | dbt-postgres |
| Data Quality | Custom SRM check (Chi-Square test, SciPy) |
| Statistics | SciPy — two-proportion z-test, 95% confidence interval |
| Dashboard | Metabase |
| Containerization | Docker Compose |

## What the Pipeline Does

1. **Generates synthetic experiment data** — 50,000 users randomly split into control/treatment groups, with a known ~15% conversion lift deliberately built into the treatment group. This known ground truth is used purely to validate that the pipeline computes results correctly during development — it plays no role in a real experiment.
2. **Ingests raw events** into PostgreSQL via an idempotent Airflow task. The task truncates `raw_events` before loading, so re-running the DAG never produces duplicate rows.
3. **Transforms data with dbt** — `stg_events` cleans the raw event stream; `fct_experiment_results` aggregates it into per-variant totals and conversion rates.
4. **Validates data quality** — runs a Sample Ratio Mismatch (SRM) check using a Chi-Square test on the control/treatment split. This acts as a safety gate: a mismatched split (commonly caused by bugs in randomization, tracking issues, or bot traffic) invalidates any statistical conclusion drawn from the experiment, so the pipeline halts here if SRM is detected.
5. **Calculates statistical significance** — a two-proportion z-test producing a p-value, relative lift, and 95% confidence interval for the difference in conversion rates.
6. **Visualizes results** in a Metabase dashboard showing the latest significance result and SRM check history.

## Project Structure

```
ab-testing-pipeline/
├── docker-compose.yml
├── data_generator/
│   └── generate_events.py          # synthetic event generator
├── airflow/
│   └── dags/
│       ├── ab_test_ingest_dag.py         # ingestion only
│       └── ab_test_full_pipeline_dag.py  # full pipeline (ingest → dbt → SRM → significance)
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   └── stg_events.sql
│   │   └── marts/
│   │       └── fct_experiment_results.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── quality_checks/
│   └── srm_check.py                # Sample Ratio Mismatch detection
├── stats_engine/
│   └── significance_calculator.py  # two-proportion z-test
└── .gitignore
```

## How to Run

1. **Start the stack** (Postgres + Airflow):
   ```bash
   docker-compose up -d
   ```

2. **Generate synthetic data:**
   ```bash
   python data_generator/generate_events.py
   ```

3. **Create the database tables** (one-time setup):
   ```bash
   docker exec -it ab_postgres psql -U postgres -d ab_testing
   ```
   Then run the `CREATE TABLE` statements for `raw_events`, `experiment_assignments`, `srm_check_results`, and `significance_results`.

4. **Run the pipeline:** open the Airflow UI at `http://localhost:8080` (user: `admin`, pass: `admin`), unpause and trigger `ab_test_full_pipeline`.

5. **View results:** add a Metabase service to `docker-compose.yml`, point it at the `ab_testing` Postgres database, and build a dashboard from the `significance_results` and `srm_check_results` tables. Metabase runs at `http://localhost:3000`.

## Key Design Decisions

- **Idempotent ingestion.** The ingest task truncates `raw_events` before loading, so triggering the DAG multiple times never duplicates data — a common pitfall in naive ingestion pipelines.
- **SRM check as a safety gate, not just a report.** If the observed group split significantly deviates from the expected 50/50 ratio, the check raises an exception, which stops the downstream `significance_check` task from running. This mirrors how mature A/B testing platforms prevent decisions from being made on invalid experiments.
- **Validated against a known ground truth.** The synthetic data generator bakes in a known treatment lift, so during development the statistical engine's output can be checked against an expected answer — the same way a scale is tested against a calibration weight before it's trusted to weigh something unknown.
- **Containerized dbt.** dbt runs inside the same Airflow container as the rest of the pipeline (via `_PIP_ADDITIONAL_REQUIREMENTS`), so `dbt run` can be triggered automatically as a pipeline step rather than run manually.

## Sample Result

| Metric | Control | Treatment |
|---|---|---|
| Users | 24,957 | 25,043 |
| Conversions | 2,426 | 2,888 |
| Conversion rate | 9.72% | 11.53% |
| Relative lift | — | +18.63% |
| P-value | < 0.0001 | |
| Statistically significant | ✅ Yes | |
| SRM detected | ❌ No (p = 0.70) |
