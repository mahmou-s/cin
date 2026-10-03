'use client';
import {useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
export default function ScenarioEngine(){
 const [goal,setGoal]=useState('تطوير صناعة غذائية قابلة للتصدير'); const [items,setItems]=useState([]); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
 async function generate(){setBusy(true);setError('');try{const r=await fetch(`${API}/scenarios/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal,limit:5})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'SCENARIO_FAILED');setItems(d.items||[])}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className="card"><h2>محرك السيناريوهات</h2><p>حوّل هدفًا عامًا إلى مسارات محتملة مبنية على القدرات الموثقة فقط.</p><textarea value={goal} onChange={e=>setGoal(e.target.value)} rows={3}/><button onClick={generate} disabled={busy}>{busy?'جارٍ بناء السيناريو…':'ابنِ سيناريو'}</button>{error&&<p className="error">{error}</p>}{items.map(s=><div className="scenario" key={s.id}><h3>{s.goal}</h3><strong>{s.steps.map(x=>x.code).join(' → ')}</strong><p>Support: {s.result.support_score}</p><ol>{s.steps.map(x=><li key={x.assertion_id}><b>{x.code} — {x.capability}</b> · {x.community}<br/><small>{x.rationale} · Confidence {x.confidence}</small></li>)}</ol><details><summary>الافتراضات والقيود</summary><ul>{s.assumptions.map((a,i)=><li key={i}>{a}</li>)}</ul></details></div>)}</section>
}
