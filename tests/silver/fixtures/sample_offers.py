from pyspark.sql.types import StructType, StructField, StringType

SCHEMA = StructType([
    StructField("id_hash", StringType(), True),
    StructField("titre_brut", StringType(), True),
    StructField("source", StringType(), True),
    StructField("pays", StringType(), True),
    StructField("entreprise", StringType(), True),
    StructField("niveau_experience_categorie", StringType(), True),
    StructField("education_categorie", StringType(), True),
    StructField("type_contrat_categorie", StringType(), True),
    StructField("date_publication", StringType(), True),
])

def sample_offer(**overrides):
    """Retourne une offre valide par défaut, avec possibilité d'override champ par champ."""
    base = {
        "id_hash": "abc123",
        "titre_brut": "Développeur Python",
        "source": "rekrute",
        "pays": "MA",
        "entreprise": "ALTEN MAROC",
        "niveau_experience_categorie": "CONFIRME",
        "education_categorie": "BAC+5",
        "type_contrat_categorie": "CDI",
        "date_publication": "2026-08-14",
    }
    base.update(overrides)
    return base

