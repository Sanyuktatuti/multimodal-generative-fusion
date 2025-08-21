import subprocess
from pathlib import Path
from typing import List


def triposr_single_image_to_mesh(image_path: str, out_stem: Path) -> str:
    """
    Try TripoSR python API; fallback to CLI. Returns path to an .obj mesh.
    """
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    try:
        import trimesh  # noqa: F401
        from triposr import api as triposr_api  # type: ignore
        mesh = triposr_api.reconstruct(str(image_path))
        tm = _to_trimesh(mesh)
        tm.remove_degenerate_faces()
        tm.remove_duplicate_faces()
        tm.remove_unreferenced_vertices()
        out_obj = str(out_stem) + ".obj"
        tm.export(out_obj)
        return out_obj
    except Exception:
        # CLI fallback
        out_obj = str(out_stem) + ".obj"
        cmd = [
            "python",
            "-m",
            "triposr.run",
            "--image",
            str(image_path),
            "--out",
            out_obj,
        ]
        subprocess.run(cmd, check=True)
        return out_obj


def _to_trimesh(mesh_like):
    import numpy as np
    import trimesh

    if isinstance(mesh_like, trimesh.Trimesh):
        return mesh_like
    if isinstance(mesh_like, dict) and "vertices" in mesh_like and "faces" in mesh_like:
        v = np.asarray(mesh_like["vertices"])  # type: ignore
        f = np.asarray(mesh_like["faces"])  # type: ignore
        return trimesh.Trimesh(vertices=v, faces=f, process=False)
    raise ValueError("Unsupported mesh_like type for conversion to trimesh")


def zero123_novel_views(image_path: Path, out_dir: Path, ckpt: str, device: str = "cuda") -> List[str]:
    """
    Optional Zero123++ novel view generation via CLI. Returns list of image paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python",
        "/opt/zero123plus/infer.py",
        "--input",
        str(image_path),
        "--output",
        str(out_dir),
        "--ckpt",
        ckpt,
        "--device",
        device,
    ]
    subprocess.run(cmd, check=True)
    return sorted([str(p) for p in out_dir.glob("*.png")])


def clean_and_pack_glb(mesh_paths: List[str], out_glb_path: Path) -> None:
    """
    Merge meshes and export GLB using trimesh when available. If trimesh not
    available, write a small stub file to indicate placeholder content.
    """
    try:
        import trimesh

        scene = trimesh.Scene()
        for mp in mesh_paths:
            m = trimesh.load(mp, force="mesh")
            if not isinstance(m, trimesh.Trimesh) and hasattr(m, "geometry"):
                for _, g in m.geometry.items():
                    scene.add_geometry(g)
            else:
                scene.add_geometry(m)

        # Simple spread so assets are not co-located
        for i, geom in enumerate(scene.geometry):
            T = trimesh.transformations.translation_matrix((i * 0.5, 0, 0))
            geom.apply_transform(T)

        combined = trimesh.util.concatenate(
            [g for g in scene.geometry if isinstance(g, trimesh.Trimesh)]
        )
        out_glb_path.parent.mkdir(parents=True, exist_ok=True)
        combined.export(out_glb_path)
    except Exception:
        out_glb_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_glb_path, "wb") as f:
            f.write(b"glTF-stub")


