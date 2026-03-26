import threading
from django.apps import AppConfig

_tokenizer = None
_model = None
_loading_lock = threading.Lock()
_model_ready = threading.Event()

def _load_model_in_background():
    global _tokenizer, _model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print("[CUFitness] Loading chatbot model in background...")
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    _model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token
    _model_ready.set()
    print("[CUFitness] Chatbot model ready.")


def get_chatbot_model():
    """Wait for the background model load to finish, then return the model."""
    _model_ready.wait()  # blocks the chatbot request until model is ready
    return _tokenizer, _model


class CUFitnessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CUFitness'

    def ready(self):
        # Kick off model loading in a background thread so the server
        # starts immediately and doesn't block on the model download.
        t = threading.Thread(target=_load_model_in_background, daemon=True)
        t.start()