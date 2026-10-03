'use client';

import {useMemo} from 'react';

export default function UserProfile({profile}) {
  const confidence = Math.round((profile?.ai_confidence_score ?? 0) * 100);
  const products = profile?.products ?? [];
  const location = [profile?.village, profile?.center, profile?.governorate, profile?.country_code]
    .filter(Boolean).join(' · ');
  const domains = useMemo(() => profile?.activity_domains ?? [], [profile]);

  if (!profile) return <section className="card profile-card"><p>لا توجد بيانات بروفايل بعد.</p></section>;

  return <section className="card profile-card">
    <div className="profile-cover" />
    <div className="profile-head">
      <div className="profile-avatar">{(profile.display_name || '?').slice(0, 1)}</div>
      <div>
        <h2>{profile.display_name}</h2>
        <p>{profile.organization_name || profile.entity_type}</p>
        <small>{location}</small>
      </div>
      <div className="confidence-card">
        <span>AI Confidence Score</span>
        <strong>{confidence}%</strong>
        <small>{profile.ai_confidence_level || 'UNVERIFIED'}</small>
      </div>
    </div>

    <div className="chips">{domains.map((d) => <span key={d}>{d}</span>)}</div>
    {profile.bio && <p className="profile-bio">{profile.bio}</p>}

    <div className="stats">
      <div><b>{products.length}</b><span>المنتجات / الأنشطة</span></div>
      <div><b>{profile.commercial_register ? 'موثق' : '—'}</b><span>السجل التجاري</span></div>
      <div><b>{profile.entity_type}</b><span>نوع الكيان</span></div>
      <div><b>{confidence}%</b><span>ثقة الأدلة</span></div>
    </div>

    <h3>المنتجات والقدرات</h3>
    <div className="profile-products">
      {products.map((product) => <article className="product-card" key={product.id}>
        <div className="row"><h4>{product.name}</h4><span className="badge">{product.category}</span></div>
        {product.description && <p>{product.description}</p>}
        <div className="chips">{(product.features || []).map((f) => <span key={f}>{f}</span>)}</div>
        {product.production_capacity && <p><strong>القدرة:</strong> {product.production_capacity.quantity} {product.production_capacity.unit}
          {product.production_capacity.delivery_days != null && ` · التسليم خلال ${product.production_capacity.delivery_days} يوم`}</p>}
        {product.additional_services?.length > 0 && <p><strong>خدمات إضافية:</strong> {product.additional_services.join('، ')}</p>}
        {product.support_types?.length > 0 && <p><strong>الدعم المطلوب:</strong> {product.support_types.join('، ')}</p>}
      </article>)}
      {!products.length && <p>أضف أول منتج أو نشاط لعرضه للمستثمرين.</p>}
    </div>
  </section>;
}
