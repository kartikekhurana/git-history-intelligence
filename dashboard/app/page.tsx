"use client"

import { useCallback, useEffect, useState } from "react";
import { analyzeRepo, parseRepo, type Analysis } from "@/lib/api";
import { CouplingCard } from "@/components/CouplingCard";
import { HotspotsCard } from "@/components/HotspotsCard";
import { PrRiskCard } from "@/components/PrRiskCard";
import { BusFactorCard } from "@/components/BusFactorCard";

const WINDOWS = [
  { label: "6 mo", months: 6 },
  { label: "12 mo", months: 12 },
  { label: "24 mo", months: 24 },
  { label: "All time", months: 600 },
];

export default function Home(){

  const [input , setInput] = useState("expressjs/express")
  const [months, setMonths] = useState(24);
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  const run = useCallback(async (repoInput : string , windowMonths : number) => {
    const repo = parseRepo(repoInput)
    if(!repo){
      setError("Enter a repo like owner/name or a GitHub URL.");
      return;
    }
    setLoading(true)
    setError(null)
    const started = performance.now()
    try{
      const result = await analyzeRepo(repo.owner , repo.name , windowMonths)
      setData(result)
      setElapsed(Math.round(performance.now() - started));
    }catch(err){
      setError(err instanceof Error ? err.message : "Something went wrong.")
    }finally{
      setLoading(false)
    }
  },[])

 useEffect(() => {
  let ignore = false;
  const started = performance.now();

  analyzeRepo("expressjs", "express", 24)
    .then((result) => {
      if (ignore) return;
      setData(result);
      setElapsed(Math.round(performance.now() - started));
    })
    .catch((err) => {
      if (!ignore) setError(err instanceof Error ? err.message : "Something went wrong.");
    })
    .finally(() => {
      if (!ignore) setLoading(false);
    });

  return () => {
    ignore = true;
  };
}, []);

  return (
      <div className="min-h-screen">
      <header className="border-b border-zinc-900">
        <div className="mx-auto flex h-14 max-w-5xl items-center px-6 font-semibold tracking-tight">
          Git History Intelligence
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 pb-16">
        <section className="pt-16">
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight">
            Know where your codebase is fragile.
          </h1>
          <p className="mt-3 max-w-xl text-[15px] text-zinc-400">
            Paste a GitHub repo. Get hotspots, hidden coupling, and ownership risk, built from
            commit history alone.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              run(input, months);
            }}
            className="mt-7 flex flex-wrap gap-2.5"
          >
            <label htmlFor="repo" className="sr-only">
              Repository
            </label>
            <div className="flex h-12 min-w-80 flex-1 items-center rounded-xl border border-zinc-800 bg-zinc-950 px-4 font-mono text-sm">
              <span className="text-zinc-500">github.com/</span>
              <input
                id="repo"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                spellCheck={false}
                className="min-w-0 flex-1 bg-transparent outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="h-12 rounded-xl bg-zinc-100 px-6 text-sm font-semibold text-zinc-950 disabled:opacity-60"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </form>

          <div className="mt-3.5 inline-flex rounded-lg border border-zinc-800 bg-zinc-950 p-0.5">
            {WINDOWS.map((w) => (
              <button
                key={w.months}
                type="button"
                onClick={() => {
                  setMonths(w.months);
                  run(input, w.months);
                }}
                className={`rounded-md px-4 py-1.5 text-[13px] font-medium ${
                  months === w.months ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {w.label}
              </button>
            ))}
          </div>
        </section>

        {error && (
          <p
            role="alert"
            className="mt-6 rounded-lg border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300"
          >
            {error}
          </p>
        )}

        {data && (
          <section
            className={`mt-10 flex flex-wrap gap-11 border-t border-zinc-900 pt-6 ${
              loading ? "opacity-50" : ""
            }`}
          >
            <Stat value={data.commit_count.toLocaleString()} label="commits analyzed" />
            <Stat
              value={data.recent_commit_count.toLocaleString()}
              label={
                data.window_months >= 600
                  ? "commits in window (all time)"
                  : `commits in the last ${data.window_months} months`
              }
            />
            <Stat value={`${elapsed} ms`} label="response time" />
          </section>
        )}
        {data && data.commit_count < 30 && (
          <p className="mt-6 rounded-lg border border-amber-900/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-200/90">
            Only {data.commit_count} commits in this repo, so these results are low confidence.
            Patterns need more history to show up.
          </p>
        )}
        {data && (
          <div className={`mt-6 grid gap-4 md:grid-cols-2 ${loading ? "opacity-50" : ""}`}>
            <HotspotsCard items={data.hotspots} />
            <CouplingCard items={data.coupling} />
          </div>
        )}
        {
          data &&(
                <div className={`mt-4 ${loading ? "opacity-50" : ""}`}>
              <BusFactorCard items={data.bus_factor} />
            </div>
          )
        }
          {data && (
          <div className="mt-4">
            <PrRiskCard key={data.repo} repo={data.repo} months={data.window_months} />
          </div>
        )}
      </main>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-2xl font-semibold tracking-tight tabular-nums">{value}</div>
      <div className="text-xs text-zinc-400">{label}</div>
    </div>
  );
}

