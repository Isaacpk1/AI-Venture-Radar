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
  reviewBriefing,
  reviewRecommendation,
} from "@/lib/api/radar-client";
import type { Briefing, Recommendation, ReviewInput, Startup, StartupEvidence } from "@/lib/api/radar-types";

function Field({ label, value }: { label: string; value: string | null }) {
  const displayValue = !value || value === "unknown" ? "Nao informado" : value;
  return <div><dt className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{label}</dt><dd className="mt-1">{displayValue}</dd></div>;
}

const REVIEW_LABELS: Record<ReviewInput["status"], string> = {
  pending: "Pendente",
  approved: "Aprovado",
  rejected: "Rejeitado",
};

const REVIEW_CLASSES: Record<ReviewInput["status"], string> = {
  pending: "bg-[#20334d] text-[var(--muted)]",
  approved: "bg-[#183414] text-[var(--accent)]",
  rejected: "bg-[#4a1e25] text-[#ff9cab]",
};

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

function ReviewControls({
  currentStatus,
  currentComment,
  reviewedBy,
  reviewedAt,
  isPending,
  onReview,
}: {
  currentStatus: ReviewInput["status"];
  currentComment: string | null;
  reviewedBy: string | null;
  reviewedAt: string | null;
  isPending: boolean;
  onReview: (input: ReviewInput) => void;
}) {
  const [comment, setComment] = useState(currentComment ?? "");
  const [reviewer, setReviewer] = useState(reviewedBy ?? "");
  const submit = (status: ReviewInput["status"]) => {
    onReview({
      status,
      comment: comment.trim() || undefined,
      reviewed_by: reviewer.trim() || undefined,
    });
  };

  return (
    <div className="mt-4 border-t border-[var(--surface-border)] pt-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${REVIEW_CLASSES[currentStatus]}`}>
          {REVIEW_LABELS[currentStatus]}
        </span>
        {reviewedAt ? <span className="text-xs text-[var(--muted)]">Revisado por {reviewedBy || "analista"} em {new Date(reviewedAt).toLocaleDateString("pt-BR")}</span> : null}
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_180px]">
        <input
          className="rounded-md border border-[var(--surface-border)] bg-[#07111f] px-3 py-2 text-sm"
          onChange={(event) => setComment(event.target.value)}
          placeholder="Comentario da revisao"
          type="text"
          value={comment}
        />
        <input
          className="rounded-md border border-[var(--surface-border)] bg-[#07111f] px-3 py-2 text-sm"
          onChange={(event) => setReviewer(event.target.value)}
          placeholder="Revisor"
          type="text"
          value={reviewer}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="rounded-md bg-[var(--accent)] px-3 py-2 text-xs font-semibold text-[#07111f] disabled:opacity-60" disabled={isPending} onClick={() => submit("approved")} type="button">Aprovar</button>
        <button className="rounded-md border border-[#ff9cab] px-3 py-2 text-xs font-semibold text-[#ff9cab] disabled:opacity-60" disabled={isPending} onClick={() => submit("rejected")} type="button">Rejeitar</button>
        <button className="rounded-md border border-[var(--surface-border)] px-3 py-2 text-xs font-semibold text-[var(--muted)] disabled:opacity-60" disabled={isPending} onClick={() => submit("pending")} type="button">Reabrir</button>
      </div>
    </div>
  );
}

function RecommendationCard({ recommendation, evidences, startupId }: { recommendation: Recommendation; evidences: StartupEvidence[]; startupId: string }) {
  const [expanded, setExpanded] = useState(false);
  const queryClient = useQueryClient();
  const matchedEvidences = evidences.filter((evidence) => recommendation.evidence_ids.includes(evidence.id));
  const reviewMutation = useMutation({
    mutationFn: (input: ReviewInput) => reviewRecommendation(recommendation.id, input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["recommendations", startupId] });
    },
  });

  const complexityLabel: Record<string, string> = { low: "Baixa", medium: "Média", high: "Alta" };
  const complexityColor: Record<string, string> = {
    low: "bg-green-900/40 text-green-300",
    medium: "bg-yellow-900/40 text-yellow-300",
    high: "bg-red-900/40 text-red-300",
  };

  return (
    <article className="rounded-md border border-[var(--surface-border)] p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[var(--muted)]">#{recommendation.priority}</span>
          <h3 className="font-medium">{recommendation.technology_name}</h3>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${complexityColor[recommendation.complexity] ?? complexityColor.medium}`}>
            Complexidade {complexityLabel[recommendation.complexity] ?? recommendation.complexity}
          </span>
          <span className="text-sm text-[var(--accent)]">{Math.round(recommendation.score * 100)}% fit</span>
          <span className="text-xs text-[var(--muted)]" title="Confiança baseada na qualidade das evidências">
            {Math.round(recommendation.confidence * 100)}% conf.
          </span>
        </div>
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
      <ReviewControls
        currentComment={recommendation.review_comment}
        currentStatus={recommendation.review_status}
        isPending={reviewMutation.isPending}
        onReview={(input) => reviewMutation.mutate(input)}
        reviewedAt={recommendation.reviewed_at}
        reviewedBy={recommendation.reviewed_by}
      />
      {reviewMutation.isError ? <p className="mt-2 text-sm text-[var(--danger)]">{reviewMutation.error.message}</p> : null}
    </article>
  );
}

function BriefingReviewPanel({ briefing, startupId }: { briefing: Briefing; startupId: string }) {
  const queryClient = useQueryClient();
  const reviewMutation = useMutation({
    mutationFn: (input: ReviewInput) => reviewBriefing(briefing.id, input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["briefings", startupId] });
    },
  });

  return (
    <>
      <ReviewControls
        currentComment={briefing.review_comment}
        currentStatus={briefing.review_status}
        isPending={reviewMutation.isPending}
        onReview={(input) => reviewMutation.mutate(input)}
        reviewedAt={briefing.reviewed_at}
        reviewedBy={briefing.reviewed_by}
      />
      {reviewMutation.isError ? <p className="mt-2 text-sm text-[var(--danger)]">{reviewMutation.error.message}</p> : null}
    </>
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
          <div className="mt-5 space-y-4">{recommendations.length ? recommendations.map((recommendation) => <RecommendationCard evidences={evidences} key={recommendation.id} recommendation={recommendation} startupId={startupId} />) : <p className="text-[var(--muted)]">Nenhuma recomendacao foi gerada.</p>}</div>
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
        {briefing ? (
          <>
            <MarkdownContent className="mt-5 text-[var(--muted)]" content={briefing.content} />
            <BriefingReviewPanel briefing={briefing} startupId={startupId} />
          </>
        ) : <p className="mt-5 text-[var(--muted)]">Briefing ainda nao disponivel.</p>}
      </section>
    </div>
  );
}
