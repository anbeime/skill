from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from math import isfinite
from pathlib import Path
from typing import Any, TypeAlias

sys.path.insert(0, str(Path(__file__).resolve().parent))
from self_intersection import analyze_mesh  # noqa: E402

SEAM_MIN_OVERLAP = 0.02
SEAM_MAX_OVERLAP = 0.05
SEAM_SOURCE = "grimoire/build/geometry_patterns.md"
DEFAULT_TRIANGLE_BUDGET = 50_000
NORMAL_DOT_THRESHOLD = 0.0
EdgeKey: TypeAlias = tuple[tuple[float, ...], tuple[float, ...]]


def _vertex_key(vertex: Any, precision: int = 6) -> tuple[float, ...]:
    if not isinstance(vertex, (list, tuple)) or len(vertex) < 3:
        raise ValueError("vertices must contain 3D positions")
    return tuple(round(float(value), precision) for value in vertex[:3])


def mesh_edge_counts(vertices: list[Any], indices: list[Any], *, precision: int = 6) -> dict[str, int]:
    keys = [_vertex_key(vertex, precision) for vertex in vertices]
    edges: Counter[EdgeKey] = Counter()
    triangles: list[Any] = indices if indices and isinstance(indices[0], (list, tuple)) else [indices[i:i + 3] for i in range(0, len(indices), 3)]
    if any(len(triangle) != 3 for triangle in triangles):
        raise ValueError("triangle indices must contain groups of three")
    for triangle in triangles:
        points = [keys[int(index)] for index in triangle]
        for left, right in ((points[0], points[1]), (points[1], points[2]), (points[2], points[0])):
            edge: EdgeKey = (left, right) if left <= right else (right, left)
            edges[edge] += 1
    return {"boundaryEdges": sum(count == 1 for count in edges.values()),
            "nonManifoldEdges": sum(count > 2 for count in edges.values()), "edgeCount": len(edges)}


def _bounds(mesh: dict[str, Any]) -> list[list[float]] | None:
    bounds = mesh.get("bounds") or mesh.get("boundingBox")
    if isinstance(bounds, dict):
        bounds = [bounds.get("min"), bounds.get("max")]
    if isinstance(bounds, (list, tuple)) and len(bounds) == 2 and all(isinstance(point, (list, tuple)) and len(point) >= 3 for point in bounds):
        points = [point for point in bounds if isinstance(point, (list, tuple))]
        if len(points) == 2:
            return [[float(value) for value in points[index][:3]] for index in range(2)]
    vertices = mesh.get("vertices")
    if not isinstance(vertices, list) or not vertices:
        return None
    points = [_vertex_key(point, 12) for point in vertices]
    return [[min(point[axis] for point in points) for axis in range(3)], [max(point[axis] for point in points) for axis in range(3)]]


def _axis_index(value: Any) -> int:
    if isinstance(value, int) and value in (0, 1, 2):
        return value
    return {"x": 0, "y": 1, "z": 2, "long": 0, "length": 0, "thickness": 2}.get(str(value or "").lower(), 0)


def _seam_overlap(first: dict[str, Any], second: dict[str, Any]) -> tuple[float, int] | None:
    raw_attachment = second.get("attachment")
    attachment: dict[str, Any] = raw_attachment if isinstance(raw_attachment, dict) else {}
    axis = attachment.get("seamAxis", second.get("seamAxis", first.get("seamAxis")))
    a, b = _bounds(first), _bounds(second)
    if axis is None or a is None or b is None:
        return None
    index = _axis_index(axis)
    return min(a[1][index], b[1][index]) - max(a[0][index], b[0][index]), index


def _blade_thickness(mesh: dict[str, Any]) -> dict[str, Any]:
    samples = mesh.get("thicknessSamples") or mesh.get("crossSections")
    grind_samples = mesh.get("grindSamples") or samples
    distal_samples = mesh.get("distalThicknessSamples") or samples
    values = []
    def numeric_values(source: Any) -> list[float]:
        result: list[float] = []
        if isinstance(source, list):
            for sample in source:
                value = sample.get("thickness") if isinstance(sample, dict) else sample
                if isinstance(value, (int, float)):
                    result.append(float(value))
        return result
    if isinstance(samples, list):
        for sample in samples:
            value = sample.get("thickness") if isinstance(sample, dict) else sample
            if isinstance(value, (int, float)):
                values.append(float(value))
    grind_values = numeric_values(grind_samples)
    distal_values = numeric_values(distal_samples)
    grind_variation = max(grind_values) - min(grind_values) if grind_values else 0.0
    distal_variation = max(distal_values) - min(distal_values) if distal_values else 0.0
    return {"grindVariation": grind_variation, "distalVariation": distal_variation,
            "constantGrind": grind_variation <= 1e-6, "missingDistalTaper": distal_variation <= 1e-6,
            "reported": bool(values)}


def _triangle_count(mesh: dict[str, Any]) -> int | None:
    if isinstance(mesh.get("triangleCount"), (int, float)) and not isinstance(mesh["triangleCount"], bool):
        return max(0, int(mesh["triangleCount"]))
    indices = mesh.get("indices")
    if isinstance(indices, list):
        return len(indices) if indices and isinstance(indices[0], (list, tuple)) else len(indices) // 3
    return None


def _has_reduced_lod_tiers(lod_plan: Any) -> bool:
    if not isinstance(lod_plan, list) or len(lod_plan) < 2:
        return False
    previous_distance: float | None = None
    previous_triangles: int | None = None
    for tier in lod_plan:
        if not isinstance(tier, dict):
            return False
        distance = tier.get("distance")
        triangles = tier.get("triangleCount")
        if (
            not isinstance(distance, (int, float))
            or isinstance(distance, bool)
            or not isfinite(distance)
            or not isinstance(triangles, int)
            or isinstance(triangles, bool)
            or triangles < 1
        ):
            return False
        if previous_distance is not None and distance <= previous_distance:
            return False
        if previous_triangles is not None and triangles >= previous_triangles:
            return False
        previous_distance = float(distance)
        previous_triangles = triangles
    return True


def _normal_consistency(mesh: dict[str, Any]) -> dict[str, Any] | None:
    normals = mesh.get("normals")
    if not isinstance(normals, list) or not isinstance(mesh.get("vertices"), list):
        return None
    if len(normals) != len(mesh["vertices"]):
        return {"checked": False, "consistent": False, "reason": "normal count does not match vertex count"}
    indices = mesh.get("indices")
    triangles = indices if isinstance(indices, list) and indices and isinstance(indices[0], (list, tuple)) else (
        [indices[i:i + 3] for i in range(0, len(indices), 3)] if isinstance(indices, list) else []
    )
    if not triangles:
        return None
    flips = 0
    checked = 0
    invalid_normals = 0
    for triangle in triangles:
        if len(triangle) != 3:
            continue
        try:
            a, b, c = (mesh["vertices"][int(index)] for index in triangle)
            edge_a = [float(b[i]) - float(a[i]) for i in range(3)]
            edge_b = [float(c[i]) - float(a[i]) for i in range(3)]
            face = [
                edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
                edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
                edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0],
            ]
            length = sum(value * value for value in face) ** 0.5
            if length <= 1e-12:
                continue
            face = [value / length for value in face]
            average = [
                sum(float(mesh["normals"][int(index)][axis]) for index in triangle) / 3
                for axis in range(3)
            ]
            normal_length = sum(value * value for value in average) ** 0.5
            if normal_length <= 1e-12:
                invalid_normals += 1
                continue
            dot = sum(face[axis] * average[axis] for axis in range(3)) / normal_length
            checked += 1
            flips += dot < NORMAL_DOT_THRESHOLD
        except (IndexError, TypeError, ValueError):
            return {"checked": False, "consistent": False, "reason": "invalid vertex/normal data"}
    return {
        "checked": checked > 0,
        "consistent": flips == 0 and invalid_normals == 0,
        "checkedTriangles": checked,
        "flippedTriangles": flips,
        "invalidNormalTriangles": invalid_normals,
    }


def measure_geometry_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    meshes = payload.get("meshes") or payload.get("components") or []
    if isinstance(meshes, dict):
        meshes = [dict(value, id=key) if isinstance(value, dict) else {"id": key} for key, value in meshes.items()]
    if not isinstance(meshes, list):
        raise ValueError("built geometry meshes/components must be an array or object")
    reports: list[dict[str, Any]] = []
    failures: list[str] = []
    issues: list[dict[str, Any]] = []
    performance = payload.get("performanceBudget") if isinstance(payload.get("performanceBudget"), dict) else {}
    triangle_budget = performance.get("triangleBudget", payload.get("triangleBudget", DEFAULT_TRIANGLE_BUDGET))
    if not isinstance(triangle_budget, (int, float)) or isinstance(triangle_budget, bool) or triangle_budget <= 0:
        triangle_budget = DEFAULT_TRIANGLE_BUDGET
    lod_plan = payload.get("lodPlan")
    lod_plan_valid = _has_reduced_lod_tiers(lod_plan)
    total_triangles = 0
    for index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict):
            continue
        item: dict[str, Any] = {"id": mesh.get("id") or mesh.get("name") or f"mesh-{index}", "realization": mesh.get("realization", "separate-geometry")}
        if isinstance(mesh.get("vertices"), list) and isinstance(mesh.get("indices"), list):
            item.update(mesh_edge_counts(mesh["vertices"], mesh["indices"]))
        else:
            item.update({"boundaryEdges": None, "nonManifoldEdges": None, "note": "mesh topology not supplied"})
        role = str(mesh.get("role") or "").lower()
        triangles = _triangle_count(mesh)
        item["triangleCount"] = triangles
        if triangles is not None:
            total_triangles += triangles
        normals = _normal_consistency(mesh)
        if normals is not None:
            item["normalConsistency"] = normals
            if normals.get("consistent") is False:
                message = f"{item['id']}: inconsistent face/vertex normals"
                failures.append(message)
                issues.append({"severity": "error", "code": "normal-consistency", "mesh": item["id"], "message": message})
        elif isinstance(mesh.get("vertices"), list) and isinstance(mesh.get("indices"), list):
            message = f"{item['id']}: normals are required for watertight geometry validation"
            failures.append(message)
            item["normalConsistency"] = {"checked": False, "consistent": False, "reason": "normals missing"}
            issues.append({"severity": "error", "code": "normal-missing", "mesh": item["id"], "message": message})
        if role == "blade" or "blade" in str(item["id"]).lower():
            item["thickness"] = _blade_thickness(mesh)
            if item["thickness"]["constantGrind"] or item["thickness"]["missingDistalTaper"]:
                failures.append(f"{item['id']}: blade has constant thickness or missing distal taper")
        if item.get("boundaryEdges", 0) not in (0, None):
            message = f"{item['id']}: openEdges={item['boundaryEdges']} ({item['realization']})"
            failures.append(message)
            issues.append({"severity": "error", "code": "watertight", "mesh": item["id"], "message": message})
        if item.get("nonManifoldEdges", 0):
            message = f"{item['id']}: nonManifoldEdges={item['nonManifoldEdges']}"
            failures.append(message)
            issues.append({"severity": "error", "code": "non-manifold", "mesh": item["id"], "message": message})
        # Both checks above are TOPOLOGICAL, and a surface pushed through its own far side changes no
        # connectivity at all -- it reports 0 open edges, 0 non-manifold edges, and an identical edge
        # count to the clean mesh. That is not a hypothetical: it is how a punched-through skull shipped.
        # The geometric check belongs right here, beside the two it complements, or it is a CLI nobody
        # remembers to run.
        if isinstance(mesh.get("vertices"), list) and isinstance(mesh.get("indices"), list):
            probe = analyze_mesh(mesh)
            item["selfIntersection"] = {
                key: probe[key]
                for key in (
                    "selfIntersecting", "insideVertexCount", "undecidedVertexCount",
                    "sampledVertexCount", "totalVertexCount", "samplingStride",
                )
                if key in probe
            }
            if probe.get("selfIntersecting"):
                message = (
                    f"{item['id']}: selfIntersecting, {probe.get('insideVertexCount')} of "
                    f"{probe.get('sampledVertexCount')} sampled vertices lie inside their own surface"
                )
                failures.append(message)
                issues.append({"severity": "error", "code": "self-intersection", "mesh": item["id"], "message": message})
        reports.append(item)
    seams: list[dict[str, Any]] = []
    for first, second in combinations([item for item in meshes if isinstance(item, dict)], 2):
        relation = second.get("adjacentTo") or first.get("adjacentTo")
        attached = isinstance(second.get("attachment"), dict) and second["attachment"].get("parentId") == first.get("id")
        if relation not in (None, first.get("id"), second.get("id")) and not attached:
            continue
        result = _seam_overlap(first, second)
        if result is None:
            continue
        overlap, axis = result
        seam = {"a": first.get("id"), "b": second.get("id"), "axis": axis, "overlap": round(overlap, 6), "minimum": SEAM_MIN_OVERLAP, "source": SEAM_SOURCE}
        seams.append(seam)
        if overlap < SEAM_MIN_OVERLAP:
            failures.append(f"seam {seam['a']}↔{seam['b']}: overlap={overlap:.3f} < {SEAM_MIN_OVERLAP:.2f}")
    if total_triangles > triangle_budget:
        message = f"triangle budget exceeded: {total_triangles} > {int(triangle_budget)}"
        failures.append(message)
        issues.append({"severity": "error", "code": "triangle-budget", "message": message, "triangles": total_triangles, "budget": int(triangle_budget)})
        if not lod_plan_valid:
            lod_message = "triangle budget exceeded without LOD tiers with increasing distance and decreasing triangleCount"
            failures.append(lod_message)
            code = "lod-required" if not isinstance(lod_plan, list) or not lod_plan else "lod-invalid"
            issues.append({"severity": "error", "code": code, "message": lod_message})
    return {"passed": not failures, "source": SEAM_SOURCE, "minimumSeamOverlap": SEAM_MIN_OVERLAP,
            "maximumDocumentedSeamOverlap": SEAM_MAX_OVERLAP, "triangleBudget": int(triangle_budget),
            "triangleCount": total_triangles, "lodPlanPresent": isinstance(lod_plan, list) and bool(lod_plan),
            "lodPlanValid": lod_plan_valid,
            "meshes": reports, "seams": seams, "failures": failures, "issues": issues}
