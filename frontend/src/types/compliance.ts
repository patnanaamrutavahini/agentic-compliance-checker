export type ComplianceStatus = 
  | 'Compliant' 
  | 'Partially Compliant' 
  | 'Non-Compliant' 
  | 'Requires Human Review';

export type SeverityLevel = 
  | 'Critical' 
  | 'High' 
  | 'Medium' 
  | 'Low' 
  | 'Informational';

export interface EvidenceLocation {
  document_id: string;
  document_name: string;
  page_number?: number;
  section_title?: string;
  start_char?: number;
  end_char?: number;
  line_number?: number;
  snippet: string;
  similarity_score?: number;
}

export interface RequirementItem {
  id: string;
  text: string;
  source_document?: string;
  section: string;
  category: string;
  severity: SeverityLevel;
  mandatory: boolean;
  source_clause?: string;
  expected_evidence_type?: string;
}

export interface HumanOverride {
  is_overridden: boolean;
  original_status?: ComplianceStatus;
  overridden_status?: ComplianceStatus;
  reviewer_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

export interface DiscrepancyItem {
  id: string;
  requirement_id: string;
  discrepancy_type: string;
  severity: SeverityLevel;
  description: string;
  expected_statement: string;
  found_statement?: string;
  remediation_recommendation: string;
}

export interface ComplianceVerdict {
  requirement_id: string;
  requirement_text: string;
  category: string;
  severity: SeverityLevel;
  mandatory: boolean;
  status: ComplianceStatus;
  confidence_score: number;
  evidence_snippet?: string;
  evidence_location?: EvidenceLocation;
  supporting_evidence?: EvidenceLocation[];
  rationale: string;
  missing_elements: string[];
  conflicting_elements: string[];
  deviations: string[];
  remarks: string;
  discrepancy_details?: DiscrepancyItem;
  human_override?: HumanOverride;
}

export interface AgentExecutionEvent {
  agent_id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  duration_ms?: number;
  thought_process: string[];
  output_summary?: string;
  tokens_used: number;
  artifacts_generated?: string[];
}

export interface ComplianceReport {
  job_id: string;
  timestamp: string;
  reference_doc_name: string;
  submitted_doc_name: string;
  reference_doc_names?: string[];
  submitted_doc_names?: string[];
  domain: string;
  overall_status: ComplianceStatus;
  compliance_score: number;
  confidence_score: number;
  total_requirements: number;
  compliant_count: number;
  partial_count: number;
  non_compliant_count: number;
  human_review_count: number;
  critical_violations_count: number;
  executive_summary: string;
  requirements?: RequirementItem[];
  requirements_matrix: ComplianceVerdict[];
  discrepancies: DiscrepancyItem[];
  agent_audit_trail: AgentExecutionEvent[];
  classification?: Record<string, unknown>;
  pipeline_info?: Record<string, string>;
  export_formats: Record<string, string>;
}

export interface SampleScenario {
  id: string;
  title: string;
  domain: string;
  description: string;
  reference_filename: string;
  submitted_filename: string;
  reference_text: string;
  submitted_text: string;
  expected_outcome_summary: string;
}

/** A document held in the UI (uploaded file or pasted text). */
export interface DocItem {
  id?: string;
  name: string;
  text: string;
  pages?: number;
}
