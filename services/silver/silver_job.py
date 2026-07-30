import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from dotenv import load_dotenv
import os
from pyspark.conf import SparkConf
from pyspark.sql import SparkSession , Window
from pyspark.sql import functions as F 
from pyspark.sql.functions import col ,row_number ,desc ,to_timestamp ,when , upper , trim , regexp_replace , array , lit , udf
from pyspark.sql.types import *
from services.silver.skill_extractor import extract_skills_from_text
from services.silver.dict_matcher import TECH_SKILLS , SYNONYMS

load_dotenv()

def create_spark_session_minio(spark_master_url , s3_url ,s3_access_key ,s3_secret_key):
    conf = SparkConf()
    conf.set('spark.hadoop.fs.s3a.endpoint', s3_url)
    conf.set('spark.hadoop.fs.s3a.access.key', s3_access_key)
    conf.set('spark.hadoop.fs.s3a.secret.key', s3_secret_key)
    conf.set('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    conf.set('spark.hadoop.fs.s3a.path.style.access', 'true')
    
    spark = (
        SparkSession.builder
        .appName("tech project")
        .master(spark_master_url)
        .config(conf=conf)
        .getOrCreate()
    )
    return spark

# Read data from bronze layer
def read_data_from_bronze(spark: SparkSession ):
    df = (
        spark.read
            .option("multiline", "true")
            .json("s3a://lakehouse/bronze/*/*.json")
    )
    return df

# Deduplication
def data_processing(df):

    # Offers deduplication
    window = Window\
    .orderBy(desc("date_ingestion"))\
    .partitionBy("id_hash")

    df = df.withColumn(
        "row_number" ,
        row_number().over(window)
    )

    df = df.filter(df.row_number == 1)

    # Cleaning 
    # 1- Parsing date 
    date_columns=[
        "date_actualisation",
        "date_ingestion",
        "date_publication"
    ]
    for co in date_columns:
        df = df.withColumn(
            co, 
            when (col(co) == "" , None )
            .otherwise(to_timestamp(col(co)))
        )
    # 2- Normalizing columns 
    columns = [
        "ville_brute",
        "entreprise", 
        "type_contrat",
        "secteur_activite",
        "niveau_experience",
        "education" ,
        "remote"
        ]
    messages = {
        "ville_brute" : "VILLE NON PRÉCISÉE",
        "entreprise"  : "ENTREPRISE NON PRÉCISÉE",
        "type_contrat": "TYPE DE CONTRAT NON PRÉCISÉE",
        "secteur_activite" : "SECTEUR D'ACTIVITÉ NON PRÉCISÉE",
        "niveau_experience": "NIVEAU D'EXPÉRIENCE NON PRÉCISÉE",
        "education" : "NIVEAU D'ÉDUCATION NON PRÉCISÉE",
        "remote" : "POSSIBILITÉ REMOTE NON PRÉCISÉE"
        }
    for c in columns: 
        df = df.withColumn(
            c,
            when ((col(c).isNull()) , messages.get(c, "NON PRÉCISÉE"))
            .otherwise(trim(upper(regexp_replace(col(c) , r"\s+" , " "))))
            )
        
    # 3- Skills extraction using dict-matcher and handle synonyms 
    
    extract_skills_udf = udf(extract_skills_from_text, ArrayType(StringType()))

    df = df.withColumn(
        "competences_brutes",
        extract_skills_udf(col("description"))
    )

    @udf(ArrayType(StringType()))
    def handle_syn(skills):
        return list({SYNONYMS.get(s.lower(),s.lower())for s in (skills or [])})

    df = df.withColumn("competences_brutes",handle_syn(col("competences_brutes")))

    return df 

if __name__ == "__main__":
    spark_master_url = os.getenv('SPARK_MASTER_URL')
    s3_url= os.getenv('MINIO_ENDPOINT')
    s3_access_key= os.getenv('MINIO_ACCESS_KEY')
    s3_secret_key = os.getenv('MINIO_SECRET_KEY')
    spark = create_spark_session_minio(spark_master_url , s3_url ,s3_access_key ,s3_secret_key)
    df = read_data_from_bronze(spark)
    df_2 = data_processing(df)
    #df.printSchema()
    df_2.filter(
        col("source").isin("indeed_fr", "france_travail")
    ).select(
        "titre_brut", "source", "competences_brutes", "langues", "qualites_pro", "url_offre"
    ).show(5, truncate=False, vertical=True)



