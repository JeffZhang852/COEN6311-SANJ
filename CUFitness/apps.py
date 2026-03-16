from django.apps import AppConfig
from transformers import AutoModelForCausalLM, AutoTokenizer


class CUFitnessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CUFitness'

    def ready(self):
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto" # Auto use GPU if available
        )
        # avoid warnings
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        CUFitnessConfig.tokenizer = self.tokenizer
        CUFitnessConfig.model = self.model
