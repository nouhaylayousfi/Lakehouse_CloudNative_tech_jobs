import re
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType



def categorize_experience(years):
    if years <= 2:
        return "DEBUTANT"
    elif years <= 5:
        return "CONFIRME"
    else:
        return "SENIOR"


def parse_experience(text):
    if not text or not text.strip():
        return (text, "NON_RENSEIGNE", None, None)

    original = text
    t = text.strip()

    # Case 1: number at the beginning ("5 Year(s) - free text", "24 Months")
    match = re.match(r'^(\d+)\s*(an|mois)', t, re.IGNORECASE)
    if match:
        val, unit = match.groups()
        val = int(val)
        years = val if unit.lower().startswith("an") else round(val / 12, 2)
        return (original, categorize_experience(years), years, years)

    # Case 2: named categories, potentially multiple ones separated by "|"
    # -> we keep the lowest one (actual minimum requirement)

    priority = ["débutant", "junior", "intermédiaire", "confirmé", "expert", "très senior"]
    mapping = {
        "débutant": "DEBUTANT",
        "junior": "DEBUTANT",
        "intermédiaire": "CONFIRME",
        "confirmé": "CONFIRME",
        "expert": "SENIOR",
        "très senior": "SENIOR",
    }
    t_lower = t.lower()
    found = [kw for kw in priority if kw in t_lower]
    if found:
        return (original, mapping[found[0]], None, None)

    # Case 3: nothing usable ("Experience required", etc.)
    return (original, "NON_STRUCTURE", None, None)

def parse_education(text):
    if not text or not text.strip():
        return (text, "NON_RENSEIGNE", None)
    
    original = text 
    t= text.strip().lower()

    match = re.match(r'^bac\s\+\s*(\d+)', t)
    if match:
        niveau = int(match.group(1))
        return (text, f"BAC+{niveau}", niveau)

    if "qualification avant bac" in t:
        return (text, "INFRA_BAC", None)

    if t == "bac":
        return (text, "BAC", 0)

    return (text, "NON_STRUCTURE", None)

def apply_experience_parsing(df):
    parse_experience_udf = udf(parse_experience, StructType([
        StructField("niveau_experience_brut", StringType()),
        StructField("niveau_experience_categorie", StringType()),
        StructField("niveau_experience_min", DoubleType()),
        StructField("niveau_experience_max", DoubleType()),
    ]))

    df = df.withColumn("experience_parsed", parse_experience_udf(col("niveau_experience")))

    df = df.select(
        "*",
        col("experience_parsed.niveau_experience_categorie").alias("niveau_experience_categorie"),
        col("experience_parsed.niveau_experience_min").alias("niveau_experience_min"),
        col("experience_parsed.niveau_experience_max").alias("niveau_experience_max"),
    ).drop("experience_parsed")
    return df

def apply_education_parsing(df):
    parse_education_udf = udf(parse_education, StructType([
        StructField("education_brut", StringType()),
        StructField("education_categorie", StringType()),
        StructField("education_niveau", IntegerType()),
    ]))

    df = df.withColumn("education_parsed", parse_education_udf(col("education")))

    df = df.select(
        "*",
        col("education_parsed.education_categorie").alias("education_categorie"),
        col("education_parsed.education_niveau").alias("education_niveau"),
    ).drop("education_parsed")



    return df
