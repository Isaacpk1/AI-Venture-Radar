"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStartup, listRecommendations } from "@/lib/api/radar-client";

type CompareSlot = { startupId: string };

function maturityLabel(level: string | null) {
  if (!level) return "Sem classificação";
  return { ai_native: "AI-Native", ai_enabled: "AI-Enabled", non_ai: "Non-AI" }[level] ?? level;
}

function maturityColor(level: string | null) {
  return {
    ai_native: "bg-green-100 text-green-800",
    ai_enabled: "bg-blue-100 text-blue-800",
    non_ai: "bg-gray-100 text-gray-600",
  }[level ?? ""] ?? "bg-gray-100 text-gray-500";
}

function StartupCard({ startupId }: CompareSlot) {
  const { data: startup, isLoading: loadingStartup } = useQuery({
    queryKey: ["startup", startupId],
    queryFn: () => getStartup(startupId),
    enabled: !!startupId,
  });

  const { data: recs, isLoading: loadingRecs } = useQuery({
    queryKey: ["recommendations", startupId],
    queryFn: () => listRecommendations(startupId),
    enabled: !!startupId,
  });

  if (loadingStartup || loadingRecs) {
    return <div className="p-4 text-gray-400 text-sm">Carregando...</div>;
  }
  if (!startup) {
    return <div className="p-4 text-red-400 text-sm">Startup não encontrada.</div>;
  }

  const bestRec = recs?.sort((a, b) => b.score - a.score)[0];

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h3 className="font-semibold text-gray-900 truncate">{startup.name}</h3>
        {startup.website_url && (
          <a
            href={startup.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-500 hover:underline truncate block"
          >
            {startup.website_url}
          </a>
        )}
      </div>

      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium w-fit ${maturityColor(startup.ai_maturity_level)}`}>
        {maturityLabel(startup.ai_maturity_level)}
      </span>

      {startup.sector && (
        <p className="text-xs text-gray-500">Setor: {startup.sector}</p>
      )}

      {bestRec ? (
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-500 mb-1">Melhor recomendação</p>
          <p className="text-sm font-semibold text-gray-800">{bestRec.technology_name}</p>
          <p className="text-xs text-gray-500">Score: {(bestRec.score * 100).toFixed(0)}%</p>
        </div>
      ) : (
        <p className="text-xs text-gray-400">Sem recomendações geradas.</p>
      )}

      <div>
        <p className="text-xs font-medium text-gray-500 mb-1">
          Recomendações ({recs?.length ?? 0})
        </p>
        <div className="flex flex-wrap gap-1">
          {recs?.slice(0, 5).map((r) => (
            <span
              key={r.id}
              className="text-xs bg-nvidia-green/10 text-green-800 rounded px-2 py-0.5"
            >
              {r.technology_name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function CompareInput({
  index,
  value,
  onChange,
}: {
  index: number;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-500">
        Startup {index + 1} — ID
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Cole o ID da startup aqui"
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
      />
    </div>
  );
}

export function StartupCompare() {
  const [ids, setIds] = useState(["", "", ""]);
  const activeIds = ids.filter((id) => id.trim().length > 0);

  const update = (i: number, v: string) =>
    setIds((prev) => prev.map((old, idx) => (idx === i ? v : old)));

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
        Comparação de Startups
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {ids.map((id, i) => (
          <CompareInput key={i} index={i} value={id} onChange={(v) => update(i, v)} />
        ))}
      </div>

      {activeIds.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-8">
          Insira os IDs das startups acima para comparar lado a lado.
        </p>
      ) : (
        <div
          className="grid gap-6"
          style={{ gridTemplateColumns: `repeat(${activeIds.length}, 1fr)` }}
        >
          {activeIds.map((id) => (
            <div key={id} className="border border-gray-100 rounded-lg p-4">
              <StartupCard startupId={id} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
