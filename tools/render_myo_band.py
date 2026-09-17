"""Render the exported rigid and TPU STLs without changing them."""

from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "mechanical" / "myo-band-v0.7"
OUT = MODEL / "cad-render.png"


def load(name):
    mesh = trimesh.load_mesh(MODEL / "print" / name, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"Expected one triangle mesh for {name}")
    return mesh


rigid = load("rigid-band-shells.stl")
soft = load("tpu-u-flexures.stl")
camera = np.array([1.15, -1.45, 0.82], dtype=float)
camera /= np.linalg.norm(camera)
right = np.cross(camera, np.array([0.0, 0.0, 1.0]))
right /= np.linalg.norm(right)
up = np.cross(right, camera)
up /= np.linalg.norm(up)


def projected(mesh):
    x = mesh.vertices @ right
    y = mesh.vertices @ up
    d = mesh.vertices @ camera
    return np.column_stack((x, y, d))


rp, sp = projected(rigid), projected(soft)
allp = np.vstack((rp[:, :2], sp[:, :2]))
lo, hi = allp.min(axis=0), allp.max(axis=0)
canvas = np.array([1500, 1050])
margin = 105
scale = min((canvas[0] - 2 * margin) / (hi[0] - lo[0]), (canvas[1] - 2 * margin) / (hi[1] - lo[1]))


def screen(points):
    q = (points[:, :2] - lo) * scale + margin
    q[:, 1] = canvas[1] - q[:, 1]
    return q


triangles = []
for mesh, proj, base in ((rigid, rp, np.array([83, 105, 116])), (soft, sp, np.array([31, 179, 174]))):
    for face, normal in zip(mesh.faces, mesh.face_normals):
        light = float(np.clip(0.56 + 0.44 * np.dot(normal, np.array([0.3, -0.4, 0.86])), 0.34, 1.0))
        facing = float(np.dot(normal, camera))
        if facing <= 0.015:
            continue
        color = tuple(int(v) for v in np.clip(base * light, 0, 255))
        p = proj[face]
        triangles.append((float(p[:, 2].mean()), screen(p), color))

image = Image.new("RGB", tuple(canvas), (245, 243, 237))
draw = ImageDraw.Draw(image)
for _, points, color in sorted(triangles, key=lambda item: item[0]):
    draw.polygon([tuple(p) for p in points], fill=color)

try:
    font_title = ImageFont.truetype("arialbd.ttf", 34)
    font_body = ImageFont.truetype("arial.ttf", 22)
except OSError:
    font_title = font_body = ImageFont.load_default()

draw.rounded_rectangle((30, 25, 650, 120), radius=16, fill=(245, 243, 237), outline=(196, 199, 195), width=2)
draw.text((52, 42), "CLASPLESS TWO-MATERIAL BAND", fill=(31, 48, 56), font=font_title)
draw.text((53, 83), "Actual exported STL geometry · rigid + TPU", fill=(75, 94, 103), font=font_body)
draw.rounded_rectangle((1045, 890, 1468, 1018), radius=16, fill=(245, 243, 237), outline=(196, 199, 195), width=2)
draw.rectangle((1073, 920, 1104, 945), fill=(83, 105, 116))
draw.text((1122, 919), "rigid shells", fill=(48, 65, 73), font=font_body)
draw.rectangle((1073, 965, 1104, 990), fill=(31, 179, 174))
draw.text((1122, 964), "paired TPU U-flexures", fill=(48, 65, 73), font=font_body)
image.save(OUT)
print(OUT)
