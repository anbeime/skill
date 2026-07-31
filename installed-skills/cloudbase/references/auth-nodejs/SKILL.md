---
name: auth-nodejs-cloudbase
description: Complete guide for CloudBase Auth using the CloudBase Node SDK – caller identity, user lookup, custom login tickets, and server-side best practices.
alwaysApply: false
---

## When to use this skill

Use this skill whenever the task involves **server-side authentication or identity** in a CloudBase project, and the code is running in **Node.js**, for example:

- CloudBase 云函数 (Node runtime) that needs to know **who is calling**
- Node services that use **CloudBase Node SDK** to look up user information
- Backends that issue **custom login tickets** for Web / mobile clients
- Admin or ops tools that need to inspect CloudBase end-user profiles

**Do NOT use this skill for:**

- Frontend Web login / sign-up flows using `@cloudbase/js-sdk` (handle those with the **auth-web** skill, not this Node skill).
- Direct HTTP auth API integrations (this skill does not describe raw HTTP endpoints; use the **http-api** skill instead).
- Database or storage operations that do not involve identity (use database/storage docs or skills).

When the user request mixes frontend and backend concerns (e.g. "build a web login page and a Node API that knows the user"), treat them separately:

- Use Web-side auth docs/skills for client login and UX.
- Use this Node Auth skill for how the backend sees and uses the authenticated user.

---

## How to use this skill (for a coding agent)

When you load this skill to work on a task:

1. **Clarify the runtime and responsibility**

   Ask the user:

   - Where does this Node code run?
     - CloudBase 云函数
     - Long‑running Node service using CloudBase
   - What do they need from auth?
     - Just the **caller identity** for authorization?
     - **Look up arbitrary users** by UID / login identifier?
     - **Bridge their own user system** into CloudBase via custom login?

2. **Confirm CloudBase environment and SDK**

   - Ask for:
     - `env` – CloudBase environment ID
   - Install the latest `@cloudbase/node-sdk` from npm if it is not already available.
   - Always initialize the SDK using this pattern (values can change, shape must not):

   ```ts
   import tcb from "@cloudbase/node-sdk";

   const app = tcb.init({ env: "your-env-id" });
   const auth = app.auth();
   ```

3. **Pick the relevant scenario from this file**

   - For **caller identity inside a function**, use the `getUserInfo` scenarios.
   - For **full user profile or admin lookup**, use the `getEndUserInfo` and `queryUserInfo` scenarios.
   - For **client systems that already have their own users**, use the **custom login ticket** scenarios built on `createTicket`.
   - For **logging / security**, use the `getClientIP` scenario.

4. **Follow Node SDK API shapes exactly**

   - Treat all `auth.*` methods and parameter shapes in this file as canonical.
   - You may change variable names and framework (e.g. Express vs 云函数 handler), but **do not change SDK method names or parameter fields**.
   - If you see a method in older code that is not listed here or in the Node SDK docs mirror, treat it as suspect and avoid using it.

5. **If you are unsure about an API**

   - Consult the official CloudBase Auth Node SDK documentation.
   - Only use methods and shapes that appear in the official documentation.
   - If you cannot find an API you want:
     - Prefer composing flows from the documented methods, or
     - Explain that this skill only covers Node SDK auth, and suggest using the relevant CloudBase Web or HTTP auth documentation for client-side or raw-HTTP flows.

---

## Node auth architecture – how Node fits into CloudBase Auth

CloudBase Auth v2 separates **where users log in** from **where backend code runs**:

- Users log in through the supported auth methods (anonymous, username/password, SMS, email, WeChat, custom login, etc.) using client SDKs or HTTP interfaces, as described in the official CloudBase Auth overview documentation.
- Once logged in, CloudBase attaches the user identity and tokens to the environment.
- Node code then **reads** that identity using the Node SDK, or **bridges** external identities into CloudBase using custom login.

In practice, Node code usually does one or more of:

1. **Identify the current caller**

   - In 云函数, use `auth.getUserInfo()` to read `uid`, `openId`, and `customUserId`.
   - Use this identity for **authorization decisions**, logging, and personalisation.

2. **Look up other users**

   - Use `auth.getEndUserInfo(uid)` when you know the CloudBase `uid`.
   - Use `auth.queryUserInfo({ platform, platformId, uid? })` when you only have login identifiers such as phone, email, username, or a custom ID.

3. **Issue custom login tickets**

   - When you already have your own user system, your Node backend can call `auth.createTicket(customUserId, options)` and return the ticket to a trusted client.
   - The client (typically Web) then uses this ticket with the Web SDK to log the user into CloudBase without forcing them to sign up again.

4. **Log client IP for security**

   - In 云函数, `auth.getClientIP()` returns the caller IP, which you can use for audit logs, anomaly detection, or access control.

The scenarios later in this file turn these responsibilities into explicit, copy‑pasteable patterns.

---

## Node Auth APIs covered by this skill

This skill covers the following `auth` methods on the CloudBase Node SDK. Treat these method signatures as the only supported entry points for Node auth flows when using this skill:

- `getUserInfo(): IGetUserInfoResult`
  Returns `{ openId, appId, uid, customUserId }` for the **current caller**.

- `getEndUserInfo(uid?: string, opts?: ICustomReqOpts): Promise<{ userInfo: EndUserInfo; requestId?: string }>`
  Returns detailed CloudBase end‑user profile for a given `uid` or for the current caller (when `uid` is omitted).

- `queryUserInfo(query: IUserInfoQuery, opts?: ICustomReqOpts): Promise<{ userInfo: EndUserInfo; requestId?: string }>`
  Finds a user by login identifier (`platform` + `platformId`) or `uid`.

- `getClientIP(): string`
  Returns the caller’s IP address when running in a supported environment (e.g. 云函数).

- `createTicket(customUserId: string, options?: ICreateTicketOpts): string`
  Creates a **custom login ticket** for the given `customUserId` that clients can exchange for a CloudBase login.

The exact field names and allowed values for `EndUserInfo`, `IUserInfoQuery`, and `ICreateTicketOpts` are defined by the official CloudBase Node SDK typings and documentation. When writing Node code, do not guess shapes; follow the SDK types and the examples in this file.

---

## Scenarios – Node auth patterns

### Scenario 1: Initialize Node SDK and auth in a CloudBase function

Use this when writing a CloudBase 云函数 that needs to interact with Auth:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  // Your logic here
};
```

Key points:

- Use the same `env` as configured for the function’s CloudBase 环境.
- Avoid hardcoding sensitive values; prefer environment variables or function configuration.

### Scenario 2: Get caller identity in a CloudBase function

Use this when you need to know **who is calling** your cloud function:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  const { openId, appId, uid, customUserId } = auth.getUserInfo();

  console.log("Caller identity", { openId, appId, uid, customUserId });

  // Use uid / customUserId for authorization decisions
  // e.g. check roles, permissions, or data ownership
};
```

Best practices:

- Treat `uid` as the canonical CloudBase user identifier.
- Use `customUserId` only when you have enabled **自定义登录** and mapped your own users.
- Never trust `openId`/`appId` alone for authorization; they are WeChat‑specific identifiers.

### Scenario 3: Get full end‑user profile by UID

Use this when you know a user’s CloudBase `uid` (for example, from a database record) and you need detailed profile information:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  const uid = "user-uid";

  try {
    const { userInfo } = await auth.getEndUserInfo(uid);
    console.log("User profile", userInfo);
  } catch (error) {
    console.error("Failed to get end user info", error.message);
  }
};
```

Best practices:

- Call `getEndUserInfo` from trusted backend code only; do not expose it directly to untrusted clients.
- Log minimal necessary data for debugging; avoid logging full profiles in production.

### Scenario 4: Get full profile for the current caller

Use this when you want the **current caller’s** full profile without manually passing `uid`:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  try {
    const { userInfo } = await auth.getEndUserInfo();
    console.log("Current caller profile", userInfo);
  } catch (error) {
    console.error("Failed to get current caller profile", error.message);
  }
};
```

This relies on the environment providing the caller’s identity (e.g. within a CloudBase 云函数). If called where no caller context exists, refer to the official docs and handle errors gracefully.

### Scenario 5: Query user by login identifier

Use this when you only know a user’s login identifier (phone, email, username, or custom ID) and need their CloudBase profile:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  try {
    // Find by phone number
    const { userInfo: byPhone } = await auth.queryUserInfo({
      platform: "PHONE",
      platformId: "+86 13800000000",
    });

    // Find by email
    const { userInfo: byEmail } = await auth.queryUserInfo({
      platform: "EMAIL",
      platformId: "test@example.com",
    });

    // Find by customUserId
    const { userInfo: byCustomId } = await auth.queryUserInfo({
      platform: "CUSTOM",
      platformId: "your-customUserId",
    });

    console.log({ byPhone, byEmail, byCustomId });
  } catch (error) {
    console.error("Failed to query user info", error.message);
  }
};
```

Best practices:

- Prefer `uid` when you already have it; use `queryUserInfo` only when needed.
- Make sure `platformId` uses the exact format you used at sign‑up (e.g. `+86` + phone number).

### Scenario 6: Get client IP in a function

Use this for logging or basic IP‑based checks:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: "your-env-id" });
const auth = app.auth();

exports.main = async (event, context) => {
  const ip = auth.getClientIP();
  console.log("Caller IP", ip);

  // e.g. block or flag suspicious IPs
};
```

---

## Custom login tickets (Node side only)

Custom login lets you keep your existing user system while still mapping each user to a CloudBase account.

### Scenario 7: Initialize Node SDK with custom login credentials

Before issuing tickets, install the custom login private key file from the CloudBase console and load it in Node:

```ts
import tcb from "@cloudbase/node-sdk";
import path from "node:path";

const app = tcb.init({
  env: "your-env-id",
  credentials: require(path.join(__dirname, "tcb_custom_login.json")),
});

const auth = app.auth();
```

Keep `tcb_custom_login.json` secret and **never** bundle it into frontend code.

### Scenario 8: Issue a custom login ticket for a given customUserId

Use this in backend code that has already authenticated your own user and wants to let them log into CloudBase:

```ts
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({
  env: "your-env-id",
  credentials: require("/secure/path/to/tcb_custom_login.json"),
});

const auth = app.auth();

exports.main = async (event, context) => {
  const customUserId = "your-customUserId";

  const ticket = auth.createTicket(customUserId, {
    refresh: 3600 * 1000,       // access_token refresh interval (ms)
    expire: 24 * 3600 * 1000,   // ticket expiration time (ms)
  });

  // Return the ticket to the trusted client (e.g. via HTTP response)
  return { ticket };
};
```

Constraints for `customUserId` (from official docs):

- Length 4–32 characters.
- Allowed characters: letters, digits, and `_-#@(){}[]:.,<>+#~`.

Best practices:

- Only issue tickets after your own user authentication succeeds.
- Store `customUserId` in your own user database and keep it stable over time.
- Do not reuse `customUserId` for multiple distinct people.

### Scenario 9: How this pairs with Web custom login

This skill only covers **Node-side** ticket issuance. For the **client-side** flow:

- On the client (Web), use `@cloudbase/js-sdk`'s custom login support:
  - Call your backend endpoint that returns `ticket`.
  - Configure `auth.setCustomSignFunc(async () => ticketFromBackend)`.
  - Call `auth.signInWithCustomTicket()` to finish login.

Keep the responsibility clear:

- Node: authenticate your own user → create ticket → return ticket securely.
- Web: receive ticket → sign into CloudBase using documented Web SDK APIs.

---

## Node auth best practices

- **Single source of truth for identity**
  - Treat CloudBase `uid` as the primary key when relating end‑user records.
  - Use `customUserId` only as a bridge to your own user system.

- **Least privilege**
  - Perform authorization checks in Node using `uid`, roles, and ownership, not just login success.
  - Avoid exposing raw `getEndUserInfo` / `queryUserInfo` results directly to clients.

- **Error handling**
  - Wrap all `auth.*` calls in `try/catch` when they return promises.
  - Log `error.message` (and `error.code` if present), but avoid logging sensitive data.

- **Security**
  - Protect `tcb_custom_login.json` as you would any private key.
  - Rotate custom login keys according to CloudBase guidance when necessary.
  - Use HTTPS and proper authentication between your clients and Node backend when exchanging tickets.

---

## Summary

Use this Node Auth skill whenever you need to:

- Know **who** is calling your Node code in CloudBase.
- Look up CloudBase users by `uid` or login identifier.
- Bridge an existing user system into CloudBase with **custom login tickets**.
- Apply consistent, secure, server‑side auth best practices.

For end‑to‑end experiences, pair this skill with:

- Web‑side auth documentation (for all browser‑side login and UX using `@cloudbase/js-sdk`).
- CloudBase HTTP auth documentation (for language‑agnostic HTTP integrations, if you are using those).

Treat the official CloudBase Auth Node SDK documentation as the canonical reference for Node auth APIs, and treat the scenarios in this file as vetted best‑practice building blocks.
