# Contract Review Examples

## Quick Start

```python
# -*- coding: utf-8 -*-
from scripts.workflow import ContractReviewWorkflow

comments = [
    {
        "search": "Total Price",
        "comment": """[Issue Type] Payment Terms
[Risk Reason] The total amount is stated as USD 100,000 in Section 3.2, but the payment clause lists USD 1,000,000 in Section 5.1.
[Revision Suggestion] Align the total amount across clauses and clarify tax inclusion.""",
        "risk_level": "High",
    }
]

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(comments, "Contract_Reviewed.docx")
```

## Contract Summary (English)

```python
# -*- coding: utf-8 -*-
summary_text = """I. Basic Contract Information
Item\tContent
Contract Name\tNot specified
Contract Type\tNot specified
Parties\tParty A: Not specified
Party B: Not specified
Signing Date\tNot specified
Term\tNot specified
Contract Amount\tNot specified
II. Business Model Overview
Brief description: Not specified
III. Key Clause Elements
3.1 Transaction Elements
Element\tDetails
Subject Matter/Services\tNot specified
Quantity/Specs\tNot specified
Pricing Structure\tNot specified
Payment Terms\tNot specified
Delivery Terms\tNot specified
3.2 Rights and Obligations
Party A main rights/obligations:
Not specified
Party B main rights/obligations:
Not specified
3.3 Performance Safeguards
Clause Type\tDetails
Liability/Default\tNot specified
Guarantees/Security\tNot specified
Acceptance Standards\tNot specified
Quality Warranty\tNot specified
3.4 Risk Allocation & Special Terms
Risk Allocation:
Not specified
Special Terms:
Not specified
3.5 Dispute Resolution & Termination
Item\tDetails
Dispute Resolution\tNot specified
Amendment\tNot specified
Termination\tNot specified
Governing Law\tNot specified
IV. Key Timeline Milestones
Not specified
"""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_Reviewed.docx",
    summary_text=summary_text,
    summary_filename="Contract_Summary.docx",
    summary_font="Times New Roman",
)
```

## Consolidated Opinion (English)

```python
# -*- coding: utf-8 -*-
opinion_text = """This agreement is a goods sales contract under which our side purchases specific devices from the counterparty for a total amount of USD 100,000, payable as a 30% prepayment and 70% balance after acceptance, with delivery and acceptance milestones defined in the contract.

After review, the following key risks require attention: 1. Product model names are inconsistent across clauses, which may cause delivery disputes; 2. The prepayment amount does not match the stated percentage, potentially causing payment execution issues; 3. Delivery timing is stated as “reasonable time,” which is ambiguous and may lead to delay disputes."""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_reviewed.docx",
    opinion_text=opinion_text,
    opinion_filename="Consolidated_Opinion.docx",
    opinion_font="Times New Roman",
)
```

## Business Flowchart (Mermaid)

```python
# -*- coding: utf-8 -*-
flowchart_mermaid = """flowchart TD
    A[Contract Signed] -->|?| B[Performance]
"""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_reviewed.docx",
    flowchart_mermaid=flowchart_mermaid,
)
```

## Full Workflow Example

```python
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys
from pathlib import Path

skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

from scripts.workflow import ContractReviewWorkflow

contract_path = "path/to/contract.docx"
output_path = "contract_reviewed.docx"
report_path = "review_report.txt"
reviewer = "Reviewer"

comments = [
    {
        "search": "Total Price",
        "comment": """[Issue Type] Payment Terms
[Risk Reason] Amount mismatch between pricing and payment clauses.
[Revision Suggestion] Align total amount and clarify tax.""",
        "risk_level": "High"
    }
]

summary_text = """I. Basic Contract Information
Item\tContent
Contract Name\tNot specified
Contract Type\tNot specified
Parties\tParty A: Not specified
Party B: Not specified
Signing Date\tNot specified
Term\tNot specified
Contract Amount\tNot specified
"""

opinion_text = """This agreement is a services contract between our side and the counterparty with defined scope, pricing, and milestones.

After review, the following key risks require attention: 1. Payment timing is unclear; 2. Acceptance criteria are missing."""

flowchart_mermaid = """flowchart TD
    A[Contract Signed] -->|?| B[Performance]
"""

workflow = ContractReviewWorkflow(
    contract_path=contract_path,
    reviewer_name=reviewer,
    enable_smart_keyword_expansion=False,
)

workflow.run_full_workflow(
    comments=comments,
    output_docx_filename=output_path,
    report_filename=report_path,
    summary_text=summary_text,
    summary_filename="Contract_Summary.docx",
    summary_font="Times New Roman",
    opinion_text=opinion_text,
    opinion_filename="Consolidated_Opinion.docx",
    opinion_font="Times New Roman",
    flowchart_mermaid=flowchart_mermaid,
    render_flowchart=True,
    parallel_outputs=True,
)

print(f"✓ Added comments: {len(workflow.comments_added)}")
print(f"✗ Failed comments: {len(workflow.comments_failed)}")
```

## Language Notes

- Output must follow the contract’s language.
- For Chinese contracts, use the Chinese labels in **[language.md](language.md)** and set `summary_font` / `opinion_font` to Fangsong (仿宋).
