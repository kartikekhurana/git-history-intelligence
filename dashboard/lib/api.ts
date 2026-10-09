export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Hotspot = {path : string ; changes : number}
export type Coupling = {a : string ; b : string; together : number; strength : number}
export type BusFactor ={
    area : string;
    top_author : string;
    share : number;
    commits: number;
    authors: number;
    last_active: string;
}
export type Analysis = {
  graph: Graph;
  repo: string;
  commit_count: number;
  window_months: number;
  recent_commit_count: number;
  hotspots: Hotspot[];
  coupling: Coupling[];
  bus_factor: BusFactor[];
};

export type RiskResult = {
  repo : string;
  window_months : number;
  score : number;
  level : "low" | "medium" | "high";
  reasons : string[]
};
export type GraphNode = { id: string; area: string; changes: number };
export type GraphEdge = { source: string; target: string; together: number; strength: number };
export type Graph = { nodes: GraphNode[]; edges: GraphEdge[] };


export function parseRepo(input: string): { owner: string; name: string } | null {
  const cleaned = input
    .trim()
    .replace(/^https?:\/\/(www\.)?github\.com\//i, "")
    .replace(/^github\.com\//i, "");
  const [owner, rawName] = cleaned.split("/");
  const name = rawName?.replace(/\.git$/i, "");
  if (!owner || !name) return null;
  return { owner, name };
}

export async function analyzeRepo(owner : string , name : string, months : number) : Promise<Analysis>{
    const url = `${API}/analyze/${encodeURIComponent(owner)}/${encodeURIComponent(name)}?months=${months}`;
    const res = await fetch(url);
    if(!res.ok){
        const body = await res.json().catch(()=>null)
        throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`)
    }
    return res.json()
}

export async function checkPr(
  owner: string,
  name: string,
  files: string[],
  months: number,
): Promise<RiskResult>{
  const url = `${API}/risk/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`;
  const res = await fetch(url,{
    method : "POST",
    headers : {"Content-Type" : "application/json"},
    body : JSON.stringify({files , months})
  });
  if(!res.ok){
    const body = await res.json().catch(()=>null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`);

  }
  return res.json()
}