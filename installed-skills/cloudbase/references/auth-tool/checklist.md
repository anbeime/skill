# Authentication Activation Checklist

Use this checklist before generating any CloudBase authentication flow.

## When this checklist applies

- Web login or registration
- SMS, email, anonymous, Google, or WeChat provider setup
- HTTP API auth flows for native apps or backend integrations

## Required checks

1. Identify the client platform: Web, mini program, native app, or backend.
2. Confirm whether provider configuration must happen before code generation.
3. Check which login methods are required and enable them first.
4. For Web flows, get or confirm the publishable key before writing frontend auth code.
5. Route to the matching implementation skill after provider setup:
   - Web -> `auth-web`
   - Mini program -> `auth-wechat`
   - Native app / raw HTTP -> `http-api`

## Common failure patterns

- Writing a login page before enabling SMS or email login.
- Implementing Web login in cloud functions instead of CloudBase Auth.
- Using Web SDK patterns in native App code.

## Done criteria

- Required providers are enabled.
- Platform-specific auth path is selected.
- The next skill to read is explicit before code generation starts.
