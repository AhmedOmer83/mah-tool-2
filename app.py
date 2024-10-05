from flask import Flask, render_template, request, jsonify
from google.cloud import language_v1, translate_v2

# Initialize Flask app
app = Flask(__name__)

# Initialize Google Cloud clients
language_client = language_v1.LanguageServiceClient()
translate_client = translate_v2.Client()

def get_entities(text):
    """
    Use Google Cloud Natural Language API to extract entities from the text.
    """
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = language_client.analyze_entities(document=document)

    # Prepare a list of entities to highlight
    entities = []
    for entity in response.entities:
        if entity.type_ in [language_v1.Entity.Type.PERSON, language_v1.Entity.Type.ORGANIZATION, language_v1.Entity.Type.LOCATION, language_v1.Entity.Type.DATE]:
            entities.append(entity.name)
    return entities

def translate_text(text, target_language):
    """
    Use Google Cloud Translate API to translate the given text to the target language.
    """
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

@app.route('/')
def home():
    # Render the frontend HTML page
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    text = data['text']
    source_language = data['sourceLanguage']
    target_language = data['targetLanguage']

    # 1. Get entities for the source text
    source_entities = get_entities(text)

    # 2. Highlight entities in the source text
    highlighted_source = text
    for entity in source_entities:
        highlighted_source = highlighted_source.replace(entity, f'<span class="entity">{entity}</span>')

    # 3. Translate the source text to the target language using Google Translate API
    translated_text = translate_text(text, target_language)

    # 4. Get entities for the translated text independently
    translated_entities = get_entities(translated_text)

    # 5. Highlight entities in the translated text based on detected entities in the translation itself
    highlighted_translation = translated_text
    for entity in translated_entities:
        highlighted_translation = highlighted_translation.replace(entity, f'<span class="entity">{entity}</span>')

    # 6. Return the highlighted text for both source and translation
    return jsonify({
        'sentencePairs': [{'source': highlighted_source, 'translation': highlighted_translation}]
    })

if __name__ == '__main__':
    app.run(debug=True)
