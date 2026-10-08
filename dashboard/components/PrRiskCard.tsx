"use client";

import { use, useState } from "react";
import { checkPr, type RiskResult } from "@/lib/api";
import { Card } from "./Card";

    const LEVEL_STYLES = {
    low: { pill: "bg-emerald-500/10 text-emerald-300", bar: "bg-emerald-400", label: "Low risk" },
    medium: { pill: "bg-amber-500/10 text-amber-300", bar: "bg-amber-400", label: "Medium risk" },
    high: { pill: "bg-red-500/10 text-red-300", bar: "bg-red-400", label: "High risk" },
    } as const;

export function PrRiskCard({repo , months} : {repo : string , months : number}){
    const [text, setText] = useState("");
    const [result , setResult] = useState<RiskResult | null>(null);
    const [loading , setLoading] = useState(false);
    const [error , setError] = useState<string | null>(null);


    async function onCheck(){
        const files = text
        .split(/[\n,]+/)
        .map((f) => f.trim())
        .filter(Boolean);
        if(files.length === 0){
            setError("Enter at least one file path, one per line.")
            return;
        }
        const [owner, name] = repo.split("/");
        setLoading(true);
        setError(null);
        try{
            setResult(await checkPr(owner , name, files, months));
        }catch(err){
            setError(err instanceof Error ? err.message : "Something went wrong.");
        }finally{
            setLoading(false);
        }
    }
    const style = result ? LEVEL_STYLES[result.level] : null;
        return (
    <Card
        title="PR risk check"
        hint="List the files a pull request changes. Get a score and the reasons behind it."
    >
        <div className="grid gap-7 md:grid-cols-2">
            <div>
            <label htmlFor="pr-files" className="sr-only">
            Changed files
            </label>
            <textarea
            id="pr-files"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={"lib/response.js\ntest/res.send.js"}
            spellCheck={false}
            className="h-32 w-full resize-none rounded-xl border border-zinc-800 bg-zinc-950 p-3 font-mono text-[13px] leading-relaxed outline-none placeholder:text-zinc-600 focus:border-zinc-600"
            />
            <button
            type="button"
            onClick={onCheck}
            disabled={loading}
            className="mt-3 h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-4 text-[13px] font-medium disabled:opacity-60"
            >
            {loading ? "Checking..." : "Check this PR"}
            </button>
            {error && (
                <p role="alert" className="mt-3 text-sm text-red-300">
                {error}
                </p>
            )}
        </div>

            <div>
            {result && style ? (
                <>
                <div className="flex items-baseline gap-3">
                    <span className="text-5xl font-semibold leading-none tracking-tight tabular-nums">
                    {result.score}
                    </span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style.pill}`}>
                    {style.label}
                    </span>
                </div>
                <div className="mt-3.5 h-1 overflow-hidden rounded bg-zinc-900">
                    <div className={`h-full rounded ${style.bar}`} style={{ width: `${result.score}%` }} />
                </div>
                <ul className="mt-4 space-y-2">
                    {result.reasons.map((reason) => (
                    <li key={reason} className="flex gap-3 text-[13px] leading-relaxed text-zinc-300">
                        <span className="mt-2 size-1.5 shrink-0 rounded-full bg-amber-400" />
                        <span>{reason}</span>
                    </li>
                    ))}
                </ul>
                </>
            ) : (
                <p className="text-sm text-zinc-500">The score and reasons will appear here.</p>
            )}
            </div>
        </div>
        </Card>
    );
    }
