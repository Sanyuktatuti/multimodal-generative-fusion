export default async function handler(req, res) {
  try {
    const { job_id } = req.query;
    if (!job_id) {
      return res.status(400).json({ error: "job_id is required" });
    }
    const apiBase = process.env.API_BASE || "http://localhost:8000";
    const r = await fetch(`${apiBase}/v1/generations/${job_id}/presigned`);
    if (!r.ok) {
      const text = await r.text();
      return res.status(r.status).send(text);
    }
    const data = await r.json();
    return res.status(200).json(data);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}


