import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20">
      <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">Startup intelligence</p>
      <h1 className="max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
        Transforme uma URL em uma analise rastreavel para o ecossistema NVIDIA.
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)]">
        Coletamos evidencias, estruturamos o perfil da startup, classificamos a maturidade em IA e geramos recomendacoes e briefing executivo.
      </p>
      <div className="mt-10 flex flex-wrap gap-3">
        <Link className="inline-flex rounded-md bg-[var(--accent)] px-5 py-3 font-semibold text-[#07111f]" href="/analyze">Comecar uma analise</Link>
        <Link className="inline-flex rounded-md border border-[var(--surface-border)] px-5 py-3 font-semibold" href="/startups">Ver portfolio</Link>
      </div>
    </main>
  );
}
