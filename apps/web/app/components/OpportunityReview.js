'use client';
import {useEffect,useState} from 'react';
const API='http://localhost:8000/api/v1';
export default function OpportunityReview(){const [items,setItems]=useState([]),[note,setNote]=useState({}),[busy,setBusy]=useState('');
 const load=()=>fetch(`${API}/civilizational-opportunities/review-queue`).then(r=>r.json()).then(d=>setItems(d.items||[]));
 useEffect(()=>{load()},[]);
 const act=async(id,decision)=>{setBusy(id+decision);await fetch(`${API}/civilizational-opportunities/${id}/review`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision,actor:'human-reviewer',note:note[id]||null})});setBusy('');load()};
 return <section className="card" dir="rtl"><div className="row"><div><h2>مراجعة الفرص الحضارية</h2><p>القرار البشري هو الذي يحول المسار التحليلي إلى حالة مراجعة موثقة.</p></div><span className="badge">CIN 1.3</span></div>{items.length===0?<p className="message">لا توجد فرص تنتظر المراجعة.</p>:items.map(o=><article className="review-item" key={o.id}><b>{o.title}</b><span>{o.description}</span><small>الحالة الحالية: {o.status}</small><textarea placeholder="ملاحظة المراجع" value={note[o.id]||''} onChange={e=>setNote({...note,[o.id]:e.target.value})}/><div><button disabled={busy} onClick={()=>act(o.id,'ACCEPT')}>اعتماد كفرصة محتملة</button><button disabled={busy} onClick={()=>act(o.id,'MODIFY')}>إعادة للمراجعة</button><button disabled={busy} onClick={()=>act(o.id,'REJECT')}>رفض</button></div></article>)}</section>}
