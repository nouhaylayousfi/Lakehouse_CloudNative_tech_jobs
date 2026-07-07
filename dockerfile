FROM apache/airflow:3.2.2

USER root

# Java requis pour spark-submit
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Provider Spark pour Airflow + client spark-submit (via pyspark, qui inclut les binaires)
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark \
    pyspark==3.5.1 \
    boto3