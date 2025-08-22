import os
import json
import tempfile
import uuid
from pathlib import Path

import boto3


def main() -> None:
    payload = os.getenv("PROMPT_JSON")
    if not payload:
        raise RuntimeError("PROMPT_JSON env is missing")

    cfg = json.loads(payload)
    prompt = cfg.get("prompt", "(none)")
    out_bucket_uri = cfg["out_bucket"]  # e.g., s3://bucket[/prefix]
    job_id = cfg.get("job_id", f"scn_{uuid.uuid4().hex}")

    tmp_dir = Path(tempfile.mkdtemp()) / job_id
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # --- REAL PIPELINE: Use actual environment generator ---
    try:
        from shared.providers.factory import get_provider
        
        # Create a minimal scene plan from the prompt
        scene_plan = {
            "environment": {
                "theme": prompt,
                "time_of_day": "night",  # Default to night for moody scenes
                "weather": "none"
            }
        }
        
        # Get the real environment generator
        provider = get_provider("env", "sdxl_triposr", "0.1.0", cfg={"job_root": str(tmp_dir)})
        result = provider.generate(scene_plan)
        
        # Extract the generated GLB path
        glb_path = Path(result["artifacts"]["scene_glb"])
        provenance = result["provenance"]
        
    except Exception as e:
        # Fallback to stub if real pipeline fails
        print(f"Real pipeline failed: {e}, falling back to stub")
        glb_path = tmp_dir / "scene.glb"
        glb_path.write_bytes(b"glTF-stub")
        provenance = {"pipeline": "stub-fallback", "version": "0.1.0", "error": str(e)}

    manifest = {
        "job_id": job_id,
        "prompt": prompt,
        "artifacts": {"scene_glb": str(glb_path)},
        "provenance": provenance,
    }
    (tmp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # Upload to S3
    bucket_part = out_bucket_uri.replace("s3://", "", 1)
    if "/" in bucket_part:
        bucket, prefix = bucket_part.split("/", 1)
        prefix = prefix.rstrip("/")
    else:
        bucket, prefix = bucket_part, ""
    prefix = f"{prefix}/{job_id}" if prefix else job_id

    s3 = boto3.client("s3")
    s3.upload_file(str(glb_path), bucket, f"{prefix}/scene.glb")
    s3.upload_file(str(tmp_dir / "manifest.json"), bucket, f"{prefix}/manifest.json")

    print(json.dumps({"ok": True, "s3": f"s3://{bucket}/{prefix}/"}))


if __name__ == "__main__":
    main()


