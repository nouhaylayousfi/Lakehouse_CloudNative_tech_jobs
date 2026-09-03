def validate_silver(df):
    total = df.count()

    for champ in ["id_hash", "titre_brut", "source", "pays"]:
        n_null = df.filter(df[champ].isNull()).count()
        assert n_null == 0, f"{champ} contains {n_null} null values (expected: 0)"
    n_dupes = total - df.select("id_hash").distinct().count()
    assert n_dupes == 0, f"{n_dupes} duplicate id_hash values detected after deduplication"

    pays_invalides = df.filter(~df["pays"].isin("MA", "FR")).count()
    assert pays_invalides == 0, f"{pays_invalides} rows with invalid country"

    categories = {
        "niveau_experience_categorie": {"DEBUTANT", "CONFIRME", "SENIOR", "NON_STRUCTURE", "NON_RENSEIGNE"},
        "education_categorie": {"BAC", "BAC+1", "BAC+2", "BAC+3", "BAC+4", "BAC+5", "INFRA_BAC", "NON_STRUCTURE", "NON_RENSEIGNE"},
        "type_contrat_categorie": {"CDI", "CDD", "INTERIM", "STAGE", "FREELANCE", "NON_RENSEIGNE", "AUTRE"},
    }

    for champ , valeurs_valides in categories.items():
        if champ in df.columns:
            trouvees = {r[0] for r in df.select(champ).distinct().collect() if r[0] is not None}
            innattendues = trouvees - valeurs_valides
            assert not innattendues , f"Unexpected values in {champ}: {innattendues}"

    return True 