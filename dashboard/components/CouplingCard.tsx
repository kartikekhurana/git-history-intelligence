import type { Coupling } from "@/lib/api";
import { Card } from "./Card";

export function CouplingCard({ items }: { items: Coupling[] }) {
    return (
    <Card title="Hidden coupling" hint="Files that change together with no code linking them.">
        {items.length === 0 ? (
        <p className="py-6 text-sm text-zinc-500">
            No pair of files changed together more than once, so there is no coupling to report yet.
        </p>
        ) : (
        <ul>
            {items.map((c) => (
                <li key={`${c.a}|${c.b}`} className="border-t border-zinc-900 py-2.5 first:border-t-0">
                <div className="flex justify-between gap-3 text-[13px]">
                <span className="min-w-0 font-mono leading-relaxed">
                    <span className="break-all">{c.a}</span>
                    <span className="px-1.5 text-zinc-600">↔</span>
                    <span className="break-all">{c.b}</span>
                </span>
                <span className="shrink-0 tabular-nums text-zinc-400">
                  {Math.round(c.strength * 100)}%
                </span>
                </div>
                <div className="mt-2 h-1 overflow-hidden rounded bg-zinc-900">
                <div
                    className="h-full rounded bg-indigo-400"
                  style={{ width: `${c.strength * 100}%` }}
                />
                </div>
                <p className="mt-1.5 text-xs text-zinc-500">changed together {c.together} times</p>
            </li>
            ))}
        </ul>
        )}
    </Card>
    );
}