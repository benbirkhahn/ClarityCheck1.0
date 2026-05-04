export interface DemoSample {
  id: string;
  title: string;
  category: string;
  attack: string;
  summary: string;
  filename: string;
}

export const demoSamples: DemoSample[] = [
  {
    id: 'onboarding-layered',
    title: 'Onboarding ID Packet',
    category: 'Onboarding / ID',
    attack: 'Layered text',
    summary: 'Reviewer-facing identity packet with a covert approval override hidden under a cover panel.',
    filename: 'onboarding-layered-text.pdf',
  },
  {
    id: 'loan-tiny',
    title: 'Loan Prequalification Worksheet',
    category: 'Loan / Finance',
    attack: 'Tiny text',
    summary: 'Normal underwriting worksheet with microscopic text slipped into the disclosure area.',
    filename: 'loan-tiny-text.pdf',
  },
  {
    id: 'claims-offscreen',
    title: 'Property Claim Intake',
    category: 'Claims / Insurance',
    attack: 'Off-screen text',
    summary: 'A routine property claim packet containing text placed outside the visible page.',
    filename: 'claims-offscreen-text.pdf',
  },
  {
    id: 'medical-transparent',
    title: 'Medical Intake Form',
    category: 'Medical Intake',
    attack: 'Transparent text',
    summary: 'Clinical intake paperwork with a hidden instruction rendered fully transparent.',
    filename: 'medical-transparent-text.pdf',
  },
  {
    id: 'hr-zero-width',
    title: 'Candidate Screening Packet',
    category: 'HR / Hiring',
    attack: 'Zero-width characters',
    summary: 'Hiring note with invisible Unicode markers embedded into an otherwise ordinary sentence.',
    filename: 'hr-zero-width-characters.pdf',
  },
  {
    id: 'legal-annotation',
    title: 'Legal NDA Review',
    category: 'Legal',
    attack: 'Hidden annotation',
    summary: 'Counterparty NDA review with a concealed comment intended for downstream readers.',
    filename: 'legal-hidden-annotation.pdf',
  },
  {
    id: 'compliance-metadata',
    title: 'Vendor Compliance Certificate',
    category: 'Compliance',
    attack: 'Metadata abuse',
    summary: 'Clean-looking compliance certificate with risky instructions buried in PDF metadata fields.',
    filename: 'compliance-metadata-abuse.pdf',
  },
  {
    id: 'compliance-spacing',
    title: 'Compliance Exception Memo',
    category: 'Compliance',
    attack: 'Suspicious spacing',
    summary: 'Operational memo using heavily spaced text to obfuscate the real payload.',
    filename: 'compliance-suspicious-spacing.pdf',
  },
  {
    id: 'finance-overlay',
    title: 'Portfolio Risk Summary',
    category: 'Finance',
    attack: 'Chart overlay',
    summary: 'Portfolio review where the real instruction is covered by a clean chart area.',
    filename: 'finance-chart-overlay.pdf',
  },
];
