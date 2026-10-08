import { useState } from "react";
import type { BusFactor } from "@/lib/api";
import { Card } from "./Card";


const YEAR_MS = 365.25 * 24 * 60 * 60 * 1000; // milliseconds in a year

function YearsAgo(iso : string, now : number) : number {
   return Math.max(0, (now - new Date(iso).getTime()) / YEAR_MS); 
}

export function BusFactorCard({items}: {items : BusFactor[]}){
    const [now] = useState(()=>Date.now());
   return (
        <Card title="Bus factor" hint="Who wrote each area, and whether they are still around.">
        {items.length === 0 ? (
            <p className="py-6 text-sm text-zinc-500">Not enough history to see who owns what.</p>
        ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-[13px]">
                <thead>
                <tr className="border-b border-zinc-800 text-left text-xs font-medium text-zinc-500">
                    <th className="pb-2.5 pr-3 font-medium">Area</th>
                    <th className="pb-2.5 pr-3 font-medium">Top author</th>
                    <th className="pb-2.5 pr-3 font-medium">Share of commits</th>
                    <th className="pb-2.5 pr-3 font-medium">Commits</th>
                    <th className="pb-2.5 font-medium">Last active</th>
                </tr>
                </thead>
                <tbody>
                {items.map((b) => {
                    const years = YearsAgo(b.last_active, now);
                    const stale = years >= 2;
                    return (
                    <tr key={b.area} className="border-b border-zinc-900 last:border-b-0">
                        <td className="py-3 pr-3 font-mono">{b.area}</td>
                        <td className="py-3 pr-3">{b.top_author}</td>
                        <td className="py-3 pr-3">
                        <span className="mr-2.5 inline-block h-1 w-24 overflow-hidden rounded bg-zinc-900 align-middle">
                            <span
                            className="block h-full rounded bg-amber-400"
                            style={{ width: `${b.share * 100}%` }}
                            />
                        </span>
                        <span className="tabular-nums">{Math.round(b.share * 100)}%</span>
                        </td>
                        <td className="py-3 pr-3 tabular-nums">{b.commits.toLocaleString()}</td>
                        <td className="py-3">
                        <span
                            className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            stale ? "bg-red-500/10 text-red-300" : "bg-emerald-500/10 text-emerald-300"
                            }`}
                        >
                            {years < 1 ? "this year" : `${years.toFixed(1)} yrs ago`}
                        </span>
                        </td>
                    </tr>
                    );
                })}
                </tbody>
            </table>
            </div>
        )}
        </Card>
  );
}