import { useEffect, useState } from "react";

export default function Viewer() {
  const [sceneUrl, setSceneUrl] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const jobId = params.get("job_id");
    if (!jobId) return;
    fetch(`/api/presign?job_id=${jobId}`)
      .then((r) => r.json())
      .then((d) => setSceneUrl(d.scene_url))
      .catch(() => {});
  }, []);

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <SceneCanvas url={sceneUrl} />
    </div>
  );
}

function SceneCanvas({ url }) {
  const [gltf, setGltf] = useState(null);
  useEffect(() => {
    if (!url) return;
    import("three").then(async (THREE) => {
      const { GLTFLoader } = await import(
        "three/examples/jsm/loaders/GLTFLoader"
      );
      const loader = new GLTFLoader();
      loader.load(url, (g) => setGltf(g));
    });
  }, [url]);

  // Minimal canvas without R3F to keep deps light for now
  return (
    <iframe
      title="viewer"
      srcDoc={`<!doctype html><html><head><style>html,body{margin:0;height:100%;overflow:hidden}</style></head><body><div id="c" style="width:100%;height:100%"></div><script type="module">import * as THREE from 'https://unpkg.com/three@0.161.0/build/three.module.js'; import { GLTFLoader } from 'https://unpkg.com/three@0.161.0/examples/jsm/loaders/GLTFLoader.js'; const renderer=new THREE.WebGLRenderer({antialias:true}); const el=document.getElementById('c'); el.appendChild(renderer.domElement); const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(60,1,0.1,100); camera.position.set(2,2,2); const amb=new THREE.AmbientLight(0xffffff,0.7); scene.add(amb); const dir=new THREE.DirectionalLight(0xffffff,0.8); dir.position.set(5,5,5); scene.add(dir); const loader=new GLTFLoader(); loader.load('${url||''}',(g)=>{ scene.add(g.scene); animate(); }); function resize(){ const w=el.clientWidth,h=el.clientHeight; renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); } function animate(){ resize(); renderer.render(scene,camera); requestAnimationFrame(animate); } </script></body></html>`}
      style={{ border: 0, width: "100%", height: "100%" }}
    />
  );
}


