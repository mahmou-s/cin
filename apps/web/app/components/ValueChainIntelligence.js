'use client';
import {useState} from 'react';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api/v1';
const token=()=>typeof window!=='undefined'?localStorage.getItem('cin_api_token')||'':'';
const authHeaders=()=>token()?{Authorization:`Bearer ${token()}`}:{};
const stages={SUPPLIER:'مورد مكوّن',MANUFACTURER:'مصنّع',EXPORTER:'مصدّر',IMPORTER:'مستورد',DISTRIBUTOR:'موزّع/وكيل',RETAILER:'تاجر تجزئة',SERVICE_PROVIDER:'خدمة وصيانة',CUSTOMER:'عميل'};
export default function ValueChainIntelligence(){
 const [productId,setProductId]=useState(''),[data,setData]=useState(null),[busy,setBusy]=useState(false),[msg,setMsg]=useState('');
 const load=async()=>{if(!productId)return;setBusy(true);setMsg('جاري تحميل سلسلة القيمة...');try{const r=await fetch(`${API}/value-chain/products/${productId}`,{headers:authHeaders()});const x=await r.json();if(!r.ok)throw new Error(x.detail||`HTTP ${r.status}`);setData(x);setMsg(`تم تحميل ${x.components.length} مكوّن و${x.links.length} رابط في سلسلة القيمة.`);}catch(e){setData(null);setMsg(`تعذر التحميل: ${e.message}`)}finally{setBusy(false)}};
 return <section id="value-chain" className="card" dir="rtl">
  <div className="row"><div><h2>🔗 شبكة المنتج وسلسلة القيمة</h2><p>تتبع المكوّنات من مورديها، ثم انتقال المنتج عبر التصنيع والتصدير والاستيراد والتوزيع والتجزئة والخدمة.</p></div><span className="badge">Product Network · Value Chain</span></div>
  <div className="searchbar"><input value={productId} onChange={e=>setProductId(e.target.value)} placeholder="معرّف المنتج (UUID)"/><button onClick={load} disabled={busy}>{busy?'جارٍ التحميل...':'عرض السلسلة'}</button></div>
  {msg&&<div className="message">{msg}</div>}
  {data&&<><h3>المكوّنات</h3><div className="logistics-route-list">{data.components.map(c=><article className="logistics-route" key={c.id}><div className="row"><strong>{c.component_product_id}</strong><span className="badge">{c.source_type==='EXTERNAL'?'خارجي':'داخلي'}</span></div><small>{c.quantity!=null?`${c.quantity} ${c.unit||''}`:'الكمية غير مسجلة'} · {c.verification_status}</small></article>)}</div><h3>مسار القيمة</h3><div className="logistics-route-list">{data.links.map(l=><article className="logistics-route" key={l.id}><div className="row"><strong>{l.sequence_order}. {stages[l.stage_type]||l.stage_type}</strong><span className="badge">{l.relationship_type}</span></div><small>{l.from_profile_id} → {l.to_profile_id} · {l.verification_status}</small></article>)}</div></>}
  <small>السلسلة تصف علاقات وقدرات مسجلة؛ لا تعني أن علاقة تجارية أو توريدًا قد تم الاتفاق عليه ما لم توجد أدلة وحالة تحقق مناسبة.</small>
 </section>
}
