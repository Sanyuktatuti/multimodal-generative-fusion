import { useEffect, useState } from 'react'

export default function Home() {
  const [prompt, setPrompt] = useState('misty cyberpunk alley')
  const [jobId, setJobId] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let timer
    if (jobId) {
      const poll = async () => {
        try {
          const res = await fetch(`http://localhost:8000/v1/generations/${jobId}/status`)
          const json = await res.json()
          setStatus(json.status)
        } catch (e) {
          setError('Failed to fetch status')
        }
      }
      poll()
      timer = setInterval(poll, 1000)
    }
    return () => timer && clearInterval(timer)
  }, [jobId])

  const createJob = async () => {
    setError('')
    setStatus('')
    setJobId('')
    try {
      const res = await fetch('http://localhost:8000/v1/generations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      })
      const json = await res.json()
      setJobId(json.job_id)
      setStatus(json.status)
    } catch (e) {
      setError('Failed to create job')
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1>Multimodal Fusion Viewer</h1>
      <p>Job results will appear here</p>
      <div style={{ marginTop: 16 }}>
        <input
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          style={{ padding: 8, width: '60%' }}
        />
        <button onClick={createJob} style={{ padding: '8px 16px', marginLeft: 8 }}>Create Job</button>
      </div>
      {jobId && (
        <div style={{ marginTop: 16 }}>
          <div><strong>Job ID:</strong> {jobId}</div>
          <div><strong>Status:</strong> {status}</div>
        </div>
      )}
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  )
}
