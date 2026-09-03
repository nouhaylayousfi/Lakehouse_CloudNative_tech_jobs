from services.silver.dedup import deduplicate_cross_source
from tests.silver.fixtures.sample_offers import sample_offer , SCHEMA

def test_dedup_removes_same_market_same_company_same_title(spark):
    df = spark.createDataFrame([
        sample_offer(id_hash="1", source="rekrute", entreprise="alten maroc", titre_brut="dev python"),
        sample_offer(id_hash="2", source="indeed_ma", entreprise="alten maroc", titre_brut="dev python"),
    ],schema=SCHEMA)
    result = deduplicate_cross_source(df)
    assert result.count() == 1

def test_dedup_keeps_different_markets(spark):
    df = spark.createDataFrame([
        sample_offer(id_hash="1", pays="MA", entreprise="capgemini", titre_brut="dev python"),
        sample_offer(id_hash="2", pays="FR", entreprise="capgemini", titre_brut="dev python"),
    ],schema=SCHEMA)
    result = deduplicate_cross_source(df)
    assert result.count() == 2

def test_dedup_keeps_different_titles_same_company(spark):
    df = spark.createDataFrame([
        sample_offer(id_hash="1", entreprise="alten maroc", titre_brut="python developer"),
        sample_offer(id_hash="2", entreprise="alten maroc", titre_brut="python developer senior"),
    ],schema=SCHEMA)
    result = deduplicate_cross_source(df)
    assert result.count() == 2