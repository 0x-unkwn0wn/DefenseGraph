import { CoveragePage } from "./CoveragePage";

import type { Capability, TechniqueCoverage, Tool } from "../types";

interface GapsPageProps {
  capabilities: Capability[];
  coverage: TechniqueCoverage[];
  tools: Tool[];
}

export function GapsPage({ capabilities, coverage, tools }: GapsPageProps) {
  return <CoveragePage capabilities={capabilities} coverage={coverage} tools={tools} viewMode="gaps" />;
}
