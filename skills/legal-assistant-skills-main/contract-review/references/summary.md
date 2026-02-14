# Contract Summary Extraction

Objectively summarize the contract’s basic content to help legal teams understand the agreement quickly. **Do not provide risk assessments or legal advice.**

Default output is a DOCX rich-text file (`合同概要.docx` for Chinese, `Contract_Summary.docx` for English). Font defaults to Fangsong; adjust `summary_font` for non‑Chinese languages.

**Language rule:** output in the contract’s language. See **[language.md](language.md)** for selection rules and label mappings.

## Output Format

I. Basic Contract Information  
Item	Content  
Contract Name	[Extract title or designated name]  
Contract Type	[e.g., Sales, Services, Lease]  
Parties	Party A: [Name, Address]  
Party B: [Name, Address]  
Signing Date	[Signature date]  
Term	[Start/end date or performance period]  
Contract Amount	[Total amount & currency; include installment schedule if any]  

II. Business Model Overview  
Brief description: [1–2 paragraphs summarizing the core transaction and relationship]  

III. Key Clause Elements  
3.1 Transaction Elements  
Element	Details  
Subject Matter/Services	[Goods, services, or deliverables]  
Quantity/Specs	[Quantity, model, technical specs]  
Pricing Structure	[Unit price, total price, adjustment mechanism]  
Payment Terms	[Payment ratio, milestones, method]  
Delivery Terms	[Location, time, acceptance standards]  

3.2 Rights and Obligations  
Party A main rights/obligations:

[Main rights]  
[Main obligations]  

Party B main rights/obligations:

[Main rights]  
[Main obligations]  

3.3 Performance Safeguards  
Clause Type	Details  
Liability/Default	[Consequences for each party]  
Guarantees/Security	[Deposit, guarantee, etc.]  
Acceptance Standards	[Procedure, criteria, dispute handling]  
Quality Warranty	[Warranty period, responsibilities, after-sales]  

3.4 Risk Allocation & Special Terms  
Risk Allocation:

[Force majeure clause]  
[Risk transfer trigger]  
[Loss allocation]  

Special Terms:

[Intellectual property]  
[Confidentiality]  
[Exclusivity]  
[Other special conditions or restrictions]  

3.5 Dispute Resolution & Termination  
Item	Details  
Dispute Resolution	[Negotiation, mediation, arbitration, litigation & jurisdiction]  
Amendment	[Conditions and procedure]  
Termination	[Triggers, procedure, consequences]  
Governing Law	[Applicable laws/regulations]  

IV. Key Timeline Milestones  
[List key milestones in chronological order: signing, payment, delivery, acceptance, etc.]  

## Output Requirements

- **Objectivity**: only extract and describe clauses; no subjective judgments
- **Completeness**: if a clause is missing, write “Not specified”
- **Accuracy**: faithfully reflect the contract text; quote critical wording when needed
- **Conciseness**: 500–800 words (simple), 800–1200 (standard), 1200–1500 (complex)
- **Structure**: strictly follow the above format for quick navigation
