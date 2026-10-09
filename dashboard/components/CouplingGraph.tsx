"use client";
import { useMemo, useState } from "react";
import type { Graph } from "@/lib/api";
import { layoutGraph } from "@/lib/GraphLayout";
import { Card } from "./Card";

const W = 760;
const H = 380;
const LABELED = 8;

function baseName(path: string): string {
  const name = path.split("/").pop() ?? path;
  return name.length > 24 ? `${name.slice(0, 23)}…` : name;
}

export function CouplingGraph({graph} : {graph : Graph}){
    const placed = useMemo(()=>layoutGraph(graph , W , H) , [graph])
    const [hover , setHover] = useState<string | null>(null)
    const byId = useMemo(() => new Map(placed.nodes.map((n) => [n.id, n])), [placed]);
    const neighbours = useMemo(()=>{
        const map = new Map<string , Set<string>>();
        for(const e of placed.edges){
            if (!map.has(e.source)) map.set(e.source, new Set());
            if (!map.has(e.target)) map.set(e.target, new Set());
            map.get(e.source)!.add(e.target);
            map.get(e.target)!.add(e.source);
        }
        return map;
    },[placed]);
    const biggest = useMemo(
    () => new Set([...placed.nodes].sort((a, b) => b.changes - a.changes).slice(0, LABELED).map((n) => n.id)),
    [placed],
    );

    const hovered = hover ? byId.get(hover) : undefined;
    const related = hover ? neighbours.get(hover) : undefined;

    return (
        <Card
        title="Coupling map"
        hint="Each line joins files that change together. Thicker means stronger. Hover a file."
        >
        {placed.edges.length === 0 ? (
            <p className="py-6 text-sm text-zinc-500">
            Not enough history in this window to draw a coupling map.
            </p>
        ) : (
            <>
            <svg
                viewBox={`0 0 ${W} ${H}`}
                role="img"
                aria-label="Network graph of files that change together"
                className="h-auto w-full"
            >
                <g strokeLinecap="round">
                {placed.edges.map((e) => {
                    const a = byId.get(e.source);
                    const b = byId.get(e.target);
                    if (!a || !b) return null;
                    const active = hover !== null && (e.source === hover || e.target === hover);
                    const dimmed = hover !== null && !active;
                    return (
                    <line
                        key={`${e.source}|${e.target}`}
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        stroke="#7C86FF"
                        strokeWidth={0.8 + e.strength * 2.4}
                        opacity={active ? 0.95 : dimmed ? 0.08 : 0.25 + 0.5 * e.strength}
                    />
                    );
                })}
                </g>
                <g>
                {placed.nodes.map((n) => {
                    const dimmed = hover !== null && n.id !== hover && !related?.has(n.id);
                    return (
                    <circle
                        key={n.id}
                        cx={n.x}
                        cy={n.y}
                        r={n.r}
                        fill={placed.colors[n.area]}
                        stroke="#0F0F12"
                        strokeWidth={2.5}
                        opacity={dimmed ? 0.25 : 1}
                        tabIndex={0}
                        onMouseEnter={() => setHover(n.id)}
                        onMouseLeave={() => setHover(null)}
                        onFocus={() => setHover(n.id)}
                        onBlur={() => setHover(null)}
                    >
                        <title>{n.id}</title>
                    </circle>
                    );
                })}
                </g>
                <g
                textAnchor="middle"
                fontSize={11}
                fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
                pointerEvents="none"
                >
                {placed.nodes.map((n) => {
                    const show = hover ? n.id === hover || related?.has(n.id) : biggest.has(n.id);
                    if (!show) return null;
                    const label = baseName(n.id);
                    return (
                    <g key={n.id}>
                        <text x={n.x} y={n.y + n.r + 13} fill="none" stroke="#0F0F12" strokeWidth={4} strokeLinejoin="round">
                        {label}
                        </text>
                        <text x={n.x} y={n.y + n.r + 13} fill="#C9C9D1">
                        {label}
                        </text>
                    </g>
                    );
                })}
                </g>
            </svg>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-zinc-500">
                {placed.legend.map((area) => (
                <span key={area} className="inline-flex items-center gap-1.5">
                    <span
                    className="inline-block size-2 rounded-full"
                    style={{ background: placed.colors[area] }}
                    />
                    {area}
                </span>
                ))}
            </div>
            <p className="mt-3 min-h-5 truncate font-mono text-xs text-zinc-400">
                {hovered ? `${hovered.id} · ${hovered.changes} changes` : "Dot size is how often a file changes."}
            </p>
            </>
        )}
        </Card>
    );

    }
