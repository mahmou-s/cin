'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

const ForceGraph = dynamic(() => import('react-force-graph-2d'), { ssr: false });
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function GraphVisualization({ refresh = 0 }) {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [state, setState] = useState('loading');
  const [selected, setSelected] = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    let active = true;
    setState('loading');
    fetch(`${API}/graph/capabilities?limit=500`, { cache: 'no-store' })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'GRAPH_LOAD_FAILED');
        return payload;
      })
      .then((payload) => {
        if (active) {
          setData({ nodes: payload.nodes || [], links: payload.links || [] });
          setState('ready');
        }
      })
      .catch(() => active && setState('error'));
    return () => { active = false; };
  }, [refresh]);

  return (
    <section className="card graph-card" dir="rtl">
      <div className="row">
        <div>
          <h2>خريطة المعرفة الحضارية</h2>
          <p>المجتمع ← القدرة الموثقة ← نوع القدرة</p>
        </div>
        <span className="badge">Neo4j</span>
      </div>

      {state === 'loading' && <p className="message">جاري تحميل الجراف…</p>}
      {state === 'error' && <p className="error">تعذر الوصول إلى Knowledge Graph. تأكد من تشغيل Neo4j والـ Worker.</p>}

      {state === 'ready' && (
        <div className="graph-shell" dir="ltr">
          <ForceGraph
            ref={ref}
            graphData={data}
            nodeLabel={(node) => `${node.type}: ${node.label}`}
            nodeAutoColorBy="type"
            nodeRelSize={6}
            linkLabel={(link) => link.type}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={1}
            onNodeClick={(node) => setSelected(node)}
            width={Math.max(520, typeof window !== 'undefined' ? window.innerWidth * 0.45 : 700)}
            height={560}
          />
        </div>
      )}

      {selected && (
        <div className="graph-selection">
          <b>{selected.label}</b>
          <span>{selected.type}{selected.code ? ` · ${selected.code}` : ''}</span>
          {selected.confidence != null && <span>الثقة: {Number(selected.confidence).toFixed(2)}</span>}
        </div>
      )}
    </section>
  );
}
