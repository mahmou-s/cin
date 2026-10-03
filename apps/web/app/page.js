'use client';
import TokenSettings from './components/TokenSettings';
import {useState} from 'react';
import SubmissionForm from './components/SubmissionForm';
import GraphVisualization from './components/GraphVisualization';
import OpportunityExplorer from './components/OpportunityExplorer';
import PathExplorer from './components/PathExplorer';
import ScenarioEngine from './components/ScenarioEngine';
import ScenarioComparison from './components/ScenarioComparison';
import IntelligenceDashboard from './components/IntelligenceDashboard';
import CivilizationalRelations from './components/CivilizationalRelations';
import CivilizationalOpportunityPaths from './components/CivilizationalOpportunityPaths';
import OpportunityReview from './components/OpportunityReview';
import LogisticsIntelligence from './components/LogisticsIntelligence';
import ValueChainIntelligence from './components/ValueChainIntelligence';
import AdaptiveClientIntelligence from './components/AdaptiveClientIntelligence';
export default function Home(){const [refresh,setRefresh]=useState(0);return <main><header><h1>منصة الشبكة الحضارية العالمية</h1><p>CIN · Evidence-first capability matching · Governed outreach · v2.0</p><nav><a href="/review">مركز التحقق</a> <a className="home-logistics-button" href="#logistics">🚚 اللوجستيات</a></nav></header><IntelligenceDashboard/><AdaptiveClientIntelligence/><LogisticsIntelligence/><ValueChainIntelligence/><CivilizationalRelations/><CivilizationalOpportunityPaths/><OpportunityReview/><section className="grid"><TokenSettings/><SubmissionForm onSubmitted={()=>setRefresh(x=>x+1)}/><GraphVisualization refresh={refresh}/>
<OpportunityExplorer refresh={refresh}/><PathExplorer refresh={refresh}/><ScenarioEngine/><ScenarioComparison/></section></main>}
