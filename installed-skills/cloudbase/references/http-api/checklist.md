# HTTP API Routing Checklist

Use this checklist when the request comes from Android, iOS, Flutter, React Native, backend scripts, or any environment that is not using a CloudBase SDK.

## Required checks

1. Confirm the caller really needs raw HTTP APIs rather than Web SDK or MCP tools.
2. Confirm environment ID, region, and gateway base URL.
3. Choose the auth mechanism: AccessToken, API Key, or Publishable Key.
4. Query the matching OpenAPI definition before writing request code.
5. For database work, confirm whether the task is MySQL REST API, MCP SQL management, or Web SDK data access.

## Do not route here when

- The user is building a Web frontend with `@cloudbase/js-sdk`.
- The user is building a CloudBase mini program with `wx.cloud`.
- The task is MCP-driven database management rather than raw HTTP calls.

## Done criteria

- SDK support boundary is explicit.
- OpenAPI source has been checked.
- The auth method and request base URL are fixed before code generation.
