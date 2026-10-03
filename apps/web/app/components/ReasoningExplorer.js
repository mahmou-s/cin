'use client';
import {useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
export default function ReasoningExplorer({opportunityId}){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 if(!opportunityId) return null;
 const run=async()=>{setBusy(true);setError('');try{const r=await fetch(`${API}/ai/opportunities/${opportunityId}/analyze`,{method:'POST'});const x=await r.json();if(!r.ok) throw new Error(x.detail||'REASONING_FAILED');setData(x)}catch(e){setError(e.message)}finally{setBusy(false)}};
 return <div className="reasoning"><button onClick={run} disabled={busy}>{busy?'جارٍ التحليل...':'حلّل الفرصة بالذكاء التفسيري'}</button>{error&&<p className="error">{error}</p>}{data&&<div><h4>فرضية التحليل</h4><p>{data.result.hypothesis}</p><div className="chips">{data.result.capabilities.map(x=><span key={x}>{x}</span>)}</div><p><strong>ثقة التحليل:</strong> {Math.round(data.result.confidence*100)}%</p><small>هذه نتيجة تحليلية قابلة للمراجعة وليست إثباتًا لجدوى التعاون.</small></div>}</div>
}
