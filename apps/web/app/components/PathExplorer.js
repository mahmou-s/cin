'use client';
import {useEffect,useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
export default function PathExplorer({refresh}){
  const [items,setItems]=useState([]); const [busy,setBusy]=useState(false); const [result,setResult]=useState(null);
  async function load(){setBusy(true);try{const r=await fetch(`${API}/reasoning/paths?limit=30`,{cache:'no-store'});setItems((await r.json()).items||[])}finally{setBusy(false)}}
  useEffect(()=>{load()},[refresh]);
  async function analyze(item){setBusy(true);try{const r=await fetch(`${API}/reasoning/paths/analyze`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({assertion_ids:item.assertions})});setResult(await r.json())}finally{setBusy(false)}}
  return <section className="card"><h2>مسارات القدرات</h2><p>اكتشاف سلاسل تكامل محتملة من القدرات الموثقة، دون ترتيب للمجتمعات.</p>{busy&&<small>جارٍ التحليل…</small>}{items.map((x,i)=><div className="path" key={i}><strong>{x.path}</strong><div>{x.communities.map(c=>c.name).join(' → ')}</div><small>Support: {x.support_score}</small><button onClick={()=>analyze(x)}>تحليل المسار</button></div>)}{result&&<pre className="reasoning">{JSON.stringify(result,null,2)}</pre>}</section>
}
