import pytest

from services.silver.data_quality import validate_silver
from tests.silver.fixtures.sample_offers import sample_offer , SCHEMA

def test_validate_silver_passes_on_clean_data(spark):
    df = spark.createDataFrame([sample_offer(), sample_offer(id_hash="def456")],schema=SCHEMA)
    assert validate_silver(df) is True

def test_validate_silver_fails_on_null_id_hash(spark):
    df = spark.createDataFrame([sample_offer(id_hash=None)],schema=SCHEMA)
    with pytest.raises(AssertionError, match="id_hash"):
        validate_silver(df)

def test_validate_silver_fails_on_null_titre_brut(spark):
    df = spark.createDataFrame([sample_offer(titre_brut=None)],schema=SCHEMA)
    with pytest.raises(AssertionError, match="titre_brut"):
        validate_silver(df)


def test_validate_silver_fails_on_duplicate_id_hash(spark):
    df = spark.createDataFrame([
        sample_offer(id_hash="same_id"),
        sample_offer(id_hash="same_id"),
    ],schema=SCHEMA)
    with pytest.raises(AssertionError, match="duplicate"):
        validate_silver(df)


def test_validate_silver_fails_on_invalid_pays(spark):
    df = spark.createDataFrame([sample_offer(pays="ES")],schema=SCHEMA)
    with pytest.raises(AssertionError, match="country"):
        validate_silver(df)


def test_validate_silver_fails_on_unexpected_category_value(spark):
    df = spark.createDataFrame([sample_offer(niveau_experience_categorie="INCONNU_BUG")],schema=SCHEMA)
    with pytest.raises(AssertionError, match="niveau_experience_categorie"):
        validate_silver(df)


def test_validate_silver_allows_null_optional_fields(spark):
    df = spark.createDataFrame([sample_offer(entreprise=None)],schema=SCHEMA)
    assert validate_silver(df) is True