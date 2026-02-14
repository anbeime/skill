# Business Flowchart Extraction (Mermaid)

Generate a Mermaid flowchart by extracting the full business transaction process from the contract.

**Language rule:** use the contract’s language for node text and labels. See **[language.md](language.md)**.

## Extraction Requirements

### 1. Process Completeness
- Cover the full lifecycle from contract signing to performance completion
- Include normal performance, breach handling, and termination
- Show interactions, rights, and obligations between both parties

### 2. Precision of Information
- **Time points**: extract explicit time requirements and triggers (e.g., X business days, X hours)
- **Amounts**: extract amounts and ratios (e.g., 30% prepayment, total amount)
- **Quantity/specs**: extract quantities, models, technical specs
- **Locations**: delivery/acceptance locations
- **Standards**: acceptance standards, quality requirements, technical specs
- **Strict source**: all extracted data must come from the contract text

### 3. Node Format
- Each node uses brackets `[]`
- Use `<br>` to break multiple items
- Edge labels show trigger/time requirement: `|condition|`; if missing, use `?`

### 4. Flow Logic
- Use `-->` for normal flow
- Include decision branches (e.g., acceptance pass/fail)
- Include parallel flows (e.g., risk transfer vs. title transfer)
- Show escalation of breach outcomes (minor → serious → termination)

### 5. Visual Styles
Add styles at the end:
- Normal performance nodes: `style [nodeId] fill:#e6e6fa`
- Breach-related nodes: `style [nodeId] fill:#ffff99`
- Termination nodes: `style [nodeId] fill:#ff6666`
- Normal completion nodes: `style [nodeId] fill:#90ee90`

## Output Format
- Output **only** Mermaid code, starting with `flowchart TD`
- No extra explanation or code fences
- Syntax must be valid and renderable
