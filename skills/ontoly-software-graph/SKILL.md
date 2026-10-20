---
name: ontoly-software-graph
description: Use Ontoly's deterministic Software Graph and MCP capabilities for architecture review, request tracing, dependency analysis, configuration lookup, and impact analysis before falling back to source-file search.
---

# Ontoly Software Graph

Use this skill when a coding agent needs evidence-backed software understanding from an Ontoly graph before searching repository files directly.

## When to Use

- Explaining a repository architecture
- Tracing a request, route, controller, service, or dependency path
- Finding owners of services, modules, routes, configuration, or environment variables
- Reviewing dependency impact before a refactor
- Auditing dead code, cycles, unresolved imports, graph quality, or semantic coverage
- Preparing documentation, onboarding notes, or architecture review from graph evidence

## Required Workflow

1. Check whether an Ontoly graph already exists by looking for `.ontoly/`, `SoftwareGraph.json`, `diagnostics.json`, validation reports, or an Ontoly MCP configuration.
2. If no graph exists and the user permits local analysis, run:

   ```bash
   ontoly build .
   ```

3. Inspect graph health before answering: diagnostics, graph hash, semantic coverage, trust or quality score, framework detection, and generation timestamp.
4. Prefer Ontoly CLI or MCP capabilities for graph questions instead of scanning source files first.
5. Use repository search only when Ontoly cannot answer, the graph is stale, the graph is incomplete, or the user explicitly asks for source-level verification.
6. Always cite graph evidence in the answer: node IDs, edge types, file paths, source locations, diagnostics, or framework analyzer output.
7. State confidence from graph evidence. Do not guess confidence.

## Useful Ontoly Capabilities

- `ExplainArchitecture` for repository and package topology
- `FindDependencies` for dependency trees and direct consumers
- `ImpactAnalysis` for refactor blast radius
- `TraceExecution` for request, route, and call-flow tracing
- `FindConfigurationUsage` for configuration and environment variable usage
- `FrameworkReport` for detected framework concepts such as modules, controllers, providers, and routes
- `FindDeadCode` for unreachable or unused graph regions

## Answer Shape

When answering, include:

- the direct answer
- graph evidence
- confidence
- diagnostics or caveats
- fallback source inspection only if needed

Example:

```text
AuthController handles authentication.

Evidence:
- node: class:src/auth/auth.controller.ts:AuthController
- route edges: HANDLES POST /login, POST /logout
- dependency edges: USES AuthService, JwtService

Confidence: high, because the graph has controller, route, and dependency edges with source locations.
```

## Fallback Rules

- If the graph is missing, build it first when allowed.
- If graph validation fails, report the failure and use source search only to verify the affected area.
- If multiple nodes match the same name, ask for disambiguation or show the candidates with package/module context.
- If the requested concept is not in the graph, return `NOT_FOUND` with the closest graph evidence instead of inventing an answer.

