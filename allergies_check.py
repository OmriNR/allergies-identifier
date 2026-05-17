
import ollama

ALERGEN_DATABASE = ['Peanuts', 'Gluten', 'Sesame', 'Lactose']

def check_allergans(ingredients_list):
    prompt = f"""
        You're an professional nutritionist that specifies in allergies.
        Here is a common allergans source: {', '.join(ALERGEN_DATABASE)}

        Check this list of ingredients: {ingredients_list}

        Notify if there are any ingredients that can contain or be related to any allergans in the source

        Return the answer without any text in a JSON format in this pattern:
        {{
            'contains_allergans': true, false,
            'found_allergans': ['allergan 1', 'allergan 2'],
            'explanation': 'Short explanation'
        }}
    """

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{'role':'user', 'content': prompt}],
            options={'temperature':0}
        )

        return response['message']['content']
    except Exception as e:
        return f'Problem with model: {e}'