"""Enums do modulo NVIDIA Knowledge."""

from enum import StrEnum


class NvidiaTechnologyCategory(StrEnum):
    """Categorias iniciais do catalogo NVIDIA."""

    MODEL_SERVING = "model_serving"
    MODEL_OPTIMIZATION = "model_optimization"
    MODEL_TRAINING = "model_training"
    DATA_SCIENCE = "data_science"
    SPEECH_AI = "speech_ai"
    ACCELERATED_COMPUTING = "accelerated_computing"
    AI_PLATFORM = "ai_platform"
    HEALTHCARE_AI = "healthcare_ai"
    STARTUP_PROGRAM = "startup_program"
    ROBOTICS_SIMULATION = "robotics_simulation"
    CYBERSECURITY = "cybersecurity"
