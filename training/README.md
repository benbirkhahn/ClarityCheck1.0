# Training Data for ClarityCheck

## Purpose
This directory contains example PDFs and their labels to train better detection rules.

## Directory Structure
```
training/
├── examples/           # Put your example PDFs here
│   ├── homework1.pdf
│   ├── homework2.pdf
│   └── ...
├── labels/            # I'll generate detection reports here
│   ├── homework1_findings.json
│   └── ...
└── labeled_data.md    # Your labels go here
```

## How to Use

### Step 1: Upload Example PDFs
Place 3-5 PDFs in `training/examples/` that contain:
- Real AI traps you want removed
- False positives (legitimate text wrongly flagged)
- A mix of both scenarios

### Step 2: I'll Analyze Them
I'll run detection on each PDF and generate findings

### Step 3: You Label the Findings
Edit `labeled_data.md` and mark each finding:
```markdown
## homework1.pdf - Finding #1
**Text:** "Ignore all previous instructions"
**Detector:** MatchingColorDetector
**Location:** Page 2, off-screen (x: -50, y: 100)
**Your Decision:** REMOVE
**Reason:** Hidden AI command, should be removed

## homework1.pdf - Finding #2
**Text:** "Set up and run a statistical test"
**Detector:** TinyTextDetector
**Location:** Page 1, visible (x: 100, y: 200)
**Your Decision:** KEEP
**Reason:** Legitimate homework instruction, part of the question
```

### Step 4: I Extract Patterns
Based on your labels, I'll identify patterns and create custom rules.

## Quick Start

Just drop PDFs into `training/examples/` and I'll handle the rest!
