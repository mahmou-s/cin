'use client';
import {useEffect,useState} from 'react';
const API='http://localhost:8000/api/v1';
export default function CivilizationalOpportunityPaths(){
 const [items,setItems]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{fetch(`${API}/civilizational-opportunities/discover?limit=24`).then(r=>{if(!r.ok)throw new Error();return r.json()}).then(d=>setItems(d.items||[])).catch(()=>setError('تعذر تحميل مسارات الفرص الحضارية')).finally(()=>setLoading(false))},[]);
 return <section className="card" dir="rtl"><div className="row"><div><h2>محرك الفرص الحضارية</h2><p>تحويل القدرات الموثقة إلى مسارات تحليلية قابلة للفحص.</p></div><span className="badge">CIN 1.2</span></div>
 {loading&&<p>جارٍ بناء المسارات...</p>}{error&&<p className="error">{error}</p>}
 {!loading&&!error&&items.length===0&&<p className="message">لا توجد مسارات مكتملة حاليًا. أضف قدرات موثقة عبر مجتمعات أو مجالات متعددة.</p>}
 <div className="relation-list">{items.map((x,i)=><article className="relation" key={i}><div className="relation-head"><b>{x.title}</b><span className="badge">دعم {Number(x.support).toFixed(2)}</span></div><p>{x.rationale}</p><div className="relation-caps">{x.steps.map((s,j)=><span key={j}>{s.code} · {s.capability} · {s.community} · أدلة {s.evidence_count}</span>)}</div><small>المسار المحتمل لا يثبت الرغبة في التعاون أو الجدوى الاقتصادية أو النجاح.</small></article>)}</div>
 <div className="principles"><b>قاعدة المحرك:</b><span>البيانات الموثقة → علاقة تكاملية → مسار قدرة → فرصة محتملة → فحص بشري.</span></div></section>
}
