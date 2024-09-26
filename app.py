import re
from flask import Flask, render_template, request, jsonify
from google.cloud import translate_v2 as translate
from google.cloud import language_v1

app = Flask(__name__)

# Initialize Google Cloud clients
translate_client = translate.Client()
language_client = language_v1.LanguageServiceClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_text():
    data = request.json
    text = data.get('text')
    source_language = data.get('sourceLanguage')
    target_language = data.get('targetLanguage')

    # Translate the transcribed text
    translated_text = translate_text(text, source_language, target_language)

    # Perform NER on both source and translated text
    entities_source = extract_filtered_entities(text)
    entities_translated = extract_filtered_entities(translated_text)

    # Assign matching colors to the same entities in both source and translated texts
    entity_colors = assign_colors(entities_source, entities_translated)

    # Format the text with highlighted entities
    formatted_source_text = format_entities_with_colors(text, entities_source, entity_colors)
    formatted_translated_text = format_entities_with_colors(translated_text, entities_translated, entity_colors)

    return jsonify({
        'sourceText': formatted_source_text,
        'translatedText': formatted_translated_text
    })

def translate_text(text, source_language, target_language):
    """Translate the text using Google Cloud Translation API."""
    try:
        result = translate_client.translate(text, source_language=source_language, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        print(f"Error during translation: {e}")
        return "Error translating text"

def extract_filtered_entities(text):
    """Extract and filter relevant named entities from the text using Google Cloud Natural Language API."""
    try:
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
        response = language_client.analyze_entities(document=document)

        relevant_entities = []
        # Filter entities based on the required types
        for entity in response.entities:
            if entity.type_ in (
                    language_v1.Entity.Type.PERSON,       # Proper Names (Person)
                    language_v1.Entity.Type.ORGANIZATION, # Organization
                    language_v1.Entity.Type.LOCATION,     # Place
                    language_v1.Entity.Type.DATE,         # Time/Date
                    language_v1.Entity.Type.NUMBER,       # Numbers
                    language_v1.Entity.Type.PRICE         # Currency
            ):
                relevant_entities.append(entity.name)

        return relevant_entities
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []

def assign_colors(entities_source, entities_translated):
    """Assign matching colors to the same entities in source and translated text."""
    unique_entities = list(set(entities_source + entities_translated))  # Get unique entities from both texts
    color_map = {}

    for idx, entity in enumerate(unique_entities):
        # Assign a color to each unique entity
        color_map[entity] = f"hsl({(idx * 45) % 360}, 100%, 50%)"  # Use different hues

    return color_map

def format_entities_with_colors(text, entities, color_map):
    """Format the text by highlighting entities with colors but avoid duplication."""
    for entity in entities:
        if entity in color_map:
            # Ensure the entity is only highlighted once by limiting the replacement to the first occurrence
            text = re.sub(f'\\b{entity}\\b', f'<span style="color:{color_map[entity]};">{entity}</span>', text, count=1)
    return text

if __name__ == '__main__':
    app.run(debug=True)
