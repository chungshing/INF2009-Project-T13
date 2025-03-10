import sqlite3
from fuzzywuzzy import fuzz, process

def get_nutritional_values_local(dish_name, dish_mass):
    import sqlite3
    from fuzzywuzzy import fuzz, process

    conn = sqlite3.connect("nutritional_values.db")
    cursor = conn.cursor()
    dish_name_normalized = dish_name.lower().strip()

    query = "SELECT DISTINCT food_name FROM nutritional_values WHERE LOWER(food_name) LIKE ?"
    cursor.execute(query, (f"%{dish_name_normalized}%",))
    matching_dishes = [row[0] for row in cursor.fetchall()]

    if matching_dishes:
        best_match, match_score = process.extractOne(dish_name_normalized, matching_dishes, scorer=fuzz.token_set_ratio)
        if match_score >= 85:
            cursor.execute("SELECT nutrient, numeric_value, unit FROM nutritional_values WHERE food_name = ?", (best_match,))
            results = cursor.fetchall()
            if results:
                conn.close()
                return format_nutritional_values_dict(results, dish_mass)
    else:
        cursor.execute("SELECT DISTINCT food_name FROM nutritional_values")
        all_dishes = [row[0] for row in cursor.fetchall()]
        best_match, match_score = process.extractOne(dish_name_normalized, all_dishes, scorer=fuzz.token_set_ratio)
        if match_score >= 85:
            cursor.execute("SELECT nutrient, numeric_value, unit FROM nutritional_values WHERE food_name = ?", (best_match,))
            results = cursor.fetchall()
            if results:
                conn.close()
                return format_nutritional_values_dict(results, dish_mass)
    conn.close()
    return "Not found"

def format_nutritional_values_dict(results, dish_mass):
    """
    Given a list of tuples (nutrient, numeric_value, unit) from nutritional_values.db and a dish mass,
    returns a dictionary mapping each nutrient to its scaled value (assuming values are per 100g).
    """
    scale_factor = dish_mass / 100.0
    nutrient_dict = {}
    for nutrient, numeric_value, unit in results:
        try:
            nutrient_dict[nutrient] = float(numeric_value) * scale_factor
        except (ValueError, TypeError):
            nutrient_dict[nutrient] = 0.0
    return nutrient_dict
