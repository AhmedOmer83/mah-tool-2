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

    # Translate the text in real time (even for interim results)
    translated_text = translate_text(text, source_language, target_language)

    # Perform NER on both source and translated text
    entities_source = extract_filtered_entities(text)
    entities_translated = extract_filtered_entities(translated_text)

    # Assign red color to all entities
    entity_colors = assign_red_to_all(entities_source, entities_translated)

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
        # Translate small chunks of text in real time
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

        entities = []
        # Filter entities based on the required types and include entity type information
        for entity in response.entities:
            if entity.type_ in (
                    language_v1.Entity.Type.PERSON,       # Proper Names (Person)
                    language_v1.Entity.Type.ORGANIZATION, # Organization
                    language_v1.Entity.Type.LOCATION,     # Place
                    language_v1.Entity.Type.DATE,         # Time/Date
                    language_v1.Entity.Type.NUMBER,       # Numbers
                    language_v1.Entity.Type.PRICE         # Currency
            ):
                # Add both entity name and type for consistent color mapping
                entities.append((entity.name, entity.type_))

        return entities
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []

def assign_red_to_all(entities_source, entities_translated):
    """Assign the color red to all entities in both source and translated texts."""
    color_map = {}
    # Assign red color to all unique entities
    all_entities = entities_source + entities_translated
    for entity, entity_type in all_entities:
        color_map[entity] = 'red'  # Set the color red for all entities

    return color_map

def format_entities_with_colors(text, entities, color_map):
    """Format the text by highlighting entities with a single color (red)."""
    for entity, _ in entities:
        if entity in color_map:
            # Highlight entity using the assigned color (red) from color_map
            text = re.sub(f'\\b{entity}\\b', f'<span style="color:{color_map[entity]};">{entity}</span>', text, count=1)
    return text

if __name__ == '__main__':
    app.run(debug=True)
