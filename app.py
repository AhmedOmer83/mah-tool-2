from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from google.cloud import language_v1, translate_v2
import threading
from functools import wraps  # For route protection

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management

# Initialize Google Cloud clients
language_client = language_v1.LanguageServiceClient()
translate_client = translate_v2.Client()

# Function to check login status before accessing any route
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Function to get filtered entities based on the required types
def get_entities(text):
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = language_client.analyze_entities(document=document)
    filtered_entities = []
    for entity in response.entities:
        if entity.type_ in [
            language_v1.Entity.Type.PERSON,
            language_v1.Entity.Type.ORGANIZATION,
            language_v1.Entity.Type.LOCATION,
            language_v1.Entity.Type.DATE
        ]:
            filtered_entities.append({"name": entity.name, "type": entity.type_.name})
    return filtered_entities

# Function to wrap entities with a span tag for highlighting
def highlight_entities(text, entities):
    for entity in entities:
        text = text.replace(entity['name'], f"<span class='entity'>{entity['name']}</span>")
    return text

# Function to translate text to the specified language using Google Cloud Translate API
def translate_text(text, target_language):
    translation = translate_client.translate(text, target_language=target_language)
    return translation['translatedText']

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Mahmoud' and password == 'Gaber123456!':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/process', methods=['POST'])
@login_required
def process_text():
    data = request.get_json()
    text = data['text']
    source_language = data['sourceLanguage']
    target_language = data['targetLanguage']
    translation_result = None
    entity_result = None
    translation_entities = None

    def translate():
        nonlocal translation_result
        translation_result = translate_text(text, target_language)

    def extract_entities():
        nonlocal entity_result
        entity_result = get_entities(text)

    # Create threads to perform translation and entity extraction simultaneously
    translation_thread = threading.Thread(target=translate)
    entity_thread = threading.Thread(target=extract_entities)
    translation_thread.start()
    entity_thread.start()
    translation_thread.join()
    entity_thread.join()

    if translation_result and entity_result:
        # Highlight the entities in the source text
        highlighted_text = highlight_entities(text, entity_result)

        # Extract and highlight entities in the translated text
        translation_entities = get_entities(translation_result)
        highlighted_translation = highlight_entities(translation_result, translation_entities)

        return jsonify({
            "sentencePairs": [{"source": highlighted_text, "translation": highlighted_translation}],
            "entities": entity_result
        })
    else:
        # Return an error if something went wrong
        return jsonify({"error": "Failed to process text."}), 500

@app.route('/process_interim', methods=['POST'])
@login_required
def process_interim_text():
    data = request.get_json()
    text = data['text']
    source_language = data['sourceLanguage']
    target_language = data['targetLanguage']
    translation_result = translate_text(text, target_language)

    return jsonify({
        "sentencePairs": [{"source": text, "translation": translation_result}]
    })

if __name__ == '__main__':
    app.run(debug=True)
