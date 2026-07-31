---
name: relational-database-web-cloudbase
description: Use when building frontend Web apps that talk to CloudBase Relational Database via @cloudbase/js-sdk – provides the canonical init pattern so you can then use Supabase-style queries from the browser.
alwaysApply: false
---

## When to use this skill

Use this skill whenever you need to access **CloudBase Relational Database from a browser app** (React, Vue, vanilla JS) using `@cloudbase/js-sdk`.

Use it when you need to:

- Initialize CloudBase Relational Database on the frontend
- Replace an existing Supabase client with CloudBase Relational Database
- Share a single `db` client across your Web app

**Do NOT use this skill for:**

- Backend/Node access to CloudBase Relational Database (use `relation-database-skill` → `node-sdk/quickstart.md`)
- MCP/agent database management (use `relation-database-skill` → `mcp-tools/mcp-guide.md`)
- Auth flows (use the Web/Node/Auth skills instead)

## How to use this skill (for a coding agent)

1. **Confirm environment**
   - Ask the user for:
     - `env` – CloudBase environment ID
2. **Follow the initialization pattern in this file exactly**
   - Only change values like `env`, never the object shape.
3. **After initialization, use Supabase knowledge for queries**
   - Treat `db` as a Supabase client – method names and patterns are identical.
4. **Avoid re-initializing CloudBase**
   - Create a single shared `db` client and reuse it across components.

---

## Installation

```bash
npm install @cloudbase/js-sdk
```

## Initialization pattern (canonical)

```javascript
import cloudbase from "@cloudbase/js-sdk";

const app = cloudbase.init({
  env: "your-env-id", // CloudBase environment ID
});

const auth = app.auth();
// Handle user authentication separately (Web Auth skill)

const db = app.rdb();
// Use db exactly like a Supabase client
```

**Initialization rules (Web, @cloudbase/js-sdk):**

- Always use **synchronous initialization** with the pattern above
- Do **not** lazy-load the SDK with `import("@cloudbase/js-sdk")`
- Do **not** wrap SDK initialization in async helpers such as `initCloudBase()` with internal `initPromise` caches
- Create a single shared `db` client and reuse it instead of re-initializing

**Rules:**

- Do **not** invent new properties on the `cloudbase.init` options.
- Always call `app.rdb()` to get the database client; `app` is **not** the DB client.

---

## Scenario 1: Replace Supabase client in a React app

```javascript
// lib/db.js (shared database client)
import cloudbase from "@cloudbase/js-sdk";

const app = cloudbase.init({
  env: "your-env-id",
});

export const db = app.rdb();
```

```javascript
// hooks/usePosts.js
import { useEffect, useState } from "react";
import { db } from "../lib/db";

export function usePosts() {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    async function fetchPosts() {
      const { data } = await db.from("posts").select("*");
      setPosts(data || []);
    }
    fetchPosts();
  }, []);

  return { posts };
}
```

---

## Scenario 2: Basic query pattern (Supabase-style)

```javascript
// Fetch latest posts
const { data, error } = await db
  .from("posts")
  .select("*")
  .order("created_at", { ascending: false });

if (error) {
  console.error("Failed to load posts", error.message);
}
```

---

## Scenario 3: Insert / update / delete rows

```javascript
// Insert
await db.from("posts").insert({ title: "Hello" });

// Update
await db.from("posts").update({ title: "Updated" }).eq("id", 1);

// Delete
await db.from("posts").delete().eq("id", 1);
```

---

## Key principle: CloudBase Relational Database = Supabase API

- After you have `db = app.rdb()`, use **Supabase documentation and patterns** for all queries.
- This skill only standardizes **Web initialization and client sharing**.
- Do not duplicate Supabase docs into this skill; rely on the model's built-in Supabase knowledge for query shapes and options.
