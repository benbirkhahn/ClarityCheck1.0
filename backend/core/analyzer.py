"""
AI Trap Analyzer - Intelligent classification of hidden content.

Takes raw findings and classifies them into actionable categories,
reconstructs obfuscated text, and provides clear explanations.
"""

import re
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from backend.core.models import Finding, Report, Severity


class TrapType(str, Enum):
    """Classification of hidden content type."""
    INSTRUCTION = "instruction"      # Changes AI behavior/output
    CANARY = "canary"                # Marker text to prove AI read document
    WATERMARK = "watermark"          # Unique identifiers for tracking
    OBFUSCATION = "obfuscation"      # Makes content harder to parse
    METADATA_LEAK = "metadata_leak"  # Exposes unintended information
    UNKNOWN = "unknown"


class TrapImpact(str, Enum):
    """Impact level on AI behavior."""
    CRITICAL = "critical"    # Will definitely change AI output
    HIGH = "high"            # Likely to affect AI behavior
    MEDIUM = "medium"        # May affect AI in some cases
    LOW = "low"              # Unlikely to change AI behavior
    INFO = "info"            # Informational only


class AnalyzedFinding(BaseModel):
    """Enhanced finding with classification and analysis."""
    original: Finding
    trap_type: TrapType
    impact: TrapImpact
    decoded_text: str              # Reconstructed/cleaned text
    classification_reason: str     # Why we classified it this way
    recommended_action: str        # What user should do


class TrapAnalysis(BaseModel):
    """Complete analysis of a document's AI traps."""
    filename: str
    total_pages: int
    risk_score: int                          # 0-100
    risk_level: str                          # Low/Medium/High/Critical
    findings: list[AnalyzedFinding]
    summary: dict                            # Counts by trap type
    executive_summary: str                   # Human-readable summary
    

# Keywords that suggest instructional content
INSTRUCTION_KEYWORDS = [
    # Programming instructions
    r'\b(function|variable|code|implement|use|call|return|parameter|argument)\b',
    r'\b(list|array|dict|string|int|float|loop|for|while|if|else)\b',
    r'\b(class|method|import|print|input|output|file|read|write)\b',
    r'\b(should|must|ensure|require|need|make sure|don\'t|do not)\b',
    r'\b(name|named|called|create|define|declare|initialize)\b',
    # Assignment instructions
    r'\b(submit|assignment|homework|lab|exercise|problem|solution)\b',
    r'\b(answer|response|write|explain|describe|show|demonstrate)\b',
]

# Patterns that suggest canary/marker text
CANARY_PATTERNS = [
    # Nonsense or out-of-context content
    r'\b(yesterday|tomorrow|park|flower|ice cream|beautiful|incredible)\b',
    r'\b(weather|sunny|rain|happy|sad|friend|family|vacation)\b',
    # Random phrases
    r'(went to the|did you see|what a sight|so much fun)',
    # Unique identifiers
    r'[A-Z]{3,}-\d{4,}',  # Code-like markers
    r'\b[a-f0-9]{8,}\b',   # Hex strings
]

# Patterns suggesting watermarks/tracking (more specific)
WATERMARK_PATTERNS = [
    r'student.?id',
    r'submission.?id', 
    r'unique.?identifier',
    r'tracking.?code',
    r'\b[A-F0-9]{12,}\b',  # Long hex codes (more specific)
]


class AITrapAnalyzer:
    """Analyzes and classifies hidden content in documents."""
    
    def __init__(self):
        self.instruction_patterns = [re.compile(p, re.IGNORECASE) for p in INSTRUCTION_KEYWORDS]
        self.canary_patterns = [re.compile(p, re.IGNORECASE) for p in CANARY_PATTERNS]
        self.watermark_patterns = [re.compile(p, re.IGNORECASE) for p in WATERMARK_PATTERNS]
    
    def analyze(self, report: Report) -> TrapAnalysis:
        """Perform complete analysis of a document report."""
        analyzed_findings = []
        
        for finding in report.findings:
            analyzed = self._analyze_finding(finding)
            analyzed_findings.append(analyzed)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(analyzed_findings)
        risk_level = self._risk_level(risk_score)
        
        # Build summary counts
        summary = {}
        for af in analyzed_findings:
            key = af.trap_type.value
            summary[key] = summary.get(key, 0) + 1
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            report.filename, analyzed_findings, risk_score, risk_level
        )
        
        return TrapAnalysis(
            filename=report.filename,
            total_pages=report.total_pages,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=analyzed_findings,
            summary=summary,
            executive_summary=exec_summary,
        )
    
    def _analyze_finding(self, finding: Finding) -> AnalyzedFinding:
        """Classify and analyze a single finding."""
        # First, decode/reconstruct the text
        decoded = self._decode_text(finding.context)
        
        # Classify the trap type
        trap_type, reason = self._classify_trap(finding, decoded)
        
        # Determine impact
        impact = self._determine_impact(finding, trap_type, decoded)
        
        # Generate recommendation
        action = self._recommend_action(trap_type, impact)
        
        return AnalyzedFinding(
            original=finding,
            trap_type=trap_type,
            impact=impact,
            decoded_text=decoded,
            classification_reason=reason,
            recommended_action=action,
        )
    
    def _decode_text(self, text: str) -> str:
        """Reconstruct obfuscated text."""
        decoded = text
        
        # Remove character-by-character spacing (T h i s -> This)
        # Pattern: single char followed by space, repeated
        if re.search(r'^(\S\s){3,}', decoded):
            # Check if it's actually spaced-out text
            chars = decoded.replace(" ", "")
            if len(chars) > 3:
                # Verify by checking space ratio
                space_ratio = decoded.count(" ") / len(decoded) if decoded else 0
                if space_ratio > 0.3:
                    decoded = chars
        
        # Normalize multiple spaces
        decoded = re.sub(r'\s{2,}', ' ', decoded)
        
        # Clean up common artifacts
        decoded = decoded.strip()
        
        # If it ends with "..." remove and note truncation
        if decoded.endswith("..."):
            decoded = decoded[:-3].strip() + " [truncated]"
        
        return decoded
    
    def _classify_trap(self, finding: Finding, decoded: str) -> tuple[TrapType, str]:
        """Classify the type of trap based on content analysis."""
        detector = finding.detector
        text_lower = decoded.lower()
        
        # Check for instruction patterns
        instruction_matches = []
        for pattern in self.instruction_patterns:
            if pattern.search(text_lower):
                instruction_matches.append(pattern.pattern)
        
        # Check for canary patterns
        canary_matches = []
        for pattern in self.canary_patterns:
            if pattern.search(text_lower):
                canary_matches.append(pattern.pattern)
        
        # Check for watermark patterns
        watermark_matches = []
        for pattern in self.watermark_patterns:
            if pattern.search(text_lower):
                watermark_matches.append(pattern.pattern)
        
        # Decision logic - order matters!
        # 1. Check for instructions first (highest priority)
        if instruction_matches and len(instruction_matches) >= 2:
            return TrapType.INSTRUCTION, f"Contains programming/task keywords: {', '.join(instruction_matches[:3])}"
        
        # 2. Check for canary text (out-of-context markers)
        if canary_matches and len(canary_matches) >= 2:
            return TrapType.CANARY, f"Contains out-of-context marker text: {', '.join([p.split('(')[1].split(')')[0] if '(' in p else p[:20] for p in canary_matches[:2]])}"
        
        # 3. If both present, decide by count
        if instruction_matches and canary_matches:
            if len(instruction_matches) >= len(canary_matches):
                return TrapType.INSTRUCTION, f"Contains task keywords mixed with decoy text"
            else:
                return TrapType.CANARY, f"Marker/decoy text with some task words"
        
        # 4. Single matches
        if instruction_matches:
            return TrapType.INSTRUCTION, f"Contains task keyword: {instruction_matches[0][:30]}"
        
        if canary_matches:
            return TrapType.CANARY, f"Contains marker text"
        
        # 5. Watermarks only if nothing else matches
        if watermark_matches:
            return TrapType.WATERMARK, f"Contains tracking identifiers"
        
        # Check detector type for hints
        if detector in ["ZeroWidthCharDetector"]:
            return TrapType.OBFUSCATION, "Zero-width characters disrupt text processing"
        
        if detector in ["MetadataDetector"]:
            return TrapType.METADATA_LEAK, "Document metadata may expose information"
        
        if detector in ["SuspiciousSpacingDetector"]:
            return TrapType.OBFUSCATION, "Text spacing obfuscates content"
        
        # Default based on detector severity
        if finding.severity == Severity.HIGH:
            return TrapType.INSTRUCTION, "High severity hidden content (assumed instructional)"
        
        return TrapType.UNKNOWN, "Unable to classify - review manually"
    
    def _determine_impact(self, finding: Finding, trap_type: TrapType, decoded: str) -> TrapImpact:
        """Determine the impact level on AI behavior."""
        # Instructions have highest impact
        if trap_type == TrapType.INSTRUCTION:
            # Check for specific directives
            if any(word in decoded.lower() for word in ["must", "should", "require", "ensure"]):
                return TrapImpact.CRITICAL
            return TrapImpact.HIGH
        
        # Canaries can expose AI usage
        if trap_type == TrapType.CANARY:
            return TrapImpact.HIGH  # Can still prove AI usage if output
        
        # Watermarks track submissions
        if trap_type == TrapType.WATERMARK:
            return TrapImpact.MEDIUM
        
        # Obfuscation disrupts processing
        if trap_type == TrapType.OBFUSCATION:
            return TrapImpact.MEDIUM
        
        # Metadata leaks are informational
        if trap_type == TrapType.METADATA_LEAK:
            return TrapImpact.LOW
        
        return TrapImpact.INFO
    
    def _recommend_action(self, trap_type: TrapType, impact: TrapImpact) -> str:
        """Generate actionable recommendation."""
        recommendations = {
            TrapType.INSTRUCTION: "⚠️ CRITICAL: This hidden instruction would change AI output. AI using this document will follow these hidden directives.",
            TrapType.CANARY: "⚠️ WARNING: This marker text would appear in AI output, proving the document was processed by AI.",
            TrapType.WATERMARK: "📋 NOTE: This identifier could track the document's usage or submission source.",
            TrapType.OBFUSCATION: "🔍 INFO: This obfuscation technique may cause AI parsing issues or inconsistent behavior.",
            TrapType.METADATA_LEAK: "ℹ️ INFO: Review metadata for unintended information disclosure.",
            TrapType.UNKNOWN: "❓ REVIEW: Manual inspection recommended to determine intent.",
        }
        return recommendations.get(trap_type, "Review this finding manually.")
    
    def _calculate_risk_score(self, findings: list[AnalyzedFinding]) -> int:
        """Calculate overall risk score (0-100)."""
        if not findings:
            return 0
        
        score = 0
        weights = {
            TrapImpact.CRITICAL: 25,
            TrapImpact.HIGH: 15,
            TrapImpact.MEDIUM: 8,
            TrapImpact.LOW: 3,
            TrapImpact.INFO: 1,
        }
        
        for f in findings:
            score += weights.get(f.impact, 1)
        
        # Cap at 100
        return min(100, score)
    
    def _risk_level(self, score: int) -> str:
        """Convert score to risk level."""
        if score >= 75:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        elif score > 0:
            return "LOW"
        return "CLEAN"
    
    def _generate_executive_summary(
        self, 
        filename: str, 
        findings: list[AnalyzedFinding], 
        risk_score: int,
        risk_level: str
    ) -> str:
        """Generate human-readable executive summary."""
        if not findings:
            return f"✅ {filename} appears clean. No hidden AI traps detected."
        
        # Count by type
        instructions = sum(1 for f in findings if f.trap_type == TrapType.INSTRUCTION)
        canaries = sum(1 for f in findings if f.trap_type == TrapType.CANARY)
        other = len(findings) - instructions - canaries
        
        summary_parts = [f"🔍 **{filename}** - Risk Level: **{risk_level}** ({risk_score}/100)"]
        summary_parts.append("")
        
        if instructions:
            summary_parts.append(f"⚠️ **{instructions} Hidden Instruction(s)**: These would change how AI responds to this document.")
        
        if canaries:
            summary_parts.append(f"🐦 **{canaries} Canary/Marker Text(s)**: These would expose AI usage if included in output.")
        
        if other:
            summary_parts.append(f"📋 **{other} Other Finding(s)**: Obfuscation, metadata, or unclassified content.")
        
        summary_parts.append("")
        summary_parts.append("**Recommendation**: Review all findings before processing this document with AI tools.")
        
        return "\n".join(summary_parts)


# Singleton instance
analyzer = AITrapAnalyzer()
