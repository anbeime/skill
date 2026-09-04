#!/usr/bin/env python3
"""Classify how much semantic part evidence a GLB exposes.

This module is deliberately conservative.  It does not pretend that a mesh name,
normal discontinuity, or a guessed connected component is proof of ``head`` or
``scarf``.  It reports what the GLB metadata can support and routes ambiguous
assets to a browser ID-mask or multipart-GLB decision.
"""

from __future__ import annotations

from typing import Any


SEMANTIC_STRATEGIES = (
    "named-node",
    "primitive-material-boundary",
    "uv-texture-boundary",
    "connected-component-hypothesis",
    "curvature-normal-region-growing-hypothesis",
    "multiview-id-mask",
    "multipart-glb",
)


def assess_semantic_decomposition(
    *,
    node_count: int,
    mesh_count: int,
    primitive_count: int,
    material_count: int,
    nodes: list[dict[str, Any]],
    meshes: list[dict[str, Any]],
    materials: list[dict[str, Any]],
    texture_count: int = 0,
) -> dict[str, Any]:
    """Return a fail-closed semantic readiness assessment from GLB metadata.

    ``insufficient`` means insufficient for *reliable semantic reconstruction*,
    not that geometry algorithms are unable to propose partitions.  Hypotheses
    must be validated by a browser ID-mask or by a multipart export before they
    may drive a subject-specific procedural factory.
    """

    named_nodes = [
        str(item.get("name"))
        for item in nodes
        if isinstance(item, dict) and item.get("name") and not str(item["name"]).startswith("node-")
    ]
    named_meshes = [
        str(item.get("name"))
        for item in meshes
        if isinstance(item, dict) and item.get("name") and not str(item["name"]).startswith("mesh-")
    ]
    named_materials = [
        str(item.get("name"))
        for item in materials
        if isinstance(item, dict) and item.get("name") and not str(item["name"]).startswith("material-")
    ]

    if node_count == 1 and mesh_count == 1 and primitive_count == 1 and material_count <= 1:
        status = "insufficient"
        boundary = "multipart-glb-required"
        reason = (
            "The metadata exposes one merged drawable and no semantic material boundary. "
            "Connected-component or curvature analysis may produce hypotheses, but cannot "
            "prove which region is head, clothing, weapon, or tail."
        )
    elif len(named_nodes) >= 2 or len(named_meshes) >= 2:
        status = "rich"
        boundary = "named-node-or-mesh"
        reason = "Multiple named scene/mesh entities provide an explicit semantic starting point."
    else:
        status = "partial"
        boundary = "browser-id-mask-or-multipart-glb"
        reason = (
            "Multiple drawable/material records exist, but metadata names do not establish a "
            "complete semantic part map."
        )

    strategy_status: dict[str, str] = {
        "named-node": "available" if len(named_nodes) >= 2 else "not-proven",
        "primitive-material-boundary": "available" if primitive_count > 1 or material_count > 1 else "not-proven",
        "uv-texture-boundary": "available" if texture_count > 0 else "not-proven",
        "connected-component-hypothesis": "candidate-only",
        "curvature-normal-region-growing-hypothesis": "candidate-only",
        "multiview-id-mask": "required-for-runtime-region-evidence",
        "multipart-glb": "required" if status == "insufficient" else "recommended",
    }
    return {
        "schemaVersion": 1,
        "status": status,
        "reliableSemanticBoundary": boundary,
        "reason": reason,
        "metadataEvidence": {
            "nodeCount": node_count,
            "meshCount": mesh_count,
            "primitiveCount": primitive_count,
            "materialCount": material_count,
            "textureCount": texture_count,
            "namedNodes": named_nodes,
            "namedMeshes": named_meshes,
            "namedMaterials": named_materials,
        },
        "strategies": [
            {"id": strategy, "status": strategy_status[strategy]}
            for strategy in SEMANTIC_STRATEGIES
        ],
        "claimsAllowed": [
            "scene and drawable inventory",
            "material/primitive boundaries explicitly present in the GLB",
            "browser-rendered ID-mask evidence when captured",
        ],
        "claimsForbiddenUntilEvidence": [
            "exact semantic labels inferred from a merged mesh",
            "per-region material equality without region crops or ID masks",
            "multipart topology reconstructed from metadata alone",
        ],
    }
