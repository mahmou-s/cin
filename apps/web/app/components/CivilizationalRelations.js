'use client';
import {useEffect,useState} from 'react';
const API='http://localhost:8000/api/v1';
export default function CivilizationalRelations(){
 const [items,setItems]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
 async function load(){setLoading(true);setError('');try{const r=await fetch(`${API}/relations/communities?limit=80`);if(!r.ok)throw new Error();const d=await r.json();setItems(d.items||[])}catch(e){setError('تعذر تحميل خريطة العلاقات الحضارية')}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 return <section className="card relations" dir="rtl">
  <div className="row"><div><h2>خريطة التكامل الحضاري</h2><p>روابط محتملة بين مجتمعات تمتلك قدرات موثقة ومتكاملة.</p></div><span className="badge">CIN 1.1</span></div>
  {loading&&<p>جارٍ تحليل القدرات الموثقة...</p>}{error&&<p className="error">{error}</p>}
  {!loading&&!error&&items.length===0&&<p className="message">لا توجد علاقة تكاملية قابلة للعرض حاليًا. أضف قدرات موثقة لمجتمعات متعددة.</p>}
  <div className="relation-list">{items.map((x,i)=><article className="relation" key={`${x.source_community.id}-${x.target_community.id}-${x.source_capability.code}-${i}`}>
   <div className="relation-head"><b>{x.source_community.name}</b><span>↔</span><b>{x.target_community.name}</b></div>
   <div className="relation-caps"><span>{x.source_capability.code} · {x.source_capability.name}</span><strong>{x.relation_type}</strong><span>{x.target_capability.code} · {x.target_capability.name}</span></div>
   <p>{x.rationale}</p><small>الثقة: {Number(x.support.source_confidence).toFixed(2)} / {Number(x.support.target_confidence).toFixed(2)}</small>
  </article>)}</div>
  <div className="principles"><b>قاعدة الخريطة:</b><span>هي تكشف إمكانية التكامل من واقع القدرات الموثقة؛ لا تثبت الرغبة في التعاون أو النجاح أو الجدوى الاقتصادية، ولا ترتب المجتمعات.</span></div>
 </section>
}
