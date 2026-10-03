'use client';
import {useState} from 'react';

const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';

export default function IntelligenceDashboard(){
 const [q,setQ]=useState(''); const [results,setResults]=useState([]); const [profileId,setProfileId]=useState(''); const [profile,setProfile]=useState(null); const [error,setError]=useState('');
 async function search(e){e?.preventDefault(); if(q.trim().length<2)return; setError(''); const r=await fetch(`${API}/search?q=${encodeURIComponent(q)}`); if(!r.ok){setError('تعذر تنفيذ البحث');return;} const d=await r.json(); setResults(d.items||[]);}
 async function loadProfile(){ if(!profileId)return; setError(''); const r=await fetch(`${API}/communities/${profileId}/intelligence-profile`); if(!r.ok){setError('لم يتم العثور على المجتمع أو أن المعرّف غير صحيح');return;} setProfile(await r.json()); }
 return <section className="card intelligence" dir="rtl">
  <div className="row"><div><h2>مركز الذكاء الحضاري</h2><p>بحث موحّد وملف استخباراتي مجتمعي مبني على الحقائق الموثقة.</p></div><span className="badge">CIN 1.0</span></div>
  <form onSubmit={search} className="searchbar"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="ابحث عن مجتمع، قدرة، فرصة، أو سيناريو..."/><button>بحث</button></form>
  {results.length>0 && <div className="results"><h3>نتائج البحث</h3>{results.map(x=><div className="result" key={`${x.type}-${x.id}`}><b>{x.title}</b><small>{x.type} · {x.subtitle}</small>{x.type==='community'&&<button onClick={()=>{setProfileId(x.id);setTimeout(loadProfile,0)}}>فتح الملف</button>}</div>)}</div>}
  <div className="profile-loader"><h3>فتح ملف مجتمع</h3><div className="inline"><input value={profileId} onChange={e=>setProfileId(e.target.value)} placeholder="Community ID"/><button onClick={loadProfile}>فتح</button></div></div>
  {error&&<p className="error">{error}</p>}
  {profile&&<div className="profile"><h2>{profile.community.name}</h2><p>{profile.community.location||profile.community.country_code} {profile.community.population?`· السكان: ${profile.community.population.toLocaleString()}`:''}</p><p>{profile.community.description}</p>
   <div className="stats"><div><b>{profile.verified_capabilities.length}</b><span>قدرات موثقة</span></div><div><b>{profile.evidence_count}</b><span>أدلة</span></div><div><b>{profile.opportunities.length}</b><span>فرص مرتبطة</span></div><div><b>{profile.scenarios.length}</b><span>سيناريوهات</span></div></div>
   <h3>القدرات الموثقة</h3><div className="cap-grid">{profile.verified_capabilities.map(c=><div className="cap" key={c.assertion_id}><b>{c.code} · {c.name}</b><small>{c.domain} · {c.maturity_level}</small><span>الثقة: {c.confidence_level} ({Number(c.confidence_score).toFixed(2)}) · الأدلة: {c.evidence_count}</span></div>)}</div>
   {profile.opportunities.length>0&&<><h3>فرص مرتبطة</h3>{profile.opportunities.map(o=><div className="opportunity" key={o.id}><b>{o.title}</b><p>{o.description}</p></div>)}</>}
   <div className="principles"><b>ضوابط التفسير:</b>{profile.principles.map(p=><span key={p}>{p}</span>)}</div>
  </div>}
 </section>
}
