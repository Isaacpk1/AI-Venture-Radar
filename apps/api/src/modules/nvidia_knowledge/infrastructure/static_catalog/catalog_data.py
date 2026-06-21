"""Dados iniciais do catalogo NVIDIA Knowledge V1."""

from apps.api.src.modules.nvidia_knowledge.domain.entities import NvidiaTechnology
from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)


INITIAL_NVIDIA_TECHNOLOGIES: tuple[NvidiaTechnology, ...] = (
    NvidiaTechnology(
        slug="nvidia-nim",
        name="NVIDIA NIM",
        category=NvidiaTechnologyCategory.MODEL_SERVING,
        description=(
            "Microservicos para acelerar o deploy de foundation models e "
            "modelos generativos em cloud, data center ou workstation."
        ),
        use_cases=(
            "servir LLMs e modelos generativos em producao",
            "expor APIs de inferencia padronizadas",
            "reduzir tempo de deploy de modelos",
        ),
        keywords=(
            "llm",
            "generative ai",
            "inference",
            "api",
            "deployment",
            "microservice",
        ),
        official_url="https://docs.nvidia.com/nim/",
    ),
    NvidiaTechnology(
        slug="nvidia-nemo",
        name="NVIDIA NeMo",
        category=NvidiaTechnologyCategory.MODEL_TRAINING,
        description=(
            "Framework e suite modular para criar, customizar e otimizar "
            "modelos de IA generativa, speech e agentes."
        ),
        use_cases=(
            "fine-tuning de modelos generativos",
            "treinamento e customizacao de modelos de linguagem",
            "ciclo de vida de agentes e modelos corporativos",
        ),
        keywords=(
            "training",
            "fine tuning",
            "llm",
            "agent",
            "generative ai",
            "speech",
        ),
        official_url=(
            "https://docs.nvidia.com/nemo-framework/user-guide/latest/overview.html"
        ),
    ),
    NvidiaTechnology(
        slug="triton-inference-server",
        name="NVIDIA Triton Inference Server",
        category=NvidiaTechnologyCategory.MODEL_SERVING,
        description=(
            "Servidor de inferencia para publicar modelos de diferentes "
            "frameworks com batching, multiplos backends e observabilidade."
        ),
        use_cases=(
            "serving multi-modelo em producao",
            "inferencias com baixa latencia e alto throughput",
            "padronizar deploy de modelos em Kubernetes ou data center",
        ),
        keywords=(
            "model serving",
            "kubernetes",
            "inference",
            "batching",
            "pytorch",
            "onnx",
        ),
        official_url=(
            "https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/"
        ),
    ),
    NvidiaTechnology(
        slug="tensorrt-llm",
        name="TensorRT-LLM",
        category=NvidiaTechnologyCategory.MODEL_OPTIMIZATION,
        description=(
            "Toolkit para otimizar e executar inferencia de LLMs em GPUs "
            "NVIDIA com foco em throughput e eficiencia."
        ),
        use_cases=(
            "otimizar inferencia de LLMs",
            "reduzir custo por token em producao",
            "servir modelos generativos com alta eficiencia",
        ),
        keywords=(
            "llm",
            "optimization",
            "inference",
            "throughput",
            "token",
            "quantization",
        ),
        official_url="https://nvidia.github.io/TensorRT-LLM/",
    ),
    NvidiaTechnology(
        slug="tensorrt",
        name="NVIDIA TensorRT",
        category=NvidiaTechnologyCategory.MODEL_OPTIMIZATION,
        description=(
            "SDK para otimizar e acelerar inferencia de deep learning em GPUs "
            "NVIDIA, com suporte a precisao mista e formas dinamicas."
        ),
        use_cases=(
            "otimizar modelos PyTorch, TensorFlow ou ONNX",
            "reduzir latencia de inferencia",
            "acelerar workloads de visao computacional e transformers",
        ),
        keywords=(
            "onnx",
            "pytorch",
            "tensorflow",
            "optimization",
            "latency",
            "inference",
        ),
        official_url=(
            "https://docs.nvidia.com/deeplearning/tensorrt/latest/index.html"
        ),
    ),
    NvidiaTechnology(
        slug="rapids",
        name="RAPIDS",
        category=NvidiaTechnologyCategory.DATA_SCIENCE,
        description=(
            "Ecossistema de bibliotecas para acelerar ciencia de dados e "
            "analytics em GPUs, incluindo dataframes e machine learning."
        ),
        use_cases=(
            "acelerar pipelines de data science",
            "processar grandes volumes de dados tabulares",
            "migrar workloads pandas/scikit-learn para GPU",
        ),
        keywords=(
            "data science",
            "analytics",
            "dataframe",
            "gpu",
            "pandas",
            "spark",
        ),
        official_url="https://docs.rapids.ai/",
    ),
    NvidiaTechnology(
        slug="riva",
        name="NVIDIA Riva",
        category=NvidiaTechnologyCategory.SPEECH_AI,
        description=(
            "SDK para IA conversacional e speech, incluindo reconhecimento de "
            "fala, sintese de voz e traducao neural."
        ),
        use_cases=(
            "automatic speech recognition",
            "text-to-speech",
            "traducao e assistentes de voz",
        ),
        keywords=(
            "speech",
            "asr",
            "tts",
            "voice",
            "translation",
            "conversational ai",
        ),
        official_url="https://docs.nvidia.com/deeplearning/riva/user-guide/docs/index.html",
    ),
    NvidiaTechnology(
        slug="cuda",
        name="NVIDIA CUDA",
        category=NvidiaTechnologyCategory.ACCELERATED_COMPUTING,
        description=(
            "Plataforma e toolkit de computacao acelerada para desenvolver "
            "aplicacoes C/C++ e bibliotecas que usam GPUs NVIDIA."
        ),
        use_cases=(
            "acelerar computacao numerica",
            "criar kernels GPU customizados",
            "otimizar workloads cientificos e de engenharia",
        ),
        keywords=(
            "gpu",
            "accelerated computing",
            "c++",
            "kernel",
            "hpc",
            "parallel computing",
        ),
        official_url="https://docs.nvidia.com/cuda/",
    ),
    NvidiaTechnology(
        slug="nvidia-ai-enterprise",
        name="NVIDIA AI Enterprise",
        category=NvidiaTechnologyCategory.AI_PLATFORM,
        description=(
            "Plataforma empresarial para desenvolver, implantar e operar "
            "aplicacoes de IA com suporte, frameworks, NIM e SDKs."
        ),
        use_cases=(
            "padronizar stack corporativa de IA",
            "operar IA em ambiente enterprise",
            "combinar frameworks, NIM e infraestrutura GPU",
        ),
        keywords=(
            "enterprise",
            "platform",
            "governance",
            "deployment",
            "support",
            "infrastructure",
        ),
        official_url="https://docs.nvidia.com/ai-enterprise/",
    ),
    NvidiaTechnology(
        slug="monai",
        name="MONAI",
        category=NvidiaTechnologyCategory.HEALTHCARE_AI,
        description=(
            "Toolkit para workflows de IA medica, com foco em imagens, "
            "treinamento, inferencia e deploy em healthcare."
        ),
        use_cases=(
            "analise de imagens medicas",
            "segmentacao e classificacao em healthcare",
            "pipelines de IA clinica e pesquisa medica",
        ),
        keywords=(
            "healthcare",
            "medical imaging",
            "monai",
            "segmentation",
            "radiology",
            "clinical ai",
        ),
        official_url="https://docs.nvidia.com/clara/monai/",
    ),
)
