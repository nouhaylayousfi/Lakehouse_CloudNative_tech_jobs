import unicodedata
from pyspark.sql import Window
from pyspark.sql.functions import col, when ,row_number, desc, udf, lower, trim, regexp_replace
from pyspark.sql.types import StringType

def deduplicate(df):
    df = df.withColumn(
        "_is_complete",
        when((col("description") != "") & (col("entreprise") != ""), 1).otherwise(0)
    )
    window = Window.partitionBy("id_hash").orderBy(desc("_is_complete"), desc("date_ingestion"))
    df = df.withColumn("row_number", row_number().over(window))
    df = df.filter(col("row_number") == 1)
    df = df.drop("row_number", "_is_complete")
    return df


def strip_accents(text):
    if not text:
        return text
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )
strip_accents_udf = udf(strip_accents, StringType())


def deduplicate_cross_source(df):
    tmp = df.withColumn(
        "_titre_norm",
        trim(regexp_replace(strip_accents_udf(lower(col("titre_brut"))), r"[^\w\s]", ""))
    ).withColumn(
        "_entreprise_norm",
        trim(regexp_replace(strip_accents_udf(lower(col("entreprise"))), r"[^\w\s]", ""))
    )

    window = Window.partitionBy("pays", "_entreprise_norm", "_titre_norm").orderBy(desc("date_publication"))
    tmp = tmp.withColumn("row_number", row_number().over(window))
    tmp = tmp.filter(col("row_number") == 1)

    return tmp.drop("_titre_norm", "_entreprise_norm", "row_number")