"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { getUrlIngestionJob, listUrlIngestionJobs } from "@/lib/api/radar-client";
import type { UrlIngestionJob, UrlIngestionStatus } from "@/lib/api/radar-types";

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
  const relatedQuery = useQuery({
    enabled: Boolean(query.data),
    queryKey: ["url-ingestion-job-related", jobId, query.data?.startup_id],
    queryFn: () => listUrlIngestionJobs({ page: 1, page_size: 100, source_type: "startup_evidence" }),
    refetchInterval: (relatedQuery) => {
      const family = buildJobFamily(jobId, query.data, relatedQuery.state.data?.items ?? []);
      return hasRunningJob(family) ? 3000 : false;
    },
  });

  if (query.isLoading) return <p className="mt-8 text-[var(--muted)]">Carregando job...</p>;
  if (query.isError) return <p className="mt-8 rounded-md border border-[var(--danger)] p-4 text-[var(--danger)]">{query.error.message}</p>;

  const job = query.data;
  if (!job) return <p className="mt-8 text-[var(--muted)]">Nenhum job encontrado.</p>;
  const family = buildJobFamily(jobId, job, relatedQuery.data?.items ?? []);
  const displayJob = selectDisplayJob(job, family);
  const isRescuingFailedRoot = job.status === "failed" && displayJob.id !== job.id && displayJob.status !== "failed";
  const currentIndex = orderedStatuses.indexOf(displayJob.status);
  return (
    <section className="mt-8 rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] p-6">
      <p className="text-sm text-[var(--muted)]">{displayJob.url}</p>
      <p className="mt-2 text-xl font-semibold">{labels[displayJob.status]}</p>
      {isRescuingFailedRoot && (
        <p className="mt-3 rounded-md border border-[var(--surface-border)] bg-[#13233a] p-3 text-sm text-[var(--muted)]">
          A fonte inicial foi rejeitada, mas a analise continua com fontes de enriquecimento.
        </p>
      )}
      <ol className="mt-8 space-y-3">
        {orderedStatuses.map((status, index) => (
          <li className="flex items-center gap-3" key={status}>
            <span className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold ${index <= currentIndex ? "bg-[var(--accent)] text-[#07111f]" : "bg-[#20334d] text-[var(--muted)]"}`}>{index + 1}</span>
            <span className={index <= currentIndex ? "text-white" : "text-[var(--muted)]"}>{labels[status]}</span>
          </li>
        ))}
      </ol>
      {displayJob.status === "failed" && <p className="mt-6 rounded-md border border-[var(--danger)] p-4 text-[var(--danger)]">{displayJob.error_message ?? "A analise falhou sem uma mensagem detalhada."}</p>}
      {displayJob.status === "completed" && displayJob.startup_id && (
        <Link className="mt-8 inline-flex rounded-md bg-[var(--accent)] px-5 py-3 font-semibold text-[#07111f]" href={`/startups/${displayJob.startup_id}`}>
          Ver resultado da startup
        </Link>
      )}
    </section>
  );
}

const RUNNING_STATUSES = new Set<UrlIngestionStatus>(["pending", "scraping", "ingesting", "embedding", "analyzing"]);

function buildJobFamily(rootJobId: string, rootJob: UrlIngestionJob | undefined, jobs: UrlIngestionJob[]): UrlIngestionJob[] {
  if (!rootJob) return [];
  return [rootJob, ...jobs.filter((job) => job.parent_job_id === rootJobId && job.id !== rootJob.id)];
}

function hasRunningJob(jobs: UrlIngestionJob[]): boolean {
  return jobs.some((job) => RUNNING_STATUSES.has(job.status));
}

function selectDisplayJob(rootJob: UrlIngestionJob, family: UrlIngestionJob[]): UrlIngestionJob {
  const children = family.filter((job) => job.parent_job_id === rootJob.id);
  const completedChild = children.find((job) => job.status === "completed");
  if (completedChild) return completedChild;

  const runningChildren = children.filter((job) => RUNNING_STATUSES.has(job.status));
  if (runningChildren.length) {
    return runningChildren.sort((a, b) => orderedStatuses.indexOf(b.status) - orderedStatuses.indexOf(a.status))[0];
  }

  if (rootJob.status === "failed" && children.length) {
    const lastChild = [...children].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];
    return lastChild ?? rootJob;
  }

  return rootJob;
}
