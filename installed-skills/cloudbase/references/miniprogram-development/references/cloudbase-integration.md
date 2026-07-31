# CloudBase Mini Program References

This document supplements `SKILL.md` with practical **WeChat Mini Program + CloudBase** integration guidance.

## How to use this reference (for a coding agent)

1. **Understand platform differences**
   - WeChat Mini Program and Web have completely different authentication approaches.
   - Must strictly distinguish between platforms.
   - Never mix Web authentication methods into mini program projects.
   - Mini programs with CloudBase are naturally login-free.

2. **Follow CloudBase best practices**
   - Use `wx.cloud` APIs on the mini program client side.
   - Configure appropriate database permissions before relying on client writes.
   - Prefer cloud functions for cross-collection operations and privileged writes.
   - Use `OPENID` from `cloud.getWXContext()` as the stable user identifier on the server side.

3. **Use correct SDKs and APIs**
   - Mini program client code should use `wx.cloud.database()`, `wx.cloud.callFunction()`, and `wx.cloud.uploadFile()` as appropriate.
   - Do not use Web SDK authentication patterns in mini programs.
   - Use `envQuery` to get environment ID when available.

4. **Use CloudBase MCP via mcporter (CLI) when IDE MCP is not available**
   - You do **not** need to hard-code Secret ID / Secret Key / Env ID in config.
   - CloudBase MCP supports device-code login via the `auth` tool, so credentials can be obtained interactively.
   - Add CloudBase MCP server in `config/mcporter.json`:
     If other MCP servers already exist, keep them and only add the `cloudbase` entry.
     ```json
     {
       "mcpServers": {
         "cloudbase": {
           "command": "npx",
           "args": ["@cloudbase/cloudbase-mcp@latest"],
           "description": "CloudBase MCP",
           "lifecycle": "keep-alive"
         }
       }
     }
     ```
   - Discover tools and schemas:
     - `npx mcporter list` — list configured servers
     - `npx mcporter describe cloudbase --all-parameters` — inspect CloudBase server config and get full tool schemas with all parameters (⚠️ **必须加 `--all-parameters` 才能获取完整参数信息**)
     - `npx mcporter list cloudbase --schema` — get full JSON schema for all CloudBase tools
     - `npx mcporter call cloudbase.help --output json` — discover available CloudBase tools and their schemas
   - Call CloudBase tools (auth flow examples):
     - `npx mcporter call cloudbase.auth action=status --output json`
     - `npx mcporter call cloudbase.auth action=start_auth authMode=device --output json`
     - `npx mcporter call cloudbase.auth action=set_env envId=env-xxx --output json`

## 1. Environment Initialization

Mini programs using CloudBase should initialize `wx.cloud` once during app startup.

```js
App({
  onLaunch() {
    wx.cloud.init({
      env: "your-env-id",
      traceUser: true,
    });
  },
});
```

### Rules

- Always obtain the environment ID via `envQuery` when available.
- Prefer a single app-level initialization instead of repeated page-level initialization.
- Use `traceUser: true` unless there is a clear reason not to, so CloudBase can associate requests with the current WeChat user.

## 2. Authentication Model

Mini program CloudBase is **naturally login-free**.

### Required behavior

- Do **not** generate login pages or login flows.
- Do **not** port Web authentication patterns into mini programs.
- In cloud functions, retrieve user identity with `cloud.getWXContext().OPENID`.

```js
const cloud = require("wx-server-sdk");
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

exports.main = async () => {
  const wxContext = cloud.getWXContext();
  return {
    openid: wxContext.OPENID,
  };
};
```

## 3. Recommended Capability Boundaries

Use the right CloudBase capability in the right layer.

### Client side

- `wx.cloud.database()` for client-safe reads and user-scoped writes
- `wx.cloud.uploadFile()` for user-generated assets
- `wx.cloud.callFunction()` for invoking backend orchestration

### Cloud functions

- Privileged writes
- Cross-collection transactions or workflows
- Third-party API integration
- Data normalization / validation
- Accessing trusted user identity via `OPENID`

## 4. Environment Selection

- Do not hard-code a random environment ID.
- Prefer obtaining the environment ID from tooling such as `envQuery`.
- Initialize CloudBase once, usually in `app.js` / `app.ts`.

## 5. WeChat Developer Tools and Project Shape

- Confirm `project.config.json` includes `appid` before asking the user to open the project.
- Mini program source is typically under `miniprogram/`.
- Cloud functions are typically under `cloudfunctions/`.
- Generated pages should include companion config files such as `index.json`.

## 6. AI and Model Usage

- Mini programs on supported base library versions can use `wx.cloud.extend.AI`.
- Keep prompts and model selection explicit.
- If streaming is used, consume the stream fully and update UI incrementally where appropriate.

## 7. Fallback When IDE MCP Is Unavailable

If IDE-native MCP integration is unavailable, use the CloudBase MCP through `mcporter` and complete login with device-code auth instead of embedding secrets in config.

## 8. Console and Operational Links

When relevant, guide users to the CloudBase console for:

- environment settings
- database permission rules
- cloud function deployment status
- storage management
- billing / package information

Prefer console guidance over guessing permissions or environment state.
