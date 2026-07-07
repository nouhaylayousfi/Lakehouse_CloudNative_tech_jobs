from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


@dag(
    dag_id="test_spark_connection",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["test"],
)
def test_spark_connection():

    submit_test_job = SparkSubmitOperator(
        task_id="submit_test_job",
        application="/opt/airflow/project/jobs/test_spark.py",
        conn_id="spark_default",
    )

    submit_test_job


test_spark_connection()