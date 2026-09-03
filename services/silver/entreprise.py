from pyspark.sql.functions import col, when, trim, size, split, length

def clean_entreprise(df):
    df = df.withColumn(
        "entreprise",
        when(
            (trim(col("entreprise")) == "") |
            col("entreprise").rlike(r'(?i)\bans?\b') |
            col("entreprise").rlike(r'(?i)\(h/f\)') |
            col("entreprise").rlike(r'(?i)recrute|recherch') |
            col("entreprise").rlike(r'^[a-zàâäéèêëïîôöùûüç]') |
            col("entreprise").rlike(r'\.\s*$') |
            col("entreprise").rlike(r'\b(19|20)\d{2}\b') |
            col("entreprise").rlike(r'(?i)^(fondée|fondee|acteur|à propos|a propos|une grande|un grand)') |
            col("entreprise").rlike(r'(?i)www\.|\.com') |
            (size(split(trim(col("entreprise")), r"\s+")) > 6),
            None
        ).otherwise(col("entreprise"))
    )
    return df 