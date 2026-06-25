"use client";

import { useState } from "react";
import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";

import { MarkdownContent } from "@/components/markdown-content";
import {
  getStartup,
  getStartupEvidences,
  listBriefings,
  listRecommendations,
  refreshStartupAnalysis,
} from "@/lib/api/radar-client";
import type { Briefing, Recommendation, Startup, StartupEvidence } from "@/lib/api/radar-types";

function Field({ label, value }: { label: string; value: string | null }) {
  const displayValue = !value || value === "unknown" ? "Nao informado" : value;
  return <div><dt className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{label}</dt><dd className="mt-1">{displayValue}</dd></div>;
}

const FIT_BADGE_TONE_CLASSES: Record<"ready" | "qualifying" | "needs-evidence", string> = {
  ready: "bg-[#183414] text-[var(--accent)]",
  qualifying: "bg-[#3a2c14] text-[#e8b84b]",
  "needs-evidence": "bg-[#20334d] text-[var(--muted)]",
};

/** Regra simples sobre dados que ja existem - sem chamada nova a API. */
function computeFitBadge(startup: Startup, recommendations: Recommendation[], briefing: Briefing | undefined) {
  const bestScore = recommendations.reduce((max, recommendation) => Math.max(max, recommendation.score), 0);
  if (startup.ai_maturity_level === "ai_native" && bestScore >= 0.5 && briefing) {
    return { label: "Pronto para contato", tone: "ready" as const };
  }
  if (bestScore >= 0.25) {
    return { label: "Em qualificacao", tone: "qualifying" as const };
  }
  return { label: "Precisa mais evidencia", tone: "needs-evidence" as const };
}

function RecommendationCard({ recommendation, evidences }: { recommendation: Recommendation; evidences: StartupEvidence[] }) {
  const [expanded, setExpanded] = useState(false);
  const matchedEvidences = evidences.filter((evidence) => recommendation.evidence_ids.includes(evidence.id));

  return (
    <article className="rounded-md border border-[var(--surface-border)] p-4">
      <div className="flex justify-between gap-4">
        <h3 className="font-medium">{recommendation.technology_name}</h3>
        <span className="text-sm text-[var(--accent)]">{Math.round(recommendation.score * 100)}% fit</span>
      </div>
      <MarkdownContent className="mt-2 text-sm text-[var(--muted)] [&_p]:mt-0" content={recommendation.justification} />
      {recommendation.matched_keywords.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {recommendation.matched_keywords.map((keyword) => <span className="rounded-full bg-[#20334d] px-2 py-1 text-xs text-[var(--muted)]" key={keyword}>{keyword}</span>)}
        </div>
      )}
      <button className="mt-3 text-xs font-semibold text-[var(--accent)] underline" onClick={() => setExpanded((current) => !current)} type="button">
        {expanded ? "Ocultar evidencia" : "Ver evidencia"}
      </button>
      {expanded && (
        <div className="mt-3 space-y-2 border-t border-[var(--surface-border)] pt-3">
          {matchedEvidences.length ? matchedEvidences.map((evidence) => (
            <a className="block text-sm text-[var(--accent)] underline" href={evidence.source_url} key={evidence.id} rel="noreferrer" target="_blank">
              {evidence.title || evidence.source_url}
            </a>
          )) : <p className="text-sm text-[var(--muted)]">Sem evidencia especifica vinculada a esta recomendacao.</p>}
        </div>
      )}
    </article>
  );
}

export function StartupDetails({ startupId }: { startupId: string }) {
  const queryClient = useQueryClient();
  const [startupQuery, evidencesQuery, recommendationsQuery, briefingsQuery] = useQueries({
    queries: [
      { queryKey: ["startup", startupId], queryFn: () => getStartup(startupId) },
      { queryKey: ["startup-evidences", startupId], queryFn: () => getStartupEvidences(startupId) },
      { queryKey: ["recommendations", startupId], queryFn: () => listRecommendations(startupId) },
      { queryKey: ["briefings", startupId], queryFn: () => listBriefings(startupId) },
    ],
  });
  const refreshMutation = useMutation({
    mutationFn: () => refreshStartupAnalysis(startupId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["recommendations", startupId] }),
        queryClient.invalidateQueries({ queryKey: ["briefings", startupId] }),
      ]);
    },
  });

  if (startupQuery.isLoading) return <p className="mt-8 text-[var(--muted)]">Carregando resultado...</p>;
  if (startupQuery.isError) return <p className="mt-8 rounded-md border border-[var(--danger)] p-4 text-[var(--danger)]">{startupQuery.error.message}</p>;

  const startup = startupQuery.data;
  if (!startup) return <p className="mt-8 text-[var(--muted)]">Startup nao encontrada.</p>;
  const evidences = evidencesQuery.data ?? [];
  const recommendations = recommendationsQuery.data ?? [];
  const briefing = briefingsQuery.data?.[0];
  const fallbackDescription = evidences[0]?.notes?.replace(/\s+/g, " ").slice(0, 420);
  const fitBadge = computeFitBadge(startup, recommendations, briefing);

  return (
    <div className="mt-6 space-y-8">
      <section className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><h1 className="text-3xl font-semibold">{startup.name}</h1><p className="mt-2 max-w-3xl text-[var(--muted)]">{startup.description || fallbackDescription || "Descricao ainda nao disponivel."}</p></div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-3 py-1 text-sm font-semibold ${FIT_BADGE_TONE_CLASSES[fitBadge.tone]}`}>{fitBadge.label}</span>
            {startup.ai_maturity_level && <span className="rounded-full bg-[var(--accent)] px-3 py-1 text-sm font-semibold text-[#07111f]">{startup.ai_maturity_level.replaceAll("_", " ")}</span>}
          </div>
        </div>
        <dl className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Setor" value={startup.sector} /><Field label="Pais" value={startup.country} />
          <Field label="Funding" value={startup.funding_stage} /><Field label="Fundadores" value={startup.founders.join(", ") || null} />
          <Field label="Clientes" value={startup.customers.join(", ") || null} />
        </dl>
        {startup.website_url && <a className="mt-6 inline-block text-sm text-[var(--accent)] underline" href={startup.website_url} rel="noreferrer" target="_blank">Abrir fonte principal</a>}
      </section>

      <section className="grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6"><h2 className="text-xl font-semibold">Evidencias</h2>
          <div className="mt-5 space-y-4">{evidences.length ? evidences.map((evidence) => <article className="rounded-md border border-[var(--surface-border)] p-4" key={evidence.id}><a className="font-medium text-[var(--accent)] underline" href={evidence.source_url} rel="noreferrer" target="_blank">{evidence.title || evidence.source_url}</a><p className="mt-2 text-sm text-[var(--muted)]">{evidence.notes || "Evidencia coletada e aprovada pelo pipeline."}</p></article>) : <p className="text-[var(--muted)]">Nenhuma evidencia disponivel.</p>}</div>
        </div>
        <div className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6"><h2 className="text-xl font-semibold">Recomendacoes NVIDIA</h2>
          <div className="mt-5 space-y-4">{recommendations.length ? recommendations.map((recommendation) => <RecommendationCard evidences={evidences} key={recommendation.id} recommendation={recommendation} />) : <p className="text-[var(--muted)]">Nenhuma recomendacao foi gerada.</p>}</div>
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
        <div><h2 className="text-xl font-semibold">Atualizar analise</h2><p className="mt-1 text-sm text-[var(--muted)]">Recalcula as recomendacoes com as regras atuais e regenera o briefing.</p></div>
        <div className="text-right"><button className="rounded-md bg-[var(--accent)] px-5 py-3 font-semibold text-[#07111f] disabled:cursor-not-allowed disabled:opacity-60" disabled={refreshMutation.isPending} onClick={() => refreshMutation.mutate()} type="button">{refreshMutation.isPending ? "Atualizando..." : "Atualizar recomendacoes"}</button>{refreshMutation.isError && <p className="mt-2 text-sm text-[var(--danger)]">{refreshMutation.error.message}</p>}</div>
      </section>

      <section className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">Briefing executivo</h2>
          {briefing && <a className="rounded-md border border-[var(--surface-border)] px-4 py-2 text-sm font-semibold text-[var(--accent)]" href={`/api/radar/briefings/${briefing.id}/export`}>Exportar PDF</a>}
        </div>
        {briefing ? <MarkdownContent className="mt-5 text-[var(--muted)]" content={briefing.content} /> : <p className="mt-5 text-[var(--muted)]">Briefing ainda nao disponivel.</p>}
      </section>
    </div>
  );
}
