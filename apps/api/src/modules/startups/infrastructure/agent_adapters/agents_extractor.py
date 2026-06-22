"""Adaptador que liga o startups ao contrato publico do modulo agents.

Esta e a UNICA peca do modulo ``startups`` que conhece o Extraction Agent
de ``agents`` — e mesmo assim, conhece apenas o contrato publico
(``agents/application/public/extractor.py``). Nenhum node, grafo ou
prompt interno de ``agents`` e importado aqui.

Responsabilidade desta classe:

```txt
implementar a porta ExtractionPort (startups/application/ports.py)
traduzir os campos da startup -> ExtractionInput (agents)
traduzir ExtractionResult (agents) -> ExtractionOutcome (startups)
```

Cada modulo mantem seu proprio vocabulario (enums e DTOs). Esta classe e o
unico lugar onde os dois vocabularios se encontram.
"""

from apps.api.src.modules.agents.application.dto import ExtractionInput
from apps.api.src.modules.agents.application.public.extractor import (
    ExtractionService,
)
from apps.api.src.modules.startups.application.ports import (
    ExtractionOutcome,
    ExtractionPort,
)
from apps.api.src.modules.startups.domain.enums import FundingStage


class AgentsExtractor(ExtractionPort):
    """Implementa ``ExtractionPort`` chamando o modulo agents."""

    def __init__(self, extraction_service: ExtractionService) -> None:
        self.extraction_service = extraction_service

    async def extract(
        self,
        *,
        name: str,
        sector: str | None,
        description: str | None,
        evidence_texts: list[str],
    ) -> ExtractionOutcome:
        """Traduz a entrada, chama o agente e traduz a saida de volta."""

        agents_input = ExtractionInput(
            name=name,
            sector=sector,
            description=description,
            evidence_texts=evidence_texts,
        )
        agents_result = await self.extraction_service.extract(agents_input)

        # Os dois enums (``agents.ExtractedFundingStage`` e
        # ``startups.FundingStage``) compartilham os mesmos valores de
        # string, de proposito, para que esta traducao seja so uma troca
        # de tipo.
        funding_stage = FundingStage(agents_result.funding_stage.value)

        return ExtractionOutcome(
            founders=agents_result.founders,
            funding_stage=funding_stage,
            funding_amount_usd=agents_result.funding_amount_usd,
            customers=agents_result.customers,
        )
