from typing import List, Dict, Optional
from app.models.schemas import SampleScenario

SAMPLE_SCENARIOS: List[SampleScenario] = [
    SampleScenario(
        id="scenario-01-engineering-spec",
        title="Aerospace & Defense Engineering Spec vs Supplier Submission",
        domain="Aerospace & Mechanical Engineering",
        description="Standard compliance check from the problem statement: Reference requires design calculations, material specifications, inspection requirements, and testing procedures. Subcontractor report has calculations, materials, and testing, but lacks inspection protocols.",
        reference_filename="Aero_Pressure_Vessel_Spec_STD-4402.txt",
        submitted_filename="Supplier_Batch_Conformance_Report_V3.txt",
        reference_text="""SPECIFICATION: AERO-STD-4402 (REVISION D)
TITLE: High-Pressure Fuel Manifold Subsystem Qualification Requirements

1.0 SCOPE & APPLICABILITY
This standard establishes mandatory technical criteria for fabricated cryogenic fuel manifolds.

2.0 MANDATORY DELIVERABLES
2.1 Design Calculations: The submitted report must contain complete design calculations, finite element stress analysis (FEA), and burst pressure safety margin verifications exceeding 2.5x nominal load.
2.2 Material Specifications: The submitted document must state certified material specifications (Inconel 718 or Titanium Grade 5), heat treatment batch records, and certified chemical composition limits.
2.3 Inspection Requirements: The submission must contain comprehensive non-destructive examination (NDE) inspection requirements, including 100% X-ray radiography and fluorescent penetrant inspection (FPI) acceptance standards.
2.4 Testing Procedures: The submitted report must define hydrostatic proof pressure testing procedures, cryogenic thermal cycling protocols (-196°C to +120°C), and leak decay rate measurement criteria.""",
        submitted_text="""SUPPLIER DELIVERABLE CONFORMANCE REPORT
VENDOR: Apex Precision Propulsion Ltd.
ITEM: Cryogenic Fuel Manifold Assembly (Part #APX-9921)

SECTION 1: DESIGN CALCULATIONS & FINITE ELEMENT ANALYSIS
Design calculations were conducted in accordance with ASME Section VIII and AERO-STD-4402. Finite element stress analysis verified a maximum von Mises stress of 412 MPa under peak operating pressure (180 bar). The computed safety margin factor is 2.74x, exceeding the mandatory 2.5x threshold.

SECTION 2: MATERIAL SPECIFICATION & HEAT TREATMENT
Fabricated exclusively from vacuum-induction melted Inconel 718 per AMS 5662. Solution annealed at 980°C for 1 hour followed by two-stage precipitation hardening. Chemical composition analysis confirms Nickel 52.8%, Chromium 19.1%, Molybdenum 3.05%, conforming strictly to certified aerospace limits.

SECTION 3: TESTING PROCEDURE & QUALIFICATION LOG
Hydrostatic proof pressure testing executed at 1.5x design pressure (270 bar) held for 15 minutes with zero measurable pressure decay. Cryogenic thermal shock cycling completed for 25 consecutive cycles (-196°C liquid nitrogen dip to +120°C forced hot air). Helium mass spectrometer leak rate was below 1.0 x 10^-8 atm cc/sec.

NOTE: Inspection protocols, X-ray radiography records, and FPI reports are currently pending secondary metallurgical subcontractor sign-off and were omitted from this revision.""",
        expected_outcome_summary="Design Calculations: Compliant | Material Specification: Compliant | Testing Procedure: Compliant | Inspection Requirements: Non-Compliant / Missing. Overall: Partially Compliant / Non-Compliant."
    ),
    SampleScenario(
        id="scenario-02-iso9001-quality",
        title="ISO 9001:2015 Clause 8.4 vs Supplier Quality Manual",
        domain="Quality Management Systems (ISO 9001)",
        description="Evaluation of supplier quality documentation against ISO 9001:2015 Clause 8.4 control of externally provided processes, products and services.",
        reference_filename="ISO_9001_Section_8_4_Standard.txt",
        submitted_filename="Supplier_Quality_Management_Manual.txt",
        reference_text="""INTERNATIONAL STANDARD ISO 9001:2015
Clause 8.4: Control of externally provided processes, products, and services

8.4.1 General Requirements: The organization shall ensure that externally provided processes, products and services conform to requirements, establishing criteria for the evaluation, selection, monitoring of performance, and re-evaluation of external providers.
8.4.2 Traceability & Calibration: The organization shall maintain documented information of measuring equipment calibration traceable to international or national measurement standards.
8.4.3 Corrective Action Procedures: The organization shall establish a defined corrective and preventive action (CAPA) workflow with a maximum root-cause closure window of 30 business days.
8.4.4 Risk Assessment: Documented risk assessment must be performed for all critical suppliers prior to purchase order release.""",
        submitted_text="""GLOBAL MANUFACTURING CORP - QUALITY POLICY MANUAL (REV 5.2)

1.0 SUPPLIER SELECTION & EVALUATION
All tier-1 and tier-2 suppliers undergo quarterly scorecard evaluations, initial qualification questionnaires, and periodic supplier audits. Documented selection records are maintained in the ERP system.

2.0 EQUIPMENT CALIBRATION & METROLOGY
All dimensional inspection gauges, torque wrenches, and digital micrometers are calibrated every 6 months with calibration certs traceable directly to NIST standards.

3.0 QUALITY INCIDENT ESCALATION
When a non-conformance is raised, an incident log is generated. Investigation commences within 10 days, but closure timelines depend on production workload without a fixed 30-day mandate.

4.0 SUPPLIER RISK PROFILES
Supplier assessments focus primarily on financial stability and lead times. Formal failure modes risk matrices (FMEA) for suppliers have not yet been formalized into standard operating procedures.""",
        expected_outcome_summary="Supplier Selection: Compliant | Calibration: Compliant | CAPA: Partially Compliant (Deviating timeline) | Risk Assessment: Non-Compliant. Overall: Partially Compliant."
    ),
    SampleScenario(
        id="scenario-03-gdpr-privacy",
        title="GDPR Data Retention Policy vs Cloud Processor Agreement",
        domain="Data Privacy & Governance (GDPR / ISO 27001)",
        description="Audit of vendor cloud processing contract against GDPR Article 28 data retention and incident notification rules.",
        reference_filename="GDPR_Art28_Standard_Contractual_Clauses.txt",
        submitted_filename="CloudVendor_Data_Processing_Agreement.txt",
        reference_text="""REGULATION (EU) 2016/679 (GDPR) - DATA PROCESSING SPECIFICATION

Article 28.1: Encryption Standards - The processor shall implement state-of-the-art encryption at rest (minimum AES-256) and in transit (TLS 1.3) for all personal data.
Article 28.2: Data Retention & Deletion - Upon termination of services, the processor shall delete or return all personal data within 30 calendar days, providing written proof of destruction.
Article 28.3: Breach Notification SLA - The processor shall notify the controller without undue delay and at the latest within 48 hours of becoming aware of a personal data breach.
Article 28.4: Sub-processor Approval - The processor shall not engage another processor without prior specific or general written authorisation of the controller.""",
        submitted_text="""HYPERSCALE CLOUD ENTERPRISE DPA

1. SECURITY MEASURES
All customer data stored within the platform is encrypted using AES-256 bit keys managed through AWS KMS. All web and API traffic is strictly routed over TLS 1.3.

2. DATA LIFECYCLE & RETENTION
Following account termination, customer data remains archived in cold storage for 180 days to allow disaster recovery before automated purge runs.

3. SECURITY INCIDENT REPORTING
In the event of a verified unauthorized access or security incident, the cloud provider will alert customer contacts within 14 business days.

4. SUBCONTRACTORS
The provider maintains a public roster of sub-processors. Customers receive notification 30 days before any new sub-processor is onboarded.""",
        expected_outcome_summary="Encryption: Compliant | Data Retention: Non-Compliant (180 days vs 30 days mandatory) | Breach Notification: Non-Compliant (14 days vs 48 hours SLA) | Sub-processor: Compliant. Overall: Non-Compliant."
    )
]

def get_sample_scenarios() -> List[SampleScenario]:
    return SAMPLE_SCENARIOS

def get_scenario_by_id(scenario_id: str) -> Optional[SampleScenario]:
    for s in SAMPLE_SCENARIOS:
        if s.id == scenario_id:
            return s
    return None
