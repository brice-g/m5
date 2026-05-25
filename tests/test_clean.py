import pandas as pd
from src.pipeline.clean import drop_duplicates, normalise_text, handle_missing, flag_length_outliers, drop_invalid_rows

def test_drop_duplicates():
    data = {
        "input": ["Hello world", "Hello world", "Another input"],
        "reponse_suggeree": ["Response 1", "Response 1", "Response 2"]
    }
    df = pd.DataFrame(data)
    cleaned_df = drop_duplicates(df)
    assert len(cleaned_df) == 2
    assert cleaned_df.iloc[0]["input"] == "Hello world"
    assert cleaned_df.iloc[1]["input"] == "Another input"


def test_normalise_text():
    data = {
        "input": ["  Hello   world!  ", "Another   input"],
        "reponse_suggeree": ["Response 1", "Response 2"]
    }
    df = pd.DataFrame(data)
    cleaned_df = normalise_text(df)
    assert cleaned_df.iloc[0]["input"] == "Hello world!"
    assert cleaned_df.iloc[1]["input"] == "Another input"
    assert cleaned_df.iloc[0]["input_raw"] == "  Hello   world!  "
    assert cleaned_df.iloc[1]["input_raw"] == "Another   input"

def test_handle_missing():
    data = {
        "input": ["Hello world", "", "Another input", None],
        "reponse_suggeree": ["Response 1", "Response 2", None, "Response 4"]
    }
    df = pd.DataFrame(data)
    cleaned_df = handle_missing(df)
    assert len(cleaned_df) == 2
    assert cleaned_df.iloc[0]["input"] == "Hello world"
    assert cleaned_df.iloc[1]["input"] == "Another input"
    assert cleaned_df.iloc[0]["reponse_suggeree"] == "Response 1"
    assert cleaned_df.iloc[1]["reponse_suggeree"] == "Aucune réponse suggérée"

def test_flag_length_outliers():
    data = {
        "input": ["A", "Texte normal", "Texte normal", "Texte normal", "Ceci est un texte extrêmement long qui va forcément dépasser le seuil de l'IQR calculé sur les autres"],
        "reponse_suggeree": ["R1", "R2", "R3", "R4", "R5"]
    }
    df = pd.DataFrame(data)
    cleaned_df = flag_length_outliers(df)
    
    # Le dernier devrait être True
    assert cleaned_df.iloc[4]["is_length_outlier"] == True

def test_drop_invalid_rows():
    data = {
        "input": ["Short", "Valid input", "Another valid input", "Too short"],
        "reponse_suggeree": ["Response 1", "Response 2", "Response 3", "Response 4"]
    }
    df = pd.DataFrame(data)
    cleaned_df = drop_invalid_rows(df)
    assert len(cleaned_df) == 2
    assert cleaned_df.iloc[0]["input"] == "Valid input"
    assert cleaned_df.iloc[1]["input"] == "Another valid input"
