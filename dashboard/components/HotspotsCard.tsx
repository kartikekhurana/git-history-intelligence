import type {Hotspot} from '@/lib/api'
import { Card } from "./Card";
export function HotspotsCard({ items }: { items: Hotspot[] }) {
const max = Math.max(...items.map((h) => h.changes), 1);

return (
    <Card title="Hotspots" hint='Files that change the most. They tend to be fragile.'>
        {
            items.length === 0 ? (
                <p className="py-6 text-sm text-zinc-500">No changes in this time window.</p>
            ) : (
                <ul>
                    {
                        items.map((h)=>(
                            <li key={h.path} className="border-t border-zinc-900 py-2.5 first:border-t-0">
                                <div className='flex justify-between gap-3 text-[13px]'>
                                    <span className="truncate font-mono" title={h.path}>
                                        {h.path}
                                    </span>
                                    <span className="shrink-0 tabular-nums text-zinc-400">{h.changes}</span>
                                </div>
                                <div className="mt-2 h-1 overflow-hidden rounded bg-zinc-900">
                                    <div
                                    className="h-full rounded bg-indigo-400"
                                    style={{ width: `${(h.changes / max) * 100}%` }}
                                />
                                </div>
                            </li>
                        ))
                    }
                </ul>
            )
        }
    </Card>
)
}