from flask import Flask, render_template, request, jsonify
from google.cloud import translate_v2 as translate
from google.cloud import language_v1
import html
import re

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
    entities_source = extract_entities(text, source_language)
    entities_translated = extract_entities(translated_text, target_language)

    # Assign blue color to all entities in both source and target
    entity_colors = assign_colors(entities_source, entities_translated)

    # Split texts into sentences
    sentences_source = split_into_sentences(text)
    sentences_translated = split_into_sentences(translated_text)

    # Ensure both lists have the same length by padding with empty strings
    max_len = max(len(sentences_source), len(sentences_translated))
    sentences_source += [''] * (max_len - len(sentences_source))
    sentences_translated += [''] * (max_len - len(sentences_translated))

    # Format each sentence with NER entities highlighted
    formatted_pairs = []
    for src_sentence, tgt_sentence in zip(sentences_source, sentences_translated):
        formatted_src = format_entities_with_colors(src_sentence, entities_source, entity_colors)
        formatted_tgt = format_entities_with_colors(tgt_sentence, entities_translated, entity_colors)
        formatted_pairs.append({
            'source': formatted_src,
            'translation': formatted_tgt
        })

    # Send the response back to the frontend
    return jsonify({
        'sentencePairs': formatted_pairs
    })

def translate_text(text, source_language, target_language):
    """Translate the text using Google Cloud Translation API."""
    try:
        result = translate_client.translate(
            text,
            source_language=source_language,
            target_language=target_language,
            format_='text'  # Ensure text format
        )
        return result['translatedText']
    except Exception as e:
        print(f"Error during translation: {e}")
        return "Error translating text"

def extract_entities(text, language):
    """Extract named entities from the text using Google Cloud Natural Language API."""
    try:
        # Skip entity extraction for unsupported languages (like Arabic)
        unsupported_languages = ['ar']  # Add other unsupported language codes as needed
        if language in unsupported_languages:
            print(f"NER is not supported for the language '{language}'. Skipping entity extraction.")
            return []

        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT, language=language)
        response = language_client.analyze_entities(document=document)

        entities = []
        for entity in response.entities:
            # Only include PERSON, LOCATION, ORGANIZATION, and DATE entity types
            if entity.type_ in (
                    language_v1.Entity.Type.PERSON,
                    language_v1.Entity.Type.LOCATION,
                    language_v1.Entity.Type.ORGANIZATION,
                    language_v1.Entity.Type.DATE
            ):
                entities.append({
                    'name': entity.name,
                    'type': entity.type_
                })

        return entities
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []

def assign_colors(entities_source, entities_translated):
    """Assign the color blue to all entities."""
    color_map = {}

    # Assign blue color to every entity
    for entity in entities_source + entities_translated:
        entity_name = entity['name']
        color_map[entity_name] = "hsl(240, 100%, 50%)"  # Blue color for all entities

    return color_map

def format_entities_with_colors(text, entities, color_map):
    """Format the text by highlighting entities with colors."""
    if not text:
        return ""

    # Sort entities by length to prevent overlapping replacements
    sorted_entities = sorted(set(entity['name'] for entity in entities), key=len, reverse=True)

    for entity_name in sorted_entities:
        if entity_name in color_map:
            # Escape the entity name to avoid HTML injection
            escaped_entity = html.escape(entity_name)
            # Replace the entity in the text with its color-coded version (blue in this case)
            pattern = re.compile(r'\b{}\b'.format(re.escape(escaped_entity)), re.IGNORECASE)
            replacement = f'<span style="color:{color_map[entity_name]}; background-color: lightyellow;">{escaped_entity}</span>'
            text = pattern.sub(replacement, text)

    return text

def split_into_sentences(text):
    """
    Splits the input text into sentences using regex.
    Handles periods, exclamation points, and question marks.
    Avoids splitting on common abbreviations.
    If no punctuation is found, returns the entire text as one sentence.
    """
    # List of common abbreviations to prevent splitting
    abbreviations = [
        r'Mr\.', r'Mrs\.', r'Ms\.', r'Dr\.', r'Prof\.', r'Sr\.', r'Jr\.',
        r'i\.e\.', r'e\.g\.', r'vs\.', r'etc\.', r'U\.S\.', r'U\.K\.'  # Add more as needed
    ]

    # Combine the abbreviations into a single regex pattern
    abbrev_pattern = '|'.join(abbreviations)

    # Temporarily replace abbreviations with a placeholder to prevent splitting
    for abbrev in abbreviations:
        text = re.sub(abbrev, lambda x: x.group(0).replace('.', '<DOT>'), text)

    # Now split based on sentence-ending punctuation followed by a space
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)

    # Restore the dots in abbreviations
    sentences = [sentence.replace('<DOT>', '.') for sentence in sentences]

    # Remove any empty sentences
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    if not sentences:
        return [text.strip()]  # Return the entire text if no sentences are detected

    return sentences

if __name__ == '__main__':
    app.run(debug=True)
