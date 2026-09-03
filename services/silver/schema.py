from pyspark.sql.functions import lit
from pyspark.sql.types import ArrayType, StringType, StructType, StructField


"""
    The data normalization across different data sources should normally be
    performed in the field_mapper. It is implemented here because an issue was
    discovered too late to be fixed in the field_mapper without losing historical
    data already stored in the Bronze layer.
"""
competences_rome_schema = ArrayType(StructType([
    StructField("libelle", StringType()),
    StructField("exigence", StringType()),
]))

# Common requested columns
req_columns = [
"id_hash","id_source","source","pays","education","titre_brut","description",
"type_contrat","niveau_experience","ville_brute",
"entreprise","secteur_activite","remote",
"salaire_brut","salaire_min","salaire_max",
"competences_brutes","competences_rome","qualites_pro","langues",
"date_publication","date_actualisation","date_ingestion",
"url_offre","nombre_postes"
]

# Columns to delet 
delete_all = [
    "latitude" , "longitude" , "tranche_effectif" , "region"
    "code_postal" , "code_rome", "libelle_rome","appellation_rome",
    "langue","qualification" , "nature_contrat" , "salaire_est" 
]

def build_silver_schema(df):
    """
    Applies unified schema normalization to a source DataFrame:
    - keeps the common columns (req_columns)
    - adds missing columns based on the source (add_indeed_rek / add_ft)
    - removes unwanted columns (delete_all / delete_ft)
    """
    for c in delete_all: 
        if c in df.columns:
            df = df.drop(c)

    if "competences_rome" not in df.columns:
        df = df.withColumn("competences_rome", lit(None).cast(competences_rome_schema))

    for c in req_columns:
        if c not in df.columns:
            df = df.withColumn(c, lit(None).cast(StringType()))

    return df.select(*req_columns)