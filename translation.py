# Imports the Google Cloud Translation library
from google.cloud import translate_v3 as translate

DATASET_ID = "example-set818"  # change this to any dataset ID

def create_adaptive_mt_dataset():
    # Create a client
    client = translate.TranslationServiceClient()
    # Initialize request argument(s)
    adaptive_mt_dataset = translate.types.AdaptiveMtDataset()
    adaptive_mt_dataset.name = f"projects/mah-tool/locations/us-central1/adaptiveMtDatasets/{DATASET_ID}"
    adaptive_mt_dataset.display_name = "Example set"
    adaptive_mt_dataset.source_language_code = "en"
    adaptive_mt_dataset.target_language_code = "fr"
    request = translate.CreateAdaptiveMtDatasetRequest(
        parent="projects/mah-tool/locations/us-central1",
        adaptive_mt_dataset=adaptive_mt_dataset,
    )
    # Make the request
    response = client.create_adaptive_mt_dataset(request=request)
    # Handle the response
    print(response)

def import_adaptive_mt_file():
    # Create a client
    client = translate.TranslationServiceClient()

    # Initialize the request
    input_config = translate.types.InputConfig(
        gcs_source={"input_uri": "gs://your-bucket/path/to/file"}
    )
    request = translate.ImportAdaptiveMtDataRequest(
        parent="projects/mah-tool/locations/us-central1/adaptiveMtDatasets/{DATASET_ID}",
        input_config=input_config
    )

    # Make the request
    response = client.import_adaptive_mt_file(request=request)
    # Handle the response
    print(response)

def adaptive_mt_translate():
    text1 = """Cloud Translation API uses Google\'s neural machine translation technology to let you dynamically translate text through the API using Google pre-trained model, custom model, or a translation specialized large language model (LLMs)."""
    # Create a client
    client = translate.TranslationServiceClient()
    # Initialize the request
    request = translate.AdaptiveMtTranslateRequest(
        parent="projects/mah-tool/locations/us-central1",
        dataset=f"projects/mah-tool/locations/us-central1/adaptiveMtDatasets/{DATASET_ID}",
        content=[text1]
    )
    # Make the request
    response = client.adaptive_mt_translate(request=request)
    # Handle the response
    print(response)

# Run the functions
create_adaptive_mt_dataset()
import_adaptive_mt_file()
adaptive_mt_translate()
