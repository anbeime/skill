---
name: product-manager-toolkit
description: Comprehensive toolkit for product managers including RICE prioritization, customer interview analysis, PRD templates, discovery frameworks, and go-to-market strategies. Use for feature prioritization, user research synthesis, requirement documentation, and product strategy development.
---

# Product Manager Toolkit

Essential tools and frameworks for modern product management, from discovery to delivery.

## Quick Start

### For Feature Prioritization
```bash
python scripts/rice_prioritizer.py sample  # Create sample CSV
python scripts/rice_prioritizer.py sample_features.csv --capacity 15
```

### For Interview Analysis
```bash
python scripts/customer_interview_analyzer.py interview_transcript.txt
```

### For PRD Creation
1. Choose template from `references/prd_templates.md`
2. Fill in sections based on discovery work
3. Review with stakeholders
4. Version control in your PM tool

## Core Workflows

### Feature Prioritization Process

1. **Gather Feature Requests**
   - Customer feedback
   - Sales requests
   - Technical debt
   - Strategic initiatives

2. **Score with RICE**
   ```bash
   # Create CSV with: name,reach,impact,confidence,effort
   python scripts/rice_prioritizer.py features.csv
   ```
   - **Reach**: Users affected per quarter
   - **Impact**: massive/high/medium/low/minimal
   - **Confidence**: high/medium/low
   - **Effort**: xl/l/m/s/xs (person-months)

3. **Analyze Portfolio**
   - Review quick wins vs big bets
   - Check effort distribution
   - Validate against strategy

4. **Generate Roadmap**
   - Quarterly capacity planning
   - Dependency mapping
   - Stakeholder alignment

### Customer Discovery Process

1. **Conduct Interviews**
   - Use semi-structured format
   - Focus on problems, not solutions
   - Record with permission

2. **Analyze Insights**
   ```bash
   python scripts/customer_interview_analyzer.py transcript.txt
   ```
   Extracts:
   - Pain points with severity
   - Feature requests with priority
   - Jobs to be done
   - Sentiment analysis
   - Key themes and quotes

3. **Synthesize Findings**
   - Group similar pain points
   - Identify patterns across interviews
   - Map to opportunity areas

4. **Validate Solutions**
   - Create solution hypotheses
   - Test with prototypes
   - Measure actual vs expected behavior

### PRD Development Process

1. **Choose Template**
   - **Standard PRD**: Complex features (6-8 weeks)
   - **One-Page PRD**: Simple features (2-4 weeks)
   - **Feature Brief**: Exploration phase (1 week)
   - **Agile Epic**: Sprint-based delivery

2. **Structure Content**
   - Problem → Solution → Success Metrics
   - Always include out-of-scope
   - Clear acceptance criteria

3. **Collaborate**
   - Engineering for feasibility
   - Design for experience
   - Sales for market validation
   - Support for operational impact

## Key Scripts

### rice_prioritizer.py
Advanced RICE framework implementation with portfolio analysis.

**Features**:
- RICE score calculation
- Portfolio balance analysis (quick wins vs big bets)
- Quarterly roadmap generation
- Team capacity planning
- Multiple output formats (text/json/csv)

**Usage Examples**:
```bash
# Basic prioritization
python scripts/rice_prioritizer.py features.csv

# With custom team capacity (person-months per quarter)
python scripts/rice_prioritizer.py features.csv --capacity 20

# Output as JSON for integration
python scripts/rice_prioritizer.py features.csv --output json
```

### customer_interview_analyzer.py
NLP-based interview analysis for extracting actionable insights.

**Capabilities**:
- Pain point extraction with severity assessment
- Feature request identification and classification
- Jobs-to-be-done pattern recognition
- Sentiment analysis
- Theme extraction
- Competitor mentions
- Key quotes identification

**Usage Examples**:
```bash
# Analyze single interview
python scripts/customer_interview_analyzer.py interview.txt

# Output as JSON for aggregation
python scripts/customer_interview_analyzer.py interview.txt json
```

## Reference Documents

### prd_templates.md
Multiple PRD formats for different contexts:

1. **Standard PRD Template**
   - Comprehensive 11-section format
   - Best for major features
   - Includes technical specs

2. **One-Page PRD**
   - Concise format for quick alignment
   - Focus on problem/solution/metrics
   - Good for smaller features

3. **Agile Epic Template**
   - Sprint-based delivery
   - User story mapping
   - Acceptance criteria focus

4. **Feature Brief**
   - Lightweight exploration
   - Hypothesis-driven
   - Pre-PRD phase

## Prioritization Frameworks

### RICE Framework
```
Score = (Reach × Impact × Confidence) / Effort

Reach: # of users/quarter
Impact: 
  - Massive = 3x
  - High = 2x
  - Medium = 1x
  - Low = 0.5x
  - Minimal = 0.25x
Confidence:
  - High = 100%
  - Medium = 80%
  - Low = 50%
Effort: Person-months
```

### Value vs Effort Matrix
```
         Low Effort    High Effort
         
High     QUICK WINS    BIG BETS
Value    [Prioritize]   [Strategic]
         
Low      FILL-INS      TIME SINKS
Value    [Maybe]       [Avoid]
```

### MoSCoW Method
- **Must Have**: Critical for launch
- **Should Have**: Important but not critical
- **Could Have**: Nice to have
- **Won't Have**: Out of scope

## Discovery Frameworks

### Customer Interview Guide
```
1. Context Questions (5 min)
   - Role and responsibilities
   - Current workflow
   - Tools used

2. Problem Exploration (15 min)
   - Pain points
   - Frequency and impact
   - Current workarounds

3. Solution Validation (10 min)
   - Reaction to concepts
   - Value perception
   - Willingness to pay

4. Wrap-up (5 min)
   - Other thoughts
   - Referrals
   - Follow-up permission
```

### Hypothesis Template
```
We believe that [building this feature]
For [these users]
Will [achieve this outcome]
We'll know we're right when [metric]
```

### Opportunity Solution Tree
```
Outcome
├── Opportunity 1
│   ├── Solution A
│   └── Solution B
└── Opportunity 2
    ├── Solution C
    └── Solution D
```

## Metrics & Analytics

### North Star Metric Framework
1. **Identify Core Value**: What's the #1 value to users?
2. **Make it Measurable**: Quantifiable and trackable
3. **Ensure It's Actionable**: Teams can influence it
4. **Check Leading Indicator**: Predicts business success

### Funnel Analysis Template
```
Acquisition → Activation → Retention → Revenue → Referral

Key Metrics:
- Conversion rate at each step
- Drop-off points
- Time between steps
- Cohort variations
```

### Feature Success Metrics
- **Adoption**: % of users using feature
- **Frequency**: Usage per user per time period
- **Depth**: % of feature capability used
- **Retention**: Continued usage over time
- **Satisfaction**: NPS/CSAT for feature

## Best Practices

### Writing Great PRDs
1. Start with the problem, not solution
2. Include clear success metrics upfront
3. Explicitly state what's out of scope
4. Use visuals (wireframes, flows)
5. Keep technical details in appendix
6. Version control changes

### Effective Prioritization
1. Mix quick wins with strategic bets
2. Consider opportunity cost
3. Account for dependencies
4. Buffer for unexpected work (20%)
5. Revisit quarterly
6. Communicate decisions clearly

### Customer Discovery Tips
1. Ask "why" 5 times
2. Focus on past behavior, not future intentions
3. Avoid leading questions
4. Interview in their environment
5. Look for emotional reactions
6. Validate with data

### Stakeholder Management
1. Identify RACI for decisions
2. Regular async updates
3. Demo over documentation
4. Address concerns early
5. Celebrate wins publicly
6. Learn from failures openly

## Common Pitfalls to Avoid

1. **Solution-First Thinking**: Jumping to features before understanding problems
2. **Analysis Paralysis**: Over-researching without shipping
3. **Feature Factory**: Shipping features without measuring impact
4. **Ignoring Technical Debt**: Not allocating time for platform health
5. **Stakeholder Surprise**: Not communicating early and often
6. **Metric Theater**: Optimizing vanity metrics over real value

## Integration Points

This toolkit integrates with:
- **Analytics**: Amplitude, Mixpanel, Google Analytics
- **Roadmapping**: ProductBoard, Aha!, Roadmunk
- **Design**: Figma, Sketch, Miro
- **Development**: Jira, Linear, GitHub
- **Research**: Dovetail, UserVoice, Pendo
- **Communication**: Slack, Notion, Confluence

## Quick Commands Cheat Sheet

```bash
# Prioritization
python scripts/rice_prioritizer.py features.csv --capacity 15

# Interview Analysis
python scripts/customer_interview_analyzer.py interview.txt

# Create sample data
python scripts/rice_prioritizer.py sample

# JSON outputs for integration
python scripts/rice_prioritizer.py features.csv --output json
python scripts/customer_interview_analyzer.py interview.txt json
```

---

## 与智能体协作框架集成

本工具包可以与智能体协作框架无缝集成，实现产品团队的智能化协作。

### 集成场景

#### 场景1: 功能优先级评审会议
将RICE排序工具与多智能体会议决策结合：

```bash
# 1. 使用RICE脚本生成初步排序
python scripts/rice_prioritizer.py features.csv --capacity 15

# 2. 调用智能体团队进行会议讨论
"请用产品团队评审以下功能的优先级：[功能列表]"

# 3. 输出包含RICE分数和会议共识的完整决策
```

**参与智能体**:
- 产品经理（主持，使用RICE方法）
- 技术架构师（评估实现难度）
- 市场分析师（评估市场价值）
- 财务顾问（评估ROI）

**相关技能**:
- `agent-team`: 智能体协作框架
- `multi-agent-meeting`: 会议决策流程

**会议模板**: `multi-agent-meeting/assets/meeting-templates/product-feature-review.md`

---

#### 场景2: 客户洞察分析会议
将访谈分析工具与智能体团队结合：

```bash
# 1. 使用分析脚本提取洞察
python scripts/customer_interview_analyzer.py interview.txt

# 2. 调用智能体团队讨论改进方案
"分析这份访谈记录并生成产品改进方案：[访谈文本]"

# 3. 输出包含洞察、方案和PRD草稿的完整报告
```

**参与智能体**:
- 产品经理（方案制定）
- 用户研究员（洞察提取）
- 设计师（体验改进）
- 技术架构师（可行性评估）

**相关技能**:
- `agent-team`: 智能体协作框架
- `multi-agent-meeting`: 会议决策流程

**会议模板**: `multi-agent-meeting/assets/meeting-templates/customer-insight-analysis.md`

---

#### 场景3: 产品路线图规划会议
结合战略分析和RICE排序：

```bash
# 1. 战略分析智能体识别市场机会
"扫描AI内容生成领域的市场机会"

# 2. 使用RICE方法对机会进行排序
python scripts/rice_prioritizer.py opportunities.csv --capacity 15

# 3. 召开路线图规划会议
"制定Q2产品路线图，团队容量15人月"

# 4. 输出季度路线图和资源分配计划
```

**参与智能体**:
- 产品经理（路线图规划）
- 战略分析智能体（市场机会识别）
- 技术架构师（技术可行性）
- 项目经理（资源和时间评估）

**相关技能**:
- `agent-team`: 智能体协作框架（场景9：产品路线图规划会议）

---

### 产品经理智能体定义

当在智能体协作框架中使用"产品经理智能体"时，该智能体具备以下能力：

**专业知识**:
- RICE优先级排序方法
- 客户访谈分析技巧
- PRD文档编写规范
- 产品路线图规划
- 北极星指标定义

**工具调用**:
```python
# 优先级排序
self.call_tool("rice_prioritizer", features_csv, capacity=15)

# 访谈分析
self.call_tool("customer_interview_analyzer", interview_text)

# PRD生成
self.use_template("prd_templates", template_type="standard")
```

**协作接口**:
- **输入**: 功能列表、用户反馈、市场分析
- **输出**: 优先级排序、PRD文档、产品路线图

**适用场景**:
- 功能评审会议
- 客户洞察分析
- 产品路线图规划
- 需求文档编写

**智能体定义**: 参考 `agent-team/references/agent-registry.md` 中的"产品经理智能体（增强版）"

---

### 用户研究员智能体定义

**专业知识**:
- 客户访谈分析
- 痛点识别和严重程度评估
- 用户画像构建
- Jobs-to-be-Done 分析
- 情感分析和主题提取

**工具调用**:
```python
# 访谈分析
self.call_tool("customer_interview_analyzer", interview_text, output_format="json")

# 提取关键洞察
insights = self.extract_insights(analysis_result)
```

**协作接口**:
- **输入**: 访谈记录、用户反馈、行为数据
- **输出**: 洞察报告、痛点列表、用户画像

**适用场景**:
- 客户访谈分析
- 用户需求挖掘
- 产品改进方向识别

**智能体定义**: 参考 `agent-team/references/agent-registry.md` 中的"用户研究员智能体"

---

### 完整协作示例

**用户输入**:
```
我有以下功能需要评审优先级：
1. AI自动生成脚本
2. 多平台发布
3. 数据分析看板
4. 用户协作功能
5. API开放平台

请帮我评审并生成优先级排序，团队容量15人月。
```

**系统执行流程**:

1. **识别场景**: 产品功能优先级评审（agent-team 场景7）

2. **组建团队**: 
   - 产品经理（主持）
   - 技术架构师
   - 市场分析师
   - 财务顾问

3. **数据准备**:
   ```bash
   # 产品经理智能体调用RICE脚本
   python scripts/rice_prioritizer.py features.csv --capacity 15
   ```

4. **会议讨论** (使用 multi-agent-meeting 流程):
   ```
   > 产品经理: 根据RICE排序，AI自动生成脚本得分最高(85分)...
   > 技术架构师: 从技术角度，这个功能可行，可以使用现有大模型...
   > 市场分析师: 市场调研显示，用户对AI功能的需求强烈...
   > 财务顾问: 预计3个月可以回本，ROI较高...
   ```

5. **决策输出**:
   ```markdown
   # 功能优先级排序结果
   
   ## 最终排序
   1. AI自动生成脚本 (RICE: 85) - P0
   2. 多平台发布 (RICE: 72) - P1
   3. API开放平台 (RICE: 58) - P2
   
   ## Q2开发计划
   - AI自动生成脚本: 3人月
   - 多平台发布: 2人月
   - 预留缓冲: 1人月
   ```

---

### 相关资源

**智能体协作框架**:
- 技能名称: `agent-team`
- 智能体注册表: `agent-team/references/agent-registry.md`
- 协作模板: `agent-team/references/collaboration-templates.md`

**会议决策流程**:
- 技能名称: `multi-agent-meeting`
- 会议模板: `multi-agent-meeting/assets/meeting-templates/`
- 会议记录格式: `multi-agent-meeting/references/meeting-record-format.md`

**产品场景模板**:
- 场景7: 产品功能优先级评审会议
- 场景8: 客户访谈洞察分析会议
- 场景9: 产品路线图规划会议
- 场景10: 产品定价策略会议

---

### 集成优势

**整合前**:
- 工具独立使用，需要手动组合
- 缺少多角度专业分析
- 决策过程不透明

**整合后**:
- ✅ 一键启动完整协作流程
- ✅ 多智能体专业分析
- ✅ 实时展示讨论过程
- ✅ 标准化决策输出
- ✅ 工具自动调用

**用户价值**:
- 节省时间: 从手动组合到一键启动
- 提升质量: 多角度专业分析
- 降低门槛: 预设模板和流程
- 完整闭环: 从数据分析到决策输出
