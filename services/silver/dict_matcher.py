
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
    "api",
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
    "data Management",
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
    "qlik",

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

    # Frameworks
    "langchain",
    "langgraph",
    "llamaindex",
    "haystack",
    "semantic kernel",
    "crewai",
    "autogen",
    "pydanticai",
    "guidance",
    "dspy",
    "instructor",
    "marvin",

    # APIs / Providers
    "openai",
    "azure openai",
    "anthropic",
    "claude",
    "gemini",
    "vertex ai",
    "google ai",
    "groq",
    "cohere",
    "mistral",
    "deepseek",
    "openrouter",
    "together ai",
    "replicate",
    "fireworks ai",

    # Local inference
    "ollama",
    "vllm",
    "llama.cpp",
    "llamacpp",
    "text-generation-inference",
    "tgi",
    "lm studio",
    "jan",
    "koboldcpp",

    # Hugging Face ecosystem
    "huggingface",
    "hugging face",
    "transformers",
    "datasets",
    "evaluate",
    "accelerate",
    "peft",
    "trl",
    "diffusers",
    "tokenizers",
    "optimum",
    "safetensors",

    # Retrieval & Vector DB
    "rag",
    "graphrag",
    "faiss",
    "chroma",
    "chromadb",
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "vespa",
    "pgvector",
    "redis vector",
    "elasticsearch",
    "opensearch",

    # Fine-tuning / Inference
    "lora",
    "qlora",
    "adapterhub",
    "bitsandbytes",
    "gguf",
    "gptq",
    "awq",

    # Evaluation / Observability
    "ragas",
    "deepeval",
    "promptfoo",
    "langsmith",
    "langfuse",
    "phoenix",
    "helicone",
    "mlflow",

    # Serving
    "litellm",
    "bentoml",
    "ray serve",
    "triton inference server",

    # Protocols
    "mcp",
    "model context protocol",

    # Foundation models
    "gpt-3.5",
    "gpt-4",
    "gpt-4o",
    "gpt-5",
    "claude 3",
    "claude 3.5",
    "claude 4",
    "gemini 1.5",
    "gemini 2.0",
    "gemini 2.5",
    "llama 2",
    "llama 3",
    "llama 3.1",
    "llama 4",
    "mistral 7b",
    "mixtral",
    "deepseek-r1",
    "deepseek-v3",
    "qwen",
    "qwen2",
    "qwen3",
    "phi-3",
    "phi-4",
    "command-r",
    "gemma",
    "falcon",
    "yi",
    "vicuna",
    "zephyr"


    # Version Control
    "github", "git", "bitbucket",

    # Formats complémentaires
    "csv", "excel", "google sheets",

    # Automation
    "automation", "scripting",
]

SYNONYMS = {
    # Langages
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "c sharp": "c#",
    "csharp": "c#",
    "cpp": "c++",
    "objective c": "objective-c",

    # Cloud
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "azure cloud": "azure",
    "microsoft azure": "azure",

    # Conteneurisation / orchestration
    "k8s": "kubernetes",
    "docker compose": "docker",
    "dockerfile": "docker",

    # Data / Big Data
    "apache spark": "spark",
    "spark sql": "spark",
    "apache kafka": "kafka",
    "apache airflow": "airflow",
    "apache hadoop": "hadoop",
    "databricks lakehouse": "databricks",
    "power bi": "powerbi",
    "microsoft power bi": "powerbi",
    "ms power bi": "powerbi",

    # Bases de données
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "ms sql server": "sql server",
    "microsoft sql server": "sql server",
    "mysql db": "mysql",
    "no sql": "nosql",
    "elasticsearch db": "elasticsearch",
    "elastic search": "elasticsearch",

    # CI/CD & DevOps
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "gitlab ci": "ci/cd",
    "github actions": "ci/cd",
    "jenkins pipeline": "jenkins",
    "iac": "infrastructure as code",
    "infra as code": "infrastructure as code",
    "terraform iac": "terraform",

    # ML / IA
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "llm": "large language model",
    "llms": "large language model",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "rag": "retrieval augmented generation",
    "cv": "computer vision",
    "computer vision cv": "computer vision",

    # Frameworks web / API
    "rest api": "api rest",
    "restful api": "api rest",
    "graphql api": "graphql",
    "node": "nodejs",
    "node.js": "nodejs",
    "vue": "vuejs",
    "vue.js": "vuejs",
    "react.js": "react",
    "reactjs": "react",
    "angular js": "angular",
    "angularjs": "angular",

    # Méthodologies
    "agile scrum": "agile",
    "scrum master": "scrum",
    "devsecops": "devops",

    # Outils collaboratifs
    "ms office": "microsoft office",
    "office 365": "microsoft office",
    "vs code": "visual studio code",
    "vscode": "visual studio code",
}

