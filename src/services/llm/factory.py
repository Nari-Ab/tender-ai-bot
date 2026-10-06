from src.core.config import Settings
from src.services.llm.base import LLMProvider
from src.services.llm.mock_llm import MockLLMProvider
from src.services.llm.gigachat import GigaChatProvider
from src.services.llm.yandexgpt import YandexGPTProvider
from src.core.logger import get_logger

logger = get_logger("llm_factory")


def get_llm_provider(config: Settings) -> LLMProvider:
    """
    Factory function to instantiate the selected LLM provider.
    Defaults to MockLLMProvider if credentials are not provided or provider is 'mock'.
    """
    provider_name = config.LLM_PROVIDER.lower().strip()

    if provider_name == "gigachat":
        if not config.GIGACHAT_CREDENTIALS:
            logger.warning("GIGACHAT_CREDENTIALS not set; using MockLLMProvider instead.")
            return MockLLMProvider()
        return GigaChatProvider(
            credentials=config.GIGACHAT_CREDENTIALS,
            scope=config.GIGACHAT_SCOPE,
            verify_ssl=config.GIGACHAT_VERIFY_SSL,
        )

    elif provider_name == "yandexgpt":
        if not config.YANDEX_API_KEY or not config.YANDEX_FOLDER_ID:
            logger.warning("YANDEX_API_KEY or YANDEX_FOLDER_ID not set; using MockLLMProvider instead.")
            return MockLLMProvider()
        return YandexGPTProvider(
            api_key=config.YANDEX_API_KEY,
            folder_id=config.YANDEX_FOLDER_ID,
            model_uri=config.YANDEX_MODEL_URI,
        )

    else:
        logger.info("Using offline MockLLMProvider for evaluation and tests.")
        return MockLLMProvider()
