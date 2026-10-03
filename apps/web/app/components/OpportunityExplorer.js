'use client';
import {useEffect,useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
const token=()=>typeof window!=='undefined'?localStorage.getItem('cin_api_token')||'':'';
const authHeaders=()=>token()?{Authorization:`Bearer ${token()}`}:{ };

export default function OpportunityExplorer({refresh}){
 const [items,setItems]=useState([]),[busy,setBusy]=useState(false),[msg,setMsg]=useState(''),[query,setQuery]=useState('');
 const load=()=>fetch(`${API}/opportunities/explorer${query?`?query=${encodeURIComponent(query)}`:''}`,{headers:authHeaders()})
   .then(async r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()})
   .then(x=>setItems(x.items||[])).catch(()=>setItems([]));
 useEffect(()=>{load()},[refresh]);
 const discover=async()=>{setBusy(true);setMsg('جاري تحليل المنتجات والقدرات والأدلة الموثقة...');try{
   const r=await fetch(`${API}/opportunities/explorer${query?`?query=${encodeURIComponent(query)}`:''}`,{headers:authHeaders()});
   const x=await r.json(); if(!r.ok) throw new Error(x.detail||`HTTP ${r.status}`);
   setItems(x.items||[]);setMsg(`تم العثور على ${x.count||0} فرصة محتملة قابلة للتتبع.`);
 }catch(e){setMsg(`تعذر تشغيل الكشاف: ${e.message}`)}finally{setBusy(false)}};
 return <section className="card" dir="rtl">
   <div className="row"><div><h2>AI Investment Opportunity Explorer</h2><p>يحلل Product + Capability + Verified Evidence، ثم يعرض الهدف والطاقة الإنتاجية وطلبات الدعم مع مسار الأدلة.</p></div></div>
   <div className="row"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="ابحث عن منتج أو هدف أو فئة"/><button onClick={discover} disabled={busy}>{busy?'جارٍ التحليل...':'اكتشف الفرص'}</button></div>
   {msg&&<div className="message">{msg}</div>}
   <div>{items.map(o=><article className="opportunity" key={`${o.title}-${o.products.map(p=>p.id).join('-')}`}>
     <h3>{o.title}</h3><p>{o.description}</p>
     <small>Confidence floor: {o.confidence_floor} · Engine: {o.engine}</small>
     <div className="chips">{o.capability_pattern.codes.map(c=><span key={c}>{c}</span>)}</div>
     {o.products.map(p=><div key={p.id} className="opportunity-detail"><strong>{p.name}</strong><div>الهدف: {p.goal||'غير محدد'}</div><div>الطاقة: {p.capacity?`${p.capacity.quantity} ${p.capacity.unit}`:'غير مسجلة'}</div><div>الأدلة الموثقة: {p.verified_evidence_ids.length}</div></div>)}
     <details><summary>لماذا ظهرت هذه الفرصة؟</summary><ul>{o.explanation.map(x=><li key={x}>{x}</li>)}</ul><div>Evidence IDs: {o.evidence_trace.verified_evidence_ids.join(', ')}</div></details>
     <small>هذه فرصة محتملة وليست توصية استثمارية أو إثباتًا للجدوى.</small>
   </article>)}</div>
 </section>
}
