"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { getUrlIngestionJob } from "@/lib/api/radar-client";

import { ORDERED_STATUSES as orderedStatuses, STATUS_LABELS as labels } from "./job-status-labels";

export function JobStatusPanel({ jobId }: { jobId: string }) {
  const query = useQuery({
    queryKey: ["url-ingestion-job", jobId],
    queryFn: () => getUrlIngestionJob(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 3000;
    },
  });

  if (query.isLoading) return <p className="mt-8 text-[var(--muted)]">Carregando job...</p>;
  if (query.isError) return <p className="mt-8 rounded-md border border-[var(--danger)] p-4 text-[var(--danger)]">{query.error.message}</p>;

  const job = query.data;
  if (!job) return <p className="mt-8 text-[var(--muted)]">Nenhum job encontrado.</p>;
  const currentIndex = orderedStatuses.indexOf(job.status);
  return (
    <section className="mt-8 rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
      <p className="text-sm text-[var(--muted)]">{job.url}</p>
      <p className="mt-2 text-xl font-semibold">{labels[job.status]}</p>
      <ol className="mt-8 space-y-3">
        {orderedStatuses.map((status, index) => (
          <li className="flex items-center gap-3" key={status}>
            <span className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold ${index <= currentIndex ? "bg-[var(--accent)] text-[#07111f]" : "bg-[#20334d] text-[var(--muted)]"}`}>{index + 1}</span>
            <span className={index <= currentIndex ? "text-white" : "text-[var(--muted)]"}>{labels[status]}</span>
          </li>
        ))}
      </ol>
      {job.status === "failed" && <p className="mt-6 rounded-md border border-[var(--danger)] p-4 text-[var(--danger)]">{job.error_message ?? "A analise falhou sem uma mensagem detalhada."}</p>}
      {job.status === "completed" && job.startup_id && (
        <Link className="mt-8 inline-flex rounded-md bg-[var(--accent)] px-5 py-3 font-semibold text-[#07111f]" href={`/startups/${job.startup_id}`}>
          Ver resultado da startup
        </Link>
      )}
    </section>
  );
}
