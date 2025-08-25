import { useEffect, useState } from "react";

export default function Viewer() {
  const [sceneUrl, setSceneUrl] = useState(null);
  const [jobId, setJobId] = useState("");
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("job_id");
    if (!id) return;
    setJobId(id);
    // Use local proxy endpoints to avoid S3 CORS
    const ts = Date.now();
    fetch(`/api/scene?job_id=${id}&t=${ts}`)
      .then(async (r) => {
        if (!r.ok) throw new Error("scene fetch failed");
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        setSceneUrl(url);
      })
      .catch(() => {});
    fetch(`/api/manifest?job_id=${id}&t=${ts}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((mj) => {
        if (mj && typeof mj.prompt === "string") setPrompt(mj.prompt);
      })
      .catch(() => {});
  }, []);

  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <SceneCanvas url={sceneUrl} />
      <div
        style={{
          position: "absolute",
          top: 12,
          left: 12,
          background: "rgba(0,0,0,0.55)",
          color: "#fff",
          padding: "8px 12px",
          borderRadius: 8,
          maxWidth: "min(90vw, 720px)",
          fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
          fontSize: 14,
          lineHeight: 1.35,
          pointerEvents: "none",
          backdropFilter: "blur(4px)",
        }}
      >
        <div style={{ opacity: 0.9 }}>job_id: <code>{jobId || ""}</code></div>
        {prompt ? (
          <div style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>prompt: {prompt}</div>
        ) : null}
      </div>
    </div>
  );
}

function SceneCanvas({ url }) {
  // Minimal canvas without R3F to keep deps light for now
  return (
    <iframe
      title="viewer"
      srcDoc={`<!doctype html><html><head><meta charset="utf-8"/><style>html,body{margin:0;height:100%;overflow:hidden}</style><script type="importmap">{ "imports": { "three": "https://unpkg.com/three@0.161.0/build/three.module.js" } }</script></head><body><div id="c" style="width:100%;height:100%"></div><script type="module">import * as THREE from 'three'; import { GLTFLoader } from 'https://unpkg.com/three@0.161.0/examples/jsm/loaders/GLTFLoader.js'; const renderer=new THREE.WebGLRenderer({antialias:true}); const el=document.getElementById('c'); el.appendChild(renderer.domElement); const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(60,1,0.1,100); camera.position.set(2,2,2); const amb=new THREE.AmbientLight(0xffffff,0.7); scene.add(amb); const dir=new THREE.DirectionalLight(0xffffff,0.8); dir.position.set(5,5,5); scene.add(dir); const loader=new GLTFLoader(); const url='${url||''}'; if(url){ loader.load(url,(g)=>{ scene.add(g.scene); animate(); }); } function resize(){ const w=el.clientWidth,h=el.clientHeight; renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); } function animate(){ resize(); renderer.render(scene,camera); requestAnimationFrame(animate); } </script></body></html>`}
      style={{ border: 0, width: "100%", height: "100%" }}
    />
  );
}


