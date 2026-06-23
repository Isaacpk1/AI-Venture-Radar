"use client";

import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";

import {
  getStartup,
  getStartupEvidences,
  listBriefings,
  listRecommendations,
  refreshStartupAnalysis,
} from "@/lib/api/radar-client";

function Field({ label, value }: { label: string; value: string | null }) {
  const displayValue = !value || value === "unknown" ? "Nao informado" : value;
  return <div><dt className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{label}</dt><dd className="mt-1">{displayValue}</dd></div>;
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

  return (
    <div className="mt-6 space-y-8">
      <section className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><h1 className="text-3xl font-semibold">{startup.name}</h1><p className="mt-2 max-w-3xl text-[var(--muted)]">{startup.description || fallbackDescription || "Descricao ainda nao disponivel."}</p></div>
          {startup.ai_maturity_level && <span className="rounded-full bg-[var(--accent)] px-3 py-1 text-sm font-semibold text-[#07111f]">{startup.ai_maturity_level.replaceAll("_", " ")}</span>}
        </div>
        <dl className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Setor" value={startup.sector} /><Field label="Pais" value={startup.country} />
          <Field label="Funding" value={startup.funding_stage} /><Field label="Fundadores" value={startup.founders.join(", ") || null} />
        </dl>
        {startup.website_url && <a className="mt-6 inline-block text-sm text-[var(--accent)] underline" href={startup.website_url} rel="noreferrer" target="_blank">Abrir fonte principal</a>}
      </section>

      <section className="grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6"><h2 className="text-xl font-semibold">Evidencias</h2>
          <div className="mt-5 space-y-4">{evidences.length ? evidences.map((evidence) => <article className="rounded-md border border-[var(--surface-border)] p-4" key={evidence.id}><a className="font-medium text-[var(--accent)] underline" href={evidence.source_url} rel="noreferrer" target="_blank">{evidence.title || evidence.source_url}</a><p className="mt-2 text-sm text-[var(--muted)]">{evidence.notes || "Evidencia coletada e aprovada pelo pipeline."}</p></article>) : <p className="text-[var(--muted)]">Nenhuma evidencia disponivel.</p>}</div>
        </div>
        <div className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6"><h2 className="text-xl font-semibold">Recomendacoes NVIDIA</h2>
          <div className="mt-5 space-y-4">{recommendations.length ? recommendations.map((recommendation) => <article className="rounded-md border border-[var(--surface-border)] p-4" key={recommendation.id}><div className="flex justify-between gap-4"><h3 className="font-medium">{recommendation.technology_name}</h3><span className="text-sm text-[var(--accent)]">{Math.round(recommendation.score * 100)}% fit</span></div><p className="mt-2 text-sm text-[var(--muted)]">{recommendation.justification}</p></article>) : <p className="text-[var(--muted)]">Nenhuma recomendacao foi gerada.</p>}</div>
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
        <div><h2 className="text-xl font-semibold">Atualizar analise</h2><p className="mt-1 text-sm text-[var(--muted)]">Recalcula as recomendacoes com as regras atuais e regenera o briefing.</p></div>
        <div className="text-right"><button className="rounded-md bg-[var(--accent)] px-5 py-3 font-semibold text-[#07111f] disabled:cursor-not-allowed disabled:opacity-60" disabled={refreshMutation.isPending} onClick={() => refreshMutation.mutate()} type="button">{refreshMutation.isPending ? "Atualizando..." : "Atualizar recomendacoes"}</button>{refreshMutation.isError && <p className="mt-2 text-sm text-[var(--danger)]">{refreshMutation.error.message}</p>}</div>
      </section>

      <section className="rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6"><h2 className="text-xl font-semibold">Briefing executivo</h2>
        {briefing ? <pre className="mt-5 whitespace-pre-wrap font-sans leading-7 text-[var(--muted)]">{briefing.content}</pre> : <p className="mt-5 text-[var(--muted)]">Briefing ainda nao disponivel.</p>}
      </section>
    </div>
  );
}
