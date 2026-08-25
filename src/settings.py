from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class AzureAISettings(BaseSettings):
    """
    Configuration for Azure AI Foundry and model deployments.
    Uses pydantic_settings to load from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore'
    )
    
    # Azure AI Foundry Connection
    project_connection_string: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    api_version: str = "2026-04-01-preview"

    # Model Deployment Mapping
    # Reasoning models for strict constraint following and zero-leakage logic
    reasoning_deployment_name: str = "gpt-4o"  # or gpt-4.5 / gpt-5 
    
    # Bulk Lore Generation models with high token quotas
    bulk_lore_deployment_name: str = "gpt-4o-mini"
    
    # Semantic Distractor & Matching
    embedding_deployment_name: str = "text-embedding-3-large"
    
    # Multimodal Assets & Validation
    vision_deployment_name: str = "gpt-4o"
    image_generation_deployment: str = "dall-e-3"

    # Rate Limiting & Execution Config
    requests_per_minute: int = 500

settings = AzureAISettings()
