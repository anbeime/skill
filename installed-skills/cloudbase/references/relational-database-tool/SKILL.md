---
name: relational-database-mcp-cloudbase
description: This is the required documentation for agents operating on the CloudBase Relational Database through MCP. It defines the canonical SQL management flow with `querySqlDatabase`, `manageSqlDatabase`, `readSecurityRule`, and `writeSecurityRule`, including MySQL provisioning, destroy flow, async status checks, safe query execution, schema initialization, and security rule updates.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The agent must inspect SQL data, execute SQL statements, provision or destroy MySQL, initialize table structure, or manage table security rules through MCP tools.

### Read before writing code if

- The task includes `querySqlDatabase`, `manageSqlDatabase`, `readSecurityRule`, or `writeSecurityRule`.

### Then also read

- Web application integration -> `../relational-database-web/SKILL.md`
- Raw HTTP database access -> `../http-api/SKILL.md`

### Do NOT use for

- Frontend or backend application code that should use SDKs instead of MCP operations.

### Common mistakes / gotchas

- Initializing SDKs in an MCP management flow.
- Running write SQL or DDL before checking whether MySQL is provisioned and ready.
- Treating document database tasks as MySQL management tasks.
- Skipping `_openid` and security-rule review after creating new SQL tables.
- Destroying MySQL without explicit confirmation or without checking whether the environment still needs the instance.

## When to use this skill

Use this skill when an **agent** needs to operate on **CloudBase Relational Database via MCP tools**, for example:

- Inspecting or querying SQL data
- Provisioning MySQL for an environment
- Destroying MySQL for an environment
- Polling MySQL provisioning status
- Modifying data or schema (INSERT/UPDATE/DELETE/DDL)
- Initializing tables and indexes after MySQL is ready
- Reading or changing table security rules

Do **NOT** use this skill for:

- Building Web or Node.js applications that talk to CloudBase Relational Database directly through SDKs
- Auth flows or user identity management

## How to use this skill (for a coding agent)

1. **Recognize MCP context**
   - If you can call tools like `querySqlDatabase`, `manageSqlDatabase`, `readSecurityRule`, `writeSecurityRule`, you are in MCP context.
   - In this context, **never initialize SDKs for CloudBase Relational Database**; use MCP tools instead.

2. **Pick the right tool for the job**
   - Read-only SQL and provisioning status checks -> `querySqlDatabase`
   - MySQL provisioning, MySQL destruction, write SQL, DDL, schema initialization -> `manageSqlDatabase`
   - Inspect rules -> `readSecurityRule`
   - Change rules -> `writeSecurityRule`

3. **Always be explicit about safety**
   - Before destructive operations (DELETE, DROP, etc.), summarize what you are about to run and why.
   - Prefer `querySqlDatabase(action="getInstanceInfo")` or a read-only SQL check before writes.
   - Provisioning or destroying MySQL requires explicit confirmation because both actions have environment-level impact.

---

## Available MCP tools (CloudBase Relational Database)

These tools are the supported way to interact with CloudBase Relational Database via MCP:

### 1. `querySqlDatabase`

- **Purpose:** Query SQL data and provisioning state.
- **Use for:**
  - Running `SELECT` and other read-only SQL queries with `action="runQuery"`
  - Checking whether MySQL already exists with `action="getInstanceInfo"`
  - Inspecting asynchronous provisioning progress with `action="describeCreateResult"` or `action="describeTaskStatus"`

**Example flow:**

```json
{
  "action": "runQuery",
  "sql": "SELECT id, email FROM users ORDER BY created_at DESC LIMIT 50"
}
```

### 2. `manageSqlDatabase`

- **Purpose:** Manage SQL lifecycle and execute mutating SQL.
- **Use for:**
  - Provisioning MySQL with `action="provisionMySQL"`
  - Destroying MySQL with `action="destroyMySQL"`
  - Executing `INSERT`, `UPDATE`, `DELETE`, `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE` with `action="runStatement"`
  - Initializing tables and indexes with `action="initializeSchema"`

**Important:** When creating a new table, you **must** include the `_openid` column for per-user access control:

```sql
_openid VARCHAR(64) DEFAULT '' NOT NULL
```

Note: when a user is logged in, `_openid` is automatically populated by the server from the authenticated session. Do not manually fill it in normal inserts.

Before calling this tool, **confirm**:

- The current environment has a ready MySQL instance, or you have just provisioned one.
- The target tables and conditions are correct.
- You have run a corresponding read-only query when appropriate.

When destroying MySQL, confirm:

- The current environment really should lose the SQL instance.
- You have explicit confirmation for the destructive action.
- You are prepared to query `describeTaskStatus` afterward to inspect the destroy result.

### 3. `readSecurityRule`

- **Purpose:** Read security rules for a given SQL table.
- **Use for:**
  - Understanding who can read/write a table
  - Auditing permissions on sensitive tables

### 4. `writeSecurityRule`

- **Purpose:** Set or update security rules for a given SQL table.
- **Use for:**
  - Hardening access to sensitive data
  - Opening up read access while restricting writes
  - Applying custom rules when needed

---

## Recommended lifecycle flow

### Scenario 1: MySQL is not provisioned yet

1. Call `querySqlDatabase(action="getInstanceInfo")`.
2. If no instance exists, call `manageSqlDatabase(action="provisionMySQL", confirm=true)`.
3. Poll provisioning status with:
   - `querySqlDatabase(action="describeCreateResult")`
   - `querySqlDatabase(action="describeTaskStatus")`
4. Only continue when the returned lifecycle status is `READY`.
5. For MySQL provisioning, prefer `describeCreateResult`; reserve `describeTaskStatus` for destroy flows whose task response carries `TaskName`.

### Scenario 2: Safely inspect data in a table

1. Use `querySqlDatabase(action="runQuery")` with a limited `SELECT`.
2. Include `LIMIT` and relevant filters.
3. Review the result set and confirm it matches expectations before any write operation.

### Scenario 3: Apply schema initialization after provisioning

1. Confirm MySQL is ready.
2. Prepare ordered DDL statements.
3. Run them through `manageSqlDatabase(action="initializeSchema")`.
4. After creating tables, verify security rules with `readSecurityRule` or `writeSecurityRule`.

### Scenario 4: Execute a targeted write or DDL change

1. Use `querySqlDatabase(action="runQuery")` to inspect current data or schema if needed.
2. Run the mutation once with `manageSqlDatabase(action="runStatement")`.
3. Validate with another read-only query or by checking security rules.

### Scenario 5: Destroy MySQL when the environment no longer needs it

1. Use `querySqlDatabase(action="getInstanceInfo")` to confirm the current environment still has a SQL instance.
2. Call `manageSqlDatabase(action="destroyMySQL", confirm=true)`.
3. Query `querySqlDatabase(action="describeTaskStatus")` until the destroy task completes or fails.
4. If the task succeeds, optionally call `querySqlDatabase(action="getInstanceInfo")` to confirm the instance no longer exists.
5. If the task fails, treat the returned error as the terminal result and let the caller decide whether to retry.

---

## Key principle: MCP tools vs SDKs

- **MCP tools** are for **agent operations** and **database management**:
  - Provision MySQL.
  - Destroy MySQL.
  - Poll lifecycle state.
  - Run ad-hoc SQL.
  - Inspect and change security rules.
  - Do not depend on application auth state.

- **SDKs** are for **application code**:
  - Frontend Web apps -> Web Relational Database skill.
  - Backend Node apps -> Node Relational Database quickstart.

When working as an MCP agent, **always prefer these MCP tools** for CloudBase Relational Database, and avoid mixing them with SDK initialization in the same flow.
