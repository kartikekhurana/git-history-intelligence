import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import type {Graph} from './api'

const PALETTE = ["#7C86FF", "#3DD6A0", "#F5B85F", "#F472B6", "#38BDF8", "#A78BFA", "#FB923C"];
const OTHER_COLOR = "#8B8B96";
type SimNode = SimulationNodeDatum & { id: string; area: string; changes: number; r: number };
type SimLink = SimulationLinkDatum<SimNode> & { strength: number };


export type PlacedNode = {
    id: string;
    area: string;
    changes: number;
    r: number;
    x: number;
    y: number;
};

export type PlacedEdge = { 
    source: string;
    target: string; 
    together: number; 
    strength: number 
};

export type Placed = {
    nodes: PlacedNode[];
    edges: PlacedEdge[];
    colors: Record<string, string>;
    legend: string[];
};

    export function layoutGraph(
    graph: Graph,
    width: number,
    height: number,
    padX = 76,
    padY = 40,
    ): Placed {
    const radius = (changes: number) => Math.min(16, 4 + Math.sqrt(changes) * 1.5);

    const nodes: SimNode[] = graph.nodes.map((n) => ({ ...n, r: radius(n.changes) }));
    const links: SimLink[] = graph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        strength: e.strength,
    }));

    const simulation = forceSimulation(nodes)
        .force(
        "link",
        forceLink<SimNode, SimLink>(links)
            .id((d) => d.id)
            .distance(70)
            .strength((l) => 0.25 + 0.6 * l.strength),
        )
        .force("charge", forceManyBody<SimNode>().strength(-220))
        .force("collide", forceCollide<SimNode>().radius((d) => d.r + 8))
        .force("x", forceX<SimNode>(0).strength(0.08))
        .force("y", forceY<SimNode>(0).strength(0.08))
        .stop();
    simulation.tick(300);

    const xs = nodes.flatMap((n) => [(n.x ?? 0) - n.r, (n.x ?? 0) + n.r]);
    const ys = nodes.flatMap((n) => [(n.y ?? 0) - n.r, (n.y ?? 0) + n.r]);
    const minX = Math.min(...xs, 0);
    const maxX = Math.max(...xs, 0);
    const minY = Math.min(...ys, 0);
    const maxY = Math.max(...ys, 0);
    const scaleX = Math.min((width - 2 * padX) / Math.max(maxX - minX, 1), 2);
    const scaleY = Math.min((height - 2 * padY) / Math.max(maxY - minY, 1), 2);
    const offsetX = (width - (maxX - minX) * scaleX) / 2 - minX * scaleX;
    const offsetY = (height - (maxY - minY) * scaleY) / 2 - minY * scaleY;

    const totals = new Map<string, number>();
    for (const n of graph.nodes) totals.set(n.area, (totals.get(n.area) ?? 0) + n.changes);
    const ranked = [...totals.entries()].sort((a, b) => b[1] - a[1]).map(([area]) => area);
    const colors: Record<string, string> = {};
    ranked.forEach((area, i) => {
        colors[area] = PALETTE[i] ?? OTHER_COLOR;
    });

    return {
    nodes: nodes.map((n) => ({
        id: n.id,
        area: n.area,
        changes: n.changes,
        r: n.r,
      x: (n.x ?? 0) * scaleX + offsetX,
      y: (n.y ?? 0) * scaleY + offsetY,
    })),
    edges: graph.edges,
    colors,
    legend: ranked.slice(0, PALETTE.length),
    };
}