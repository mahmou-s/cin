'use client';
import {useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
const token=()=>typeof window!=='undefined'?localStorage.getItem('cin_api_token')||'':'';
const authHeaders=()=>token()?{Authorization:`Bearer ${token()}`}:{};

export default function LogisticsIntelligence(){
 const [origin,setOrigin]=useState(''),[destination,setDestination]=useState(''),[mode,setMode]=useState('');
 const [routes,setRoutes]=useState([]),[busy,setBusy]=useState(false),[msg,setMsg]=useState('');
 const search=async()=>{setBusy(true);setMsg('جاري البحث في المسارات اللوجستية الموثقة...');try{
   const q=new URLSearchParams(); if(origin)q.set('origin',origin); if(destination)q.set('destination',destination); if(mode)q.set('mode',mode);
   const r=await fetch(`${API}/logistics/routes${q.toString()?`?${q}`:''}`,{headers:authHeaders()});
   const x=await r.json(); if(!r.ok)throw new Error(x.detail||`HTTP ${r.status}`);
   setRoutes(x||[]);setMsg(`تم العثور على ${x.length} مسار لوجستي موثق.`);
 }catch(e){setRoutes([]);setMsg(`تعذر تحميل المسارات: ${e.message}`)}finally{setBusy(false)}};
 return <section id="logistics" className="card logistics-card" dir="rtl">
   <div className="row"><div><h2>🚚 الذكاء اللوجستي</h2><p>طبقة تربط المنتج بمسارات النقل والتخزين والتخليص والتتبع، مع إبقاء البيانات الموثقة منفصلة عن التقديرات.</p></div><span className="badge">C11 · Logistics Capability</span></div>
   <div className="logistics-principles"><span>الإنتاج → النقل</span><span>التخزين → السوق</span><span>Evidence → Verification</span><span>Local + International</span></div>
   <div className="searchbar"><input value={origin} onChange={e=>setOrigin(e.target.value)} placeholder="نقطة الانطلاق"/><input value={destination} onChange={e=>setDestination(e.target.value)} placeholder="الوجهة"/><select value={mode} onChange={e=>setMode(e.target.value)}><option value="">كل الوسائل</option><option value="ROAD">بري</option><option value="RIVER">نهري</option><option value="SEA">بحري</option><option value="AIR">جوي</option><option value="MULTIMODAL">متعدد الوسائط</option></select><button onClick={search} disabled={busy}>{busy?'جارٍ البحث...':'ابحث'}</button></div>
   {msg&&<div className="message">{msg}</div>}
   <div className="logistics-route-list">{routes.map(r=><article className="logistics-route" key={r.id}><div className="row"><strong>{r.origin} → {r.destination}</strong><span className="badge">{r.mode}</span></div><div className="chips"><span>{r.distance_km!=null?`${r.distance_km} km`:'المسافة غير مسجلة'}</span><span>{r.estimated_days!=null?`${r.estimated_days} يوم`:'المدة غير مسجلة'}</span>{r.cold_chain&&<span>Cold Chain</span>}{r.customs_support&&<span>Customs</span>}{r.tracking_available&&<span>Tracking</span>}</div><small>الحالة: {r.verification_status}</small></article>)}</div>
   <small>اللوجستيات هنا Capability موثقة وليست وعدًا بسعر أو زمن نقل فعلي. أي قرار تشغيلي يحتاج تحققًا مستقلًا.</small>
 </section>
}
