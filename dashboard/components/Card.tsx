import type { ReactNode } from "react";

export function Card({
    title ,
    hint,
    children,
} :{
    title : string;
    hint : string;
    children : ReactNode;
}){
    return (
        <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950 p-5">
            <h2 className="text-[15px] font-semibold tracking-tight">{title}</h2>
            <p className="mb-3.5 mt-1 text-[13px] text-zinc-400">{hint}</p>
            {children}
        </section>

    )
}