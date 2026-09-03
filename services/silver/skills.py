from pyspark.sql.functions import col, udf , join
from pyspark.sql.types import ArrayType, StringType
from services.silver.skill_extractor import extract_skills_from_text
from services.silver.dict_matcher import SYNONYMS

def extract_and_normalize_skills(df):
    extract_skills_udf = udf(extract_skills_from_text, ArrayType(StringType()))

    texte_pour_extraction = col("description") + " " + join(col("competences_rome").libelle, " ")
    df = df.withColumn(
        "competences_brutes",
        extract_skills_udf(texte_pour_extraction)
    )

    @udf(ArrayType(StringType()))
    def handle_syn(skills):
        return list({SYNONYMS.get(s.lower(), s.lower()) for s in (skills or [])})

    df = df.withColumn(
        "competences_brutes",
        handle_syn(col("competences_brutes"))
    )

    return df