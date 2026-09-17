"""Build a claspless, two-material Myo-style bracelet band.

The rigid shells and TPU U-flexures are exported as aligned material volumes.
Load both STLs as parts of one object in the slicer.  The interface deliberately
uses a small shared volume; material ownership at that boundary is left to the
slicer, as requested.

This is a wrist/flexure prototype, not a released electronics enclosure.  It
keeps the revision-0.6 pod envelopes and access cutouts, but lid retention,
component support, cable strain relief, and body-loaded RF performance remain
open.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct
from xml.sax.saxutils import escape
import zipfile

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Pos,
    Rot,
    export_step,
    export_stl,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "mechanical" / "myo-band-v0.7"

POD_DEPTH = 9.5  # lid adds the final 1.0 mm to the existing 10.5 mm envelope
WALL = 1.2
SATELLITE_WIDTH = 20.0
SATELLITE_HEIGHT = 38.0
MAIN_WIDTH = 24.0
MAIN_HEIGHT = 64.0
COMMON_CENTER_Z = MAIN_HEIGHT / 2.0
SATELLITE_Z0 = COMMON_CENTER_Z - SATELLITE_HEIGHT / 2.0

FLEXURE_RADIAL_WIDTH = 1.8
FLEXURE_AXIAL_HEIGHT = 5.0
FLEXURE_INNER_CLEARANCE = 1.6
FLEXURE_ANCHOR_RADIAL = POD_DEPTH - 1.3
FLEXURE_ANCHOR_OVERLAP = 0.7
FLEXURE_Z = (
    SATELLITE_Z0 + 2.5,
    SATELLITE_Z0 + SATELLITE_HEIGHT - 2.5 - FLEXURE_AXIAL_HEIGHT,
)


@dataclass(frozen=True)
class Pod:
    name: str
    width: float
    height: float
    z0: float
    theta: float


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary_stl_xml(path: Path) -> tuple[str, str]:
    """Return 3MF vertex and triangle XML from one binary STL."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"Short STL: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise ValueError(f"Expected a binary STL with {count} facets: {path}")
    vertices: list[tuple[float, float, float]] = []
    vertex_ids: dict[tuple[float, float, float], int] = {}
    triangles: list[tuple[int, int, int]] = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        ids = []
        for offset in (3, 6, 9):
            vertex = tuple(float(v) for v in values[offset : offset + 3])
            if vertex not in vertex_ids:
                vertex_ids[vertex] = len(vertices)
                vertices.append(vertex)
            ids.append(vertex_ids[vertex])
        triangles.append(tuple(ids))
    vertex_xml = "".join(
        f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x, y, z in vertices
    )
    triangle_xml = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles
    )
    return vertex_xml, triangle_xml


def export_3mf(rigid_path: Path, soft_path: Path, out_path: Path):
    """Package the aligned material meshes as one two-component 3MF object."""
    rigid_vertices, rigid_triangles = binary_stl_xml(rigid_path)
    soft_vertices, soft_triangles = binary_stl_xml(soft_path)
    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
 xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
 xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
 requiredextensions="m">
 <metadata name="Title">{escape("Claspless Myo band 195 mm")}</metadata>
 <metadata name="Designer">Codex with user-directed Myo reference</metadata>
 <resources>
  <m:basematerials id="1">
   <m:base name="Rigid shell material" displaycolor="#536974FF"/>
   <m:base name="TPU flexure material" displaycolor="#1FB3AEFF"/>
  </m:basematerials>
  <object id="2" type="model" name="Rigid pod shells" pid="1" pindex="0">
   <mesh><vertices>{rigid_vertices}</vertices><triangles>{rigid_triangles}</triangles></mesh>
  </object>
  <object id="3" type="model" name="TPU U-flexures" pid="1" pindex="1">
   <mesh><vertices>{soft_vertices}</vertices><triangles>{soft_triangles}</triangles></mesh>
  </object>
  <object id="4" type="model" name="Claspless bracelet band">
   <components><component objectid="2"/><component objectid="3"/></components>
  </object>
 </resources>
 <build><item objectid="4"/></build>
</model>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>'''
    relationships = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>'''
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("3D/3dmodel.model", model)


def local_shell(width: float, height: float, main: bool = False):
    """Open-outward pod shell in local tangent/radial/axial coordinates."""
    shell = Box(
        width,
        POD_DEPTH,
        height,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    cavity = Pos(0, WALL, WALL) * Box(
        width - 2 * WALL,
        POD_DEPTH - WALL + 0.5,
        height - 2 * WALL,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    shell -= cavity

    # The five-wire harness uses the existing 14 x 2.4 mm side mouths.
    center_z = height / 2.0
    left_mouth = Pos(-width / 2.0 - 0.1, 3.3, center_z - 7.0) * Box(
        WALL + 0.2,
        2.4,
        14.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_mouth = Pos(width / 2.0 - WALL - 0.1, 3.3, center_z - 7.0) * Box(
        WALL + 0.2,
        2.4,
        14.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    shell -= left_mouth + right_mouth

    if main:
        # Preserve the fit-mockup USB-C and sole side-button openings.
        usb = Pos(-4.8, 2.6, height - WALL - 0.1) * Box(
            9.6,
            3.9,
            WALL + 0.2,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        button_center_z = 50.0
        button = Pos(width / 2.0 - WALL - 0.1, 2.8, button_center_z - 1.6) * Box(
            WALL + 0.2,
            3.0,
            3.2,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        shell -= usb + button
    return shell


def pod_layout(wrist_mm: float) -> tuple[float, float, list[Pod]]:
    """Place tangent pods around the user's circular reference circumference."""
    radius = wrist_mm / (2.0 * math.pi)
    widths = [MAIN_WIDTH] + [SATELLITE_WIDTH] * 7
    spans = [2.0 * math.asin(width / (2.0 * radius)) for width in widths]
    gap_angle = (2.0 * math.pi - sum(spans)) / len(widths)
    if gap_angle <= 0:
        raise ValueError("Wrist circumference is too small for the retained pod widths.")

    centers = [0.0]
    for index in range(1, len(widths)):
        centers.append(
            centers[-1] + spans[index - 1] / 2.0 + gap_angle + spans[index] / 2.0
        )
    pods = [
        Pod("main", MAIN_WIDTH, MAIN_HEIGHT, 0.0, centers[0]),
        *[
            Pod(f"satellite-{index}", SATELLITE_WIDTH, SATELLITE_HEIGHT, SATELLITE_Z0, centers[index])
            for index in range(1, 8)
        ],
    ]
    return radius, gap_angle, pods


def place_local(shape, theta: float, radius: float, z0: float):
    return Rot(0, 0, math.degrees(theta)) * Pos(0, radius, z0) * shape


def local_point(theta: float, x: float, radial: float, radius: float) -> tuple[float, float]:
    y = radius + radial
    c, s = math.cos(theta), math.sin(theta)
    return c * x - s * y, s * x + c * y


def ribbon_segment(p0: tuple[float, float], p1: tuple[float, float], z0: float):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    bar = Box(
        length,
        FLEXURE_RADIAL_WIDTH,
        FLEXURE_AXIAL_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return Pos((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, z0) * Rot(0, 0, angle) * bar


def u_flexure(p0: tuple[float, float], p1: tuple[float, float], theta_mid: float, radius: float, z0: float):
    """A rounded, inward-bowed U joining two neighboring pod sidewalls."""
    inner_radius = radius + FLEXURE_INNER_CLEARANCE
    q1 = (
        -inner_radius * math.sin(theta_mid - 0.012),
        inner_radius * math.cos(theta_mid - 0.012),
    )
    q2 = (
        -inner_radius * math.sin(theta_mid + 0.012),
        inner_radius * math.cos(theta_mid + 0.012),
    )
    path = [p0, q1, q2, p1]
    flexure = None
    for a, b in zip(path, path[1:]):
        segment = ribbon_segment(a, b, z0)
        flexure = segment if flexure is None else flexure + segment
    for x, y in path:
        flexure += Pos(x, y, z0) * Cylinder(
            FLEXURE_RADIAL_WIDTH / 2.0,
            FLEXURE_AXIAL_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return flexure


def svg_preview(radius: float, gap_angle: float, pods: list[Pod], path: Path, wrist_mm: float):
    scale = 6.2
    cx, cy = 430.0, 395.0

    def xy(point: tuple[float, float]) -> tuple[float, float]:
        return cx + scale * point[0], cy - scale * point[1]

    def polygon_points(pod: Pod) -> str:
        corners = [
            local_point(pod.theta, -pod.width / 2.0, 0.0, radius),
            local_point(pod.theta, pod.width / 2.0, 0.0, radius),
            local_point(pod.theta, pod.width / 2.0, POD_DEPTH, radius),
            local_point(pod.theta, -pod.width / 2.0, POD_DEPTH, radius),
        ]
        return " ".join(f"{x:.2f},{y:.2f}" for x, y in map(xy, corners))

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">',
        '<rect width="1400" height="820" fill="#f4f2ed"/>',
        '<g font-family="Arial, sans-serif">',
        '<text x="46" y="48" font-size="29" font-weight="700" fill="#1f3038">CLASPLESS MYO-STYLE BAND / REVISION 0.7</text>',
        f'<text x="46" y="78" font-size="17" fill="#53656d">{wrist_mm:.0f} mm circular fit reference · rigid shells + paired TPU U-flexures · one co-printed band</text>',
        f'<circle cx="{cx}" cy="{cy}" r="{radius * scale:.2f}" fill="none" stroke="#8c9ba1" stroke-width="2" stroke-dasharray="8 6"/>',
    ]

    for pod in pods:
        color = "#31444d" if pod.name == "main" else "#657984"
        lines.append(f'<polygon points="{polygon_points(pod)}" fill="{color}" stroke="#16262d" stroke-width="2"/>')

    flex_paths = []
    for i, pod in enumerate(pods):
        nxt = pods[(i + 1) % len(pods)]
        p0 = local_point(pod.theta, -pod.width / 2.0 + FLEXURE_ANCHOR_OVERLAP, FLEXURE_ANCHOR_RADIAL, radius)
        p1 = local_point(nxt.theta, nxt.width / 2.0 - FLEXURE_ANCHOR_OVERLAP, FLEXURE_ANCHOR_RADIAL, radius)
        theta_next = nxt.theta if i < len(pods) - 1 else nxt.theta + 2.0 * math.pi
        theta_mid = (pod.theta + theta_next) / 2.0
        inner_radius = radius + FLEXURE_INNER_CLEARANCE
        q1 = (-inner_radius * math.sin(theta_mid - 0.012), inner_radius * math.cos(theta_mid - 0.012))
        q2 = (-inner_radius * math.sin(theta_mid + 0.012), inner_radius * math.cos(theta_mid + 0.012))
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(xy, [p0, q1, q2, p1]))
        flex_paths.append(pts)
        lines.append(f'<polyline points="{pts}" fill="none" stroke="#2aa8a6" stroke-width="{FLEXURE_RADIAL_WIDTH * scale:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')

    lines += [
        '<circle cx="430" cy="395" r="5" fill="#8c9ba1"/>',
        '<text x="430" y="400" font-size="14" text-anchor="middle" fill="#f4f2ed">+</text>',
        '<text x="850" y="145" font-size="23" font-weight="700" fill="#1f3038">What changed</text>',
        '<text x="850" y="185" font-size="18" fill="#344b55">• Eight rigid pod shells remain at the current widths.</text>',
        '<text x="850" y="217" font-size="18" fill="#344b55">• Every gap gets two soft U-shaped flexures.</text>',
        '<text x="850" y="249" font-size="18" fill="#344b55">• The eighth gap is soft-only: no clasp and no wire.</text>',
        '<text x="850" y="281" font-size="18" fill="#344b55">• The other seven gaps retain the five-wire corridor.</text>',
        '<text x="850" y="335" font-size="23" font-weight="700" fill="#1f3038">Slicer object</text>',
        '<rect x="850" y="363" width="36" height="26" rx="4" fill="#657984"/>',
        '<text x="900" y="383" font-size="18" fill="#344b55">rigid-band-shells.stl</text>',
        '<rect x="850" y="411" width="36" height="26" rx="4" fill="#2aa8a6"/>',
        '<text x="900" y="431" font-size="18" fill="#344b55">tpu-u-flexures.stl</text>',
        '<text x="850" y="477" font-size="17" fill="#53656d">Load both at the same origin as parts of one object.</text>',
        '<text x="850" y="505" font-size="17" fill="#53656d">The shared interface is intentionally slicer-resolved.</text>',
        '<text x="850" y="559" font-size="23" font-weight="700" fill="#1f3038">Fit boundary</text>',
        f'<text x="850" y="597" font-size="18" fill="#344b55">Skin reference radius: {radius:.2f} mm</text>',
        f'<text x="850" y="629" font-size="18" fill="#344b55">Equal skin-arc gap: {radius * gap_angle:.2f} mm</text>',
        '<text x="850" y="661" font-size="18" fill="#344b55">No negative ease is applied in this first prototype.</text>',
        '<text x="46" y="786" font-size="16" fill="#68777d">CAD-checked concept only. Wrist shape, TPU stiffness, print support, wiring strain, lid closure, electronics fit and RF remain to be physically verified.</text>',
        '</g></svg>',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(wrist_mm: float):
    print_dir = OUT / "print"
    cad_dir = OUT / "cad"
    print_dir.mkdir(parents=True, exist_ok=True)
    cad_dir.mkdir(parents=True, exist_ok=True)

    radius, gap_angle, pods = pod_layout(wrist_mm)
    rigid_parts = []
    for pod in pods:
        rigid_parts.append(
            place_local(
                local_shell(pod.width, pod.height, main=pod.name == "main"),
                pod.theta,
                radius,
                pod.z0,
            )
        )

    flexure_parts = []
    flexure_names = []
    for i, pod in enumerate(pods):
        nxt = pods[(i + 1) % len(pods)]
        p0 = local_point(
            pod.theta,
            -pod.width / 2.0 + FLEXURE_ANCHOR_OVERLAP,
            FLEXURE_ANCHOR_RADIAL,
            radius,
        )
        p1 = local_point(
            nxt.theta,
            nxt.width / 2.0 - FLEXURE_ANCHOR_OVERLAP,
            FLEXURE_ANCHOR_RADIAL,
            radius,
        )
        theta_next = nxt.theta if i < len(pods) - 1 else nxt.theta + 2.0 * math.pi
        theta_mid = (pod.theta + theta_next) / 2.0
        for level, z0 in zip(("lower", "upper"), FLEXURE_Z):
            flexure_parts.append(u_flexure(p0, p1, theta_mid, radius, z0))
            flexure_names.append(f"gap-{i}-{level}")

    rigid_interferences = []
    for i, first in enumerate(rigid_parts):
        for j in range(i + 1, len(rigid_parts)):
            volume = float((first & rigid_parts[j]).volume)
            if volume > 1e-5:
                rigid_interferences.append({"pods": [pods[i].name, pods[j].name], "volume_mm3": volume})
    if rigid_interferences:
        raise RuntimeError(f"Rigid pod collision(s): {rigid_interferences}")

    flexure_contacts = []
    for name, flexure in zip(flexure_names, flexure_parts):
        contacts = []
        for pod, rigid_part in zip(pods, rigid_parts):
            volume = float((flexure & rigid_part).volume)
            if volume > 1e-4:
                contacts.append({"pod": pod.name, "shared_volume_mm3": volume})
        if len(contacts) != 2:
            raise RuntimeError(f"{name} contacts {len(contacts)} rigid pods, expected 2: {contacts}")
        flexure_contacts.append({"flexure": name, "contacts": contacts})

    rigid = Compound(children=rigid_parts, label="RIGID_POD_SHELLS")
    soft = Compound(children=flexure_parts, label="TPU_U_FLEXURES")
    assembly = Compound(children=[rigid, soft], label="MYO_BAND_195MM")

    for name, shape in (("rigid-band-shells", rigid), ("tpu-u-flexures", soft)):
        if not shape.is_valid:
            raise RuntimeError(f"{name} is not a valid CAD shape")
        export_stl(shape, print_dir / f"{name}.stl", tolerance=0.02, angular_tolerance=0.12)
    export_3mf(
        print_dir / "rigid-band-shells.stl",
        print_dir / "tpu-u-flexures.stl",
        print_dir / "bracelet-band-195mm.3mf",
    )
    export_step(assembly, cad_dir / "bracelet-band-195mm.step")
    svg_preview(radius, gap_angle, pods, OUT / "preview.svg", wrist_mm)

    files = [
        print_dir / "rigid-band-shells.stl",
        print_dir / "tpu-u-flexures.stl",
        print_dir / "bracelet-band-195mm.3mf",
        cad_dir / "bracelet-band-195mm.step",
        OUT / "preview.svg",
    ]
    report = {
        "status": "CAD_EXPORT_PASS",
        "revision": "0.7 claspless Myo-style flexure prototype",
        "units": "mm",
        "user_wrist_circumference": wrist_mm,
        "skin_reference_radius": radius,
        "negative_ease": 0.0,
        "equal_skin_arc_gap": radius * gap_angle,
        "rigid_pod_count": len(rigid_parts),
        "tpu_u_flexure_count": len(flexure_parts),
        "rigid_pair_interferences": rigid_interferences,
        "flexure_contact_check": flexure_contacts,
        "print_orientation": "upright ring; global Z is along the arm",
        "expected_support": "Support seven raised satellite lower faces and the lower TPU flexures; main pod begins at Z=0.",
        "files": {str(p.relative_to(OUT)): sha256(p) for p in files},
        "scope": "CAD validity and export only; mesh audit is written separately. No slice, print, wrist fit, electronics fit, strain, RF, or durability qualification.",
    }
    (OUT / "cad-checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wrist-mm", type=float, default=195.0)
    args = parser.parse_args()
    if not math.isfinite(args.wrist_mm) or args.wrist_mm <= 0:
        parser.error("--wrist-mm must be a positive finite circumference")
    build(args.wrist_mm)


if __name__ == "__main__":
    main()
