
TECH_SKILLS = [
    # Programming Languages
    "python", "java", "scala", "go", "golang", "rust",
    "javascript", "typescript", "sql", "pl/sql",
    "bash", "shell", "powershell", "c#", "c++",

    # Big Data & Streaming
    "spark", "apache spark", "pyspark", "spark streaming",
    "kafka", "apache kafka", "kafka connect", "kafka streams",
    "hadoop", "hdfs", "yarn", "hive", "impala",
    "flink", "apache flink", "storm", "beam",
    "airflow", "apache airflow", "dbt", "luigi",
    "nifi", "apache nifi", "oozie",

    # Data Warehousing
    "snowflake", "bigquery", "redshift",
    "synapse", "teradata", "vertica",
    "oracle", "exadata", 

    # Cloud Platforms
    "aws", "amazon web services",
    "gcp", "google cloud",
    "azure", "microsoft azure",

    # AWS Services
    "s3", "emr", "glue", "athena",
    "lambda", "eks", "ecs", "dynamodb",
    "kinesis", "redshift","aurora",

    # Azure Services
    "azure data factory", "adf",
    "azure databricks",
    "azure synapse",
    "azure data lake",
    "event hub",
    "azure functions",

    # GCP Services
    "cloud storage",
    "dataflow",
    "dataproc",
    "pubsub",
    "pub/sub",
    "bigquery",
    "cloud composer",

    # Lakehouse
    "databricks",
    "unity catalog",
    "delta lake",
    "apache iceberg",
    "iceberg",
    "hudi",
    "lakehouse",

    # Storage Formats
    "parquet",
    "avro",
    "orc",
    "json",
    "csv",

    # Databases
    "postgresql",
    "mysql",
    "sql server",
    "mssql",
    "oracle",
    "mongodb",
    "redis",
    "cassandra",
    "couchbase",
    "dynamodb",
    "neo4j",
    "elasticsearch",
    "opensearch",

    # Containers & DevOps
    "docker",
    "kubernetes",
    "openshift",
    "helm",
    "terraform",
    "ansible",
    "jenkins",
    "gitlab",
    "gitlab ci",
    "ci/cd",
    "github actions",
    "azure devops",
    "argocd",
    "vault",

    # Data Modeling
    "data vault",
    "star schema",
    "snowflake schema",
    "dimensional modeling",
    "kimball",

    # APIs & Integration
    "rest",
    "rest api",
    "api rest",
    "graphql",
    "soap",
    "openapi",
    "swagger",

    # Data Quality & Governance
    "great expectations",
    "data quality",
    "data governance",
    "data lineage",
    "collibra",
    "atlas",
    "apache atlas",

    # Monitoring & Observability
    "grafana",
    "prometheus",
    "elk",
    "logstash",
    "kibana",
    "opentelemetry",

    # ML / MLOps
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "mlflow",
    "kubeflow",
    "feature store",

    # Data Visualization
    "power bi",
    "tableau",
    "looker",
    "superset",
    "metabase",

    # Data Engineering Concepts
    "etl",
    "elt",
    "data pipeline",
    "streaming",
    "batch processing",
    "real-time",
    "data lake",
    "data warehouse",
    "data mesh",
    "data fabric",
    "cdc",
    "change data capture",

    # Web Scraping
    "beautifulsoup", "selenium", "playwright", "scrapy",
    "requests", "httpx", "aiohttp",

    # AI / LLM Frameworks  
    "langchain", "llamaindex", "openrouter", "langraph",
    "ollama", "huggingface", "transformers",

    # Version Control
    "github", "git", "bitbucket",

    # Formats complémentaires
    "csv", "excel", "google sheets",

    # Automation
    "automation", "scripting",
]

import re
SKILLS_WITH_SPECIAL_CHARS = ["c++", "c#", "pl/sql", "ci/cd", "pub/sub", "rest api", "api rest"]

def extract_skills_from_text(text: str) -> list[str]:
    if not text:
        return []

    text_lower = text.lower()
    found = []

    for skill in TECH_SKILLS:
        skill_lower = skill.lower()

        if skill_lower in SKILLS_WITH_SPECIAL_CHARS:
            # Simple substring match for skills with special chars
            # Surrounded by non-alphanumeric or start/end of string
            pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"
        else:
            # Word boundary match for normal skills
            pattern = r"\b" + re.escape(skill_lower) + r"\b"

        if re.search(pattern, text_lower):
            found.append(skill)

    return found