import React, { useState, useEffect } from 'react';
import { 
  ComplianceReport, 
  ComplianceVerdict, 
  SampleScenario, 
  ComplianceStatus,
  DocItem
} from './types/compliance';
import { apiService } from './services/api';
import { Header } from './components/Header';
import { SampleScenarios } from './components/SampleScenarios';
import { DocumentUpload } from './components/DocumentUpload';
import { AgentLiveWorkflow } from './components/AgentLiveWorkflow';
import { ComplianceOverview } from './components/ComplianceOverview';
import { ComplianceMatrix } from './components/ComplianceMatrix';
import { EvidenceViewer } from './components/EvidenceViewer';
import { DiscrepancyRadar } from './components/DiscrepancyRadar';
import { RequirementsPanel } from './components/RequirementsPanel';
import { FindingsPanel } from './components/FindingsPanel';
import { AuditReportView } from './components/AuditReportView';
import { HumanReviewModal } from './components/HumanReviewModal';
import { ApiKeyModal } from './components/ApiKeyModal';

export const App: React.FC = () => {
  const [scenarios, setScenarios] = useState<SampleScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario-01-engineering-spec');
  
  const [referenceDocs, setReferenceDocs] = useState<DocItem[]>([]);
  const [submittedDocs, setSubmittedDocs] = useState<DocItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string>('');
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [selectedVerdict, setSelectedVerdict] = useState<ComplianceVerdict | undefined>(undefined);
  const [overrideVerdict, setOverrideVerdict] = useState<ComplianceVerdict | null>(null);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState<boolean>(false);

  const [activeProvider, setActiveProvider] = useState<string>(() => localStorage.getItem('agentic_llm_provider') || 'mock');
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('agentic_llm_api_key') || '');

  // Load sample scenarios on initial load
  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const data = await apiService.getSampleScenarios();
        setScenarios(data);
        if (data.length > 0) {
          const defaultScenario = data[0];
          setSelectedScenarioId(defaultScenario.id);
          const ref = [{ name: defaultScenario.reference_filename, text: defaultScenario.reference_text }];
          const sub = [{ name: defaultScenario.submitted_filename, text: defaultScenario.submitted_text }];
          setReferenceDocs(ref);
          setSubmittedDocs(sub);
          // Run the benchmark once so the dashboard is populated on first load.
          handleExecuteAudit(ref, sub, defaultScenario.domain);
        }
      } catch (err) {
        console.error('Failed to load initial scenarios', err);
      }
    };
    fetchSamples();
  }, []);

  const handleSelectScenario = (scenario: SampleScenario) => {
    setSelectedScenarioId(scenario.id);
    const ref = [{ name: scenario.reference_filename, text: scenario.reference_text }];
    const sub = [{ name: scenario.submitted_filename, text: scenario.submitted_text }];
    setReferenceDocs(ref);
    setSubmittedDocs(sub);
    handleExecuteAudit(ref, sub, scenario.domain);
  };

  // Splits the benchmark submission into two files so multi-document tracing can be seen end to end.
  const handleLoadMultiDocDemo = () => {
    const scenario = scenarios[0];
    if (!scenario) return;
    const marker = scenario.submitted_text.indexOf('SECTION 3');
    const cut = marker > 0 ? marker : Math.floor(scenario.submitted_text.length / 2);
    setReferenceDocs([{ name: scenario.reference_filename, text: scenario.reference_text }]);
    setSubmittedDocs([
      { name: 'design_and_materials_report.txt', text: scenario.submitted_text.slice(0, cut).trim() },
      { name: 'testing_and_inspection_report.txt', text: scenario.submitted_text.slice(cut).trim() },
    ]);
  };

  const handleExecuteAudit = async (refDocs?: DocItem[], subDocs?: DocItem[], domain?: string) => {
    const refs = refDocs ?? referenceDocs;
    const subs = subDocs ?? submittedDocs;
    if (refs.length === 0 || subs.length === 0) return;

    setIsLoading(true);
    setAnalysisError('');
    try {
      const generatedReport = await apiService.runComplianceAnalysis({
        reference_documents: refs,
        submitted_documents: subs,
        domain: domain,
        llm_provider: activeProvider,
        api_key: apiKey
      });
      setReport(generatedReport);
      if (generatedReport.requirements_matrix && generatedReport.requirements_matrix.length > 0) {
        // Start on the first non-compliant requirement so the key finding is visible immediately.
        const firstNonCompliant = generatedReport.requirements_matrix.find(v => v.status === 'Non-Compliant') || generatedReport.requirements_matrix[0];
        setSelectedVerdict(firstNonCompliant);
      }
    } catch (err: any) {
      console.error('Audit execution failed', err);
      const detail = err?.response?.data?.detail;
      setAnalysisError(typeof detail === 'string' ? detail : 'The compliance analysis could not be completed. Check that the backend is running, your provider is configured, and the documents are valid. No report was generated.');
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Reviewer overrides are persisted by the backend (matrix, score and overall status are recomputed there).
  const handleApplyOverride = async (requirementId: string, newStatus: ComplianceStatus, notes: string, reviewerName: string) => {
    if (!report) return;
    try {
      const updated = await apiService.submitOverride(report.job_id, {
        requirement_id: requirementId,
        new_status: newStatus,
        notes,
        reviewer_name: reviewerName
      });
      setReport(updated);
      const refreshed = updated.requirements_matrix.find(v => v.requirement_id === requirementId);
      if (refreshed) setSelectedVerdict(refreshed);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setAnalysisError(typeof detail === 'string' ? detail : 'The reviewer override could not be saved. The report was not changed.');
    }
  };

  const handleSaveConfig = (newProvider: string, newKey: string) => {
    setActiveProvider(newProvider);
    setApiKey(newKey);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 bg-grid-pattern">
      
      {/* Top Navigation */}
      <Header
        onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
        activeProvider={activeProvider}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Benchmark Scenario Selector */}
        {scenarios.length > 0 && (
          <SampleScenarios
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            onSelectScenario={handleSelectScenario}
            isLoading={isLoading}
          />
        )}

        {analysisError && (
          <div role="alert" className="mb-6 rounded-xl border border-rose-700/70 bg-rose-950/40 p-4 text-sm text-rose-200">
            <div className="font-semibold mb-1">Analysis failed — no compliance report was generated</div>
            <p>{analysisError}</p>
            <button type="button" className="mt-2 underline underline-offset-2" onClick={() => setAnalysisError('')}>Dismiss</button>
          </div>
        )}

        {/* Ingestion & Document Runner */}
        <DocumentUpload
          referenceDocs={referenceDocs}
          setReferenceDocs={setReferenceDocs}
          submittedDocs={submittedDocs}
          setSubmittedDocs={setSubmittedDocs}
          onRunAudit={() => handleExecuteAudit()}
          onLoadMultiDocDemo={scenarios.length > 0 ? handleLoadMultiDocDemo : undefined}
          isLoading={isLoading}
        />

        {/* Multi-Agent Orchestration Visualizer */}
        {report && (
          <AgentLiveWorkflow
            agentLogs={report.agent_audit_trail || []}
            isLoading={isLoading}
          />
        )}

        {/* Compliance Results Section */}
        {report && (
          <>
            {/* KPI Cards & Status Gauge */}
            <ComplianceOverview report={report} />

            {/* Extracted requirements */}
            <RequirementsPanel requirements={report.requirements || []} />

            {/* Traceable Requirements Matrix */}
            <ComplianceMatrix
              verdicts={report.requirements_matrix}
              onSelectEvidence={(v) => setSelectedVerdict(v)}
              onOpenOverrideModal={(v) => setOverrideVerdict(v)}
              selectedRequirementId={selectedVerdict?.requirement_id}
            />

            {/* Dual Document Side-by-Side Evidence Viewer */}
            <EvidenceViewer
              selectedVerdict={selectedVerdict}
              requirement={(report.requirements || []).find(r => r.id === selectedVerdict?.requirement_id)}
              referenceDocs={referenceDocs}
              submittedDocs={submittedDocs}
            />

            {/* Missing / conflicting / deviating information */}
            <FindingsPanel
              verdicts={report.requirements_matrix}
              onSelect={(v) => setSelectedVerdict(v)}
            />

            {/* Gaps, Discrepancies & Deviations Radar */}
            <DiscrepancyRadar discrepancies={report.discrepancies} />

            {/* Executive Audit Memo & PDF/CSV/JSON Exports */}
            <AuditReportView report={report} />
          </>
        )}

      </main>

      {/* Human Review Modal */}
      {overrideVerdict && (
        <HumanReviewModal
          verdict={overrideVerdict}
          onClose={() => setOverrideVerdict(null)}
          onSubmitOverride={handleApplyOverride}
        />
      )}

      {/* LLM / Engine Config Modal */}
      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => setIsApiKeyModalOpen(false)}
        activeProvider={activeProvider}
        onSaveConfig={handleSaveConfig}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>Agentic AI Document Intelligence & Compliance Checker &bull; 6-Agent LangGraph Architecture &bull; Strict Evidence Traceability</p>
      </footer>

    </div>
  );
};

export default App;
