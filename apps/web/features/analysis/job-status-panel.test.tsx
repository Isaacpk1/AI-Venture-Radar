import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getUrlIngestionJob } from "@/lib/api/radar-client";
import type { UrlIngestionJob } from "@/lib/api/radar-types";

import { JobStatusPanel } from "./job-status-panel";

vi.mock("@/lib/api/radar-client");
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const mockedGetJob = vi.mocked(getUrlIngestionJob);

const JOB_ID = "22222222-2222-2222-2222-222222222222";

function baseJob(overrides: Partial<UrlIngestionJob> = {}): UrlIngestionJob {
  return {
    id: JOB_ID,
    url: "https://acme.example.com",
    source_type: "startup_evidence",
    status: "pending",
    scraping_job_id: null,
    scraping_result_id: null,
    ingestion_job_id: null,
    document_id: null,
    embedding_job_id: null,
    startup_id: null,
    recommendation_count: null,
    briefing_id: null,
    error_message: null,
    created_at: "2026-06-01T00:00:00Z",
    started_at: null,
    finished_at: null,
    ...overrides,
  };
}

function renderWithClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("JobStatusPanel", () => {
  it("mostra estado de carregamento", () => {
    mockedGetJob.mockReturnValue(new Promise(() => {}));

    renderWithClient(<JobStatusPanel jobId={JOB_ID} />);

    expect(screen.getByText(/carregando job/i)).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando a busca falha", async () => {
    mockedGetJob.mockRejectedValue(new Error("job indisponivel"));

    renderWithClient(<JobStatusPanel jobId={JOB_ID} />);

    expect(await screen.findByText("job indisponivel")).toBeInTheDocument();
  });

  it("mostra a timeline para um job pendente", async () => {
    mockedGetJob.mockResolvedValue(baseJob({ status: "pending" }));

    renderWithClient(<JobStatusPanel jobId={JOB_ID} />);

    // "Na fila" aparece 2x na tela (titulo + 1o item da timeline) - usar
    // getAllByText em vez de findByText (que exige match unico).
    expect(await screen.findAllByText("Na fila")).toHaveLength(2);
    expect(screen.getByText("Coletando fonte")).toBeInTheDocument();
  });

  it("mostra a mensagem de erro para um job falho", async () => {
    mockedGetJob.mockResolvedValue(
      baseJob({ status: "failed", error_message: "scraping rejeitado" }),
    );

    renderWithClient(<JobStatusPanel jobId={JOB_ID} />);

    expect(await screen.findByText("scraping rejeitado")).toBeInTheDocument();
  });

  it("mostra link para o resultado quando o job conclui com startup_id", async () => {
    mockedGetJob.mockResolvedValue(
      baseJob({ status: "completed", startup_id: "startup-1" }),
    );

    renderWithClient(<JobStatusPanel jobId={JOB_ID} />);

    const link = await screen.findByRole("link", { name: /ver resultado da startup/i });
    expect(link).toHaveAttribute("href", "/startups/startup-1");
  });
});
