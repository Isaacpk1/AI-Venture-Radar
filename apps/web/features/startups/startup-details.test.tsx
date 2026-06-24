import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getStartup,
  getStartupEvidences,
  listBriefings,
  listRecommendations,
  refreshStartupAnalysis,
} from "@/lib/api/radar-client";
import type { Briefing, Recommendation, Startup, StartupEvidence } from "@/lib/api/radar-types";

import { StartupDetails } from "./startup-details";

vi.mock("@/lib/api/radar-client");

const mockedGetStartup = vi.mocked(getStartup);
const mockedGetEvidences = vi.mocked(getStartupEvidences);
const mockedListRecommendations = vi.mocked(listRecommendations);
const mockedListBriefings = vi.mocked(listBriefings);
const mockedRefresh = vi.mocked(refreshStartupAnalysis);

const STARTUP_ID = "11111111-1111-1111-1111-111111111111";

function baseStartup(overrides: Partial<Startup> = {}): Startup {
  return {
    id: STARTUP_ID,
    name: "Acme AI",
    website_url: "https://acme.example.com",
    description: "Plataforma de IA generativa para atendimento.",
    sector: "fintech",
    country: "BR",
    ai_maturity_level: "ai_native",
    classification_reason: null,
    classified_at: null,
    founders: ["Ana Silva"],
    funding_stage: "seed",
    funding_amount_usd: null,
    customers: [],
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    ...overrides,
  };
}

function renderWithClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("StartupDetails", () => {
  it("mostra estado de carregamento", () => {
    mockedGetStartup.mockReturnValue(new Promise(() => {}));
    mockedGetEvidences.mockReturnValue(new Promise(() => {}));
    mockedListRecommendations.mockReturnValue(new Promise(() => {}));
    mockedListBriefings.mockReturnValue(new Promise(() => {}));

    renderWithClient(<StartupDetails startupId={STARTUP_ID} />);

    expect(screen.getByText(/carregando resultado/i)).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando a busca da startup falha", async () => {
    mockedGetStartup.mockRejectedValue(new Error("startup indisponivel"));
    mockedGetEvidences.mockResolvedValue([]);
    mockedListRecommendations.mockResolvedValue([]);
    mockedListBriefings.mockResolvedValue([]);

    renderWithClient(<StartupDetails startupId={STARTUP_ID} />);

    expect(await screen.findByText("startup indisponivel")).toBeInTheDocument();
  });

  it("renderiza perfil, evidencias, recomendacoes e briefing quando populados", async () => {
    const evidence: StartupEvidence = {
      id: "ev-1",
      startup_id: STARTUP_ID,
      scraping_result_id: "sr-1",
      source_url: "https://acme.example.com/blog",
      evidence_type: "product_description",
      title: "Acme lanca produto de IA",
      confidence_score: 0.9,
      notes: "Evidencia coletada e aprovada pelo pipeline.",
      created_at: "2026-06-01T00:00:00Z",
    };
    const recommendation: Recommendation = {
      id: "rec-1",
      startup_id: STARTUP_ID,
      technology_slug: "nim",
      technology_name: "NVIDIA NIM",
      category: "inference",
      score: 0.8,
      justification: "Evidencias mencionam inferencia de modelos.",
      matched_keywords: ["inference"],
      evidence_ids: ["ev-1"],
      created_at: "2026-06-01T00:00:00Z",
    };
    const briefing: Briefing = {
      id: "brief-1",
      startup_id: STARTUP_ID,
      content: "# Briefing Executivo — Acme AI",
      generated_at: "2026-06-01T00:00:00Z",
    };

    mockedGetStartup.mockResolvedValue(baseStartup());
    mockedGetEvidences.mockResolvedValue([evidence]);
    mockedListRecommendations.mockResolvedValue([recommendation]);
    mockedListBriefings.mockResolvedValue([briefing]);

    renderWithClient(<StartupDetails startupId={STARTUP_ID} />);

    expect(await screen.findByText("Acme AI")).toBeInTheDocument();
    expect(screen.getByText("Acme lanca produto de IA")).toBeInTheDocument();
    expect(screen.getByText("NVIDIA NIM")).toBeInTheDocument();
    expect(screen.getByText(/Briefing Executivo/)).toBeInTheDocument();
  });

  it("mostra textos de fallback quando nao ha evidencia, recomendacao ou briefing", async () => {
    mockedGetStartup.mockResolvedValue(baseStartup({ description: null }));
    mockedGetEvidences.mockResolvedValue([]);
    mockedListRecommendations.mockResolvedValue([]);
    mockedListBriefings.mockResolvedValue([]);

    renderWithClient(<StartupDetails startupId={STARTUP_ID} />);

    expect(await screen.findByText("Nenhuma evidencia disponivel.")).toBeInTheDocument();
    expect(screen.getByText("Nenhuma recomendacao foi gerada.")).toBeInTheDocument();
    expect(screen.getByText("Briefing ainda nao disponivel.")).toBeInTheDocument();
  });

  it("aciona refreshStartupAnalysis ao clicar em atualizar recomendacoes", async () => {
    const user = userEvent.setup();
    mockedGetStartup.mockResolvedValue(baseStartup());
    mockedGetEvidences.mockResolvedValue([]);
    mockedListRecommendations.mockResolvedValue([]);
    mockedListBriefings.mockResolvedValue([]);
    mockedRefresh.mockResolvedValue({
      id: "brief-2",
      startup_id: STARTUP_ID,
      content: "novo briefing",
      generated_at: "2026-06-02T00:00:00Z",
    });

    renderWithClient(<StartupDetails startupId={STARTUP_ID} />);

    const button = await screen.findByRole("button", { name: /atualizar recomendacoes/i });
    await user.click(button);

    await waitFor(() => expect(mockedRefresh).toHaveBeenCalledWith(STARTUP_ID));
  });
});
