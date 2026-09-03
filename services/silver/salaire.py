import re
from pyspark.sql.functions import col, when, trim, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

def parse_salaire(text):
    
    if not text: 
        return (None, None, None, None)

    original = text
    # --- Structured case: Annual / Monthly / Hourly from X [to Y] Euros ---
    match = re.search(
        r'(Annuel|Mensuel|Horaire)\s+de\s+([\d.]+)\s*Euros(?:\s+à\s+([\d.]+)\s*Euros)?',
        text, re.IGNORECASE
    )
    if match: 
        periode, v1, v2 = match.groups()
        v1 = float(v1)
        v2 = float(v2) if v2 else v1
        periode = periode.upper()

        if periode == "MENSUEL":
            v1, v2 = v1 * 12, v2 * 12
        elif periode == "HORAIRE":
            return (original, "HORAIRE" , None, None)
        return (original, "ANNUEL", min(v1,v2), max(v1,v2))

    # --- Indeed range case: "De X € à Y € par an/mois/jour" ---
    match = re.search(
        r'De\s+([\d\s\xa0]+)\s*€\s*à\s+([\d\s\xa0]+)\s*€\s*par\s+(an|mois|jour)',
        text, re.IGNORECASE
    )
    if match:
        v1_raw, v2_raw, unite = match.groups()
        
        v1 = float(re.sub(r'\D', '', v1_raw))
        v2 = float(re.sub(r'\D', '', v2_raw))
        unite = unite.lower()
        if unite == "an":
            return (original, "ANNUEL", min(v1, v2), max(v1, v2))
        elif unite == "mois":
            return (original, "ANNUEL", min(v1, v2) * 12, max(v1, v2) * 12)
        else:
            return (original, "JOURNALIER", None, None)

    # --- Indeed single value case: "X € par an/mois/jour" ---
    match = re.search(
        r'([\d\s\xa0\u202f]+)\s*€\s*par\s+(an|mois|jour)',
        text, re.IGNORECASE
    )
    if match:
        v_raw, unite = match.groups()
        v = float(re.sub(r'\D', '', v_raw))
        unite = unite.lower()
        if unite == "an":
            return (original, "ANNUEL", v, v)
        elif unite == "mois":
            return (original, "ANNUEL", v * 12, v * 12)
        else:
            return (original, "JOURNALIER", None, None)
    
    # --- Case: Raw numeric value only (e.g., "22404") ---
    if re.fullmatch(r'\d{4,6}', text.strip()):
        return (original, "NON_STRUCTURE", None, None)

    # --- Case: Benefits or other non-salary text ---
    avantage_keywords = r'(?i)restaurant|télétravail|remote|prime|13[eè]me mois|smic|barème|convention'
    if re.search(avantage_keywords, text):
        return (original, "AVANTAGE", None, None)

    # --- Fallback case: "depending on experience", "negotiable", etc. ---
    return (original, "NON_STRUCTURE", None , None)


def apply_salaire_parsing(df):
    df = df.withColumn(
            "salaire_brut",
            when(trim(col("salaire_brut")) == "", None).otherwise(trim(col("salaire_brut")))
        )
    
    parse_salaire_udf = udf(parse_salaire, StructType([
        StructField("salaire_brut", StringType()),
        StructField("salaire_type", StringType()),
        StructField("salaire_min", DoubleType()),
        StructField("salaire_max", DoubleType()),
    ]))

    df = df.withColumn("salaire_parsed", parse_salaire_udf(col("salaire_brut")))
    df = df.drop("salaire_min", "salaire_max")
    df = df.select(
        "*",
        col("salaire_parsed.salaire_type").alias("salaire_type"),
        col("salaire_parsed.salaire_min").alias("salaire_min"),
        col("salaire_parsed.salaire_max").alias("salaire_max"),
    ).drop("salaire_parsed")

    return df
    