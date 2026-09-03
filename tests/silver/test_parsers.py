from services.silver.parsers import parse_experience, parse_education

class TestParseExperience:
    def test_years_with_extra_text(self):
        result = parse_experience("5 An(s) - Développement back-end")
        assert result[1] == "CONFIRME"
        assert result[2] == 5

    def test_months_converted_to_years(self):
        result = parse_experience("24 Mois")
        assert result[1] == "DEBUTANT"
        assert result[2] == 2.0

    def test_named_category_range(self):
        result = parse_experience("Intermédiaire (3 à 5 ans)")
        assert result[1] =="CONFIRME"

    def test_multiple_categories_keeps_lowest(self):
        result = parse_experience("Débutant (-1 an) | Très Senior (+20 ans)")
        assert result[1] == "DEBUTANT"

    def test_empty_string_returns_non_renseigne(self):
        result = parse_experience("")
        assert result[1] == "NON_RENSEIGNE"

    def test_unrecognized_text_returns_non_structure(self):
        result = parse_experience("Expérience exigée")
        assert result[1] == "NON_STRUCTURE"

class TestParseEducation:
    def test_bac_plus_n(self):
        result = parse_education("Bac +3")
        assert result[1] == "BAC+3"
        assert result[2] == 3

    def test_bac_plus_5_et_plus(self):
        result = parse_education("Bac +5 et plus")
        assert result[1] == "BAC+5"

    def test_infra_bac(self):
        result = parse_education("Qualification avant Bac")
        assert result[1] == "INFRA_BAC"

    def test_empty_returns_non_renseigne(self):
        result = parse_education("")
        assert result[1] == "NON_RENSEIGNE"