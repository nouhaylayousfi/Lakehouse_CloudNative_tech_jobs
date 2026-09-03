from pyspark.sql.functions import col, when , lower

def normalize_type_contrat(df):
    t = lower(col("type_contrat"))
    df = df.withColumn(
        "type_contrat_categorie",
        when(t.startswith("cdi"), "CDI")
        .when(t.startswith("cdd"), "CDD")
        .when(t.startswith("intérim") | t.startswith("interim"), "INTERIM")
        .when(t.startswith("stage"), "STAGE")
        .when(t.contains("freelance") | t.contains("indépendant"), "FREELANCE")
        .when(t.startswith("permanent"), "CDI")
        .when(t.contains("contract"), "CDD")
        .when((t == "") | col("type_contrat").isNull(), "NON_RENSEIGNE")
        .otherwise("AUTRE")
    )
    return df