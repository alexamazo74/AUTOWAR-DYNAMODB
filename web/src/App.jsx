import React, {useEffect, useState} from 'react'

export default function App(){
  const [scores, setScores] = useState([])
  useEffect(()=>{
    fetch('/evaluations')
      .then(r=>r.json())
      .then(data=>console.log('evals',data))
  },[])

  return (
    <div style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>AutoWAR — Scores</h1>
      <p>This is a minimal scaffold. Implement UI to list evaluations and per-BP scores.</p>
      <ul>
        {scores.map(s=> <li key={s.id}>{s.bp_id} — {s.total}</li>)}
      </ul>
    </div>
  )
}
