---
name: auth-tool-cloudbase
description: First-step CloudBase auth provider setup skill for login and registration flows. Use it before auth-web to configure and manage authentication providers for web applications - enable/disable login methods (SMS, Email, WeChat Open Platform, Google, Anonymous, Username/password, OAuth, SAML, CAS, Dingding, etc.) and configure provider settings via MCP tools `callCloudApi`.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The user mentions login, registration, authentication, provider setup, SMS, email, anonymous login, or third-party login.
- A Web, native App, or backend flow needs CloudBase auth configuration before implementation.
- For any CloudBase Web auth flow, activate this skill before `auth-web`.

### Read before writing code if

- The request includes any auth UI or auth API work. Provider status must be checked first.
- When the task is a Web auth flow, read `auth-web` after this skill and before writing frontend code.

### Then also read

- Web auth UI -> `../auth-web/SKILL.md`
- Mini program auth -> `../auth-wechat/SKILL.md`
- Native App / raw HTTP -> `../http-api/SKILL.md`

### Do NOT use this as

- A replacement for platform implementation rules. This skill configures providers; it does not define the full frontend or client integration path.

### Common mistakes / gotchas

- Writing login UI before enabling the required provider.
- Implementing Web login in cloud functions.
- Routing native App auth to Web SDK flows.

### Minimal checklist

- Read [Authentication Activation Checklist](checklist.md) before auth implementation.

## Overview

Configure CloudBase authentication providers: Anonymous, Username/Password, SMS, Email, WeChat, Google, and more.

**Prerequisites**: CloudBase environment ID (`env`)

---

## Authentication Scenarios

### 1. Get Login Config

Use the official login-config API. Do **not** use `lowcode/DescribeLoginStrategy` or `lowcode/ModifyLoginStrategy` as the default path.

Query current login configuration:
```js
{
    "params": { "EnvId": `env` },
    "service": "tcb",
    "action": "DescribeLoginConfig"
}
```

The response contains fields such as:

- `AnonymousLogin`
- `UserNameLogin`
- `PhoneNumberLogin`
- `EmailLogin`
- `SmsVerificationConfig`
- `MfaConfig`
- `PwdUpdateStrategy`

Parameter mapping for downstream Web auth code:

- `PhoneNumberLogin` controls phone OTP flows used by `auth-web` `auth.signInWithOtp({ phone })` and `auth.signUp({ phone })`
- `EmailLogin` controls email OTP flows used by `auth-web` `auth.signInWithOtp({ email })` and `auth.signUp({ email })`
- `UserNameLogin` controls password login flows used by `auth-web` `auth.signInWithPassword({ username, password })`
- `SmsVerificationConfig.Type = "apis"` requires both `Name` and `Method`
- `EnvId` is always the CloudBase environment ID, not the publishable key

Before calling `ModifyLoginConfig`, rebuild the payload from writable keys only. Do **not** spread the full response object back into the request.

```js
const WritableLoginConfig = {
    "PhoneNumberLogin": LoginConfig.PhoneNumberLogin,
    "EmailLogin": LoginConfig.EmailLogin,
    "UserNameLogin": LoginConfig.UserNameLogin,
    "AnonymousLogin": LoginConfig.AnonymousLogin,
    ...(LoginConfig.SmsVerificationConfig ? { "SmsVerificationConfig": LoginConfig.SmsVerificationConfig } : {}),
    ...(LoginConfig.MfaConfig ? { "MfaConfig": LoginConfig.MfaConfig } : {}),
    ...(LoginConfig.PwdUpdateStrategy ? { "PwdUpdateStrategy": LoginConfig.PwdUpdateStrategy } : {})
}
```

---

### 2. Anonymous Login

1. Get `LoginConfig` (see Scenario 1)
2. Set `LoginConfig.AnonymousLogin = true` (on) or `false` (off)
3. Update:
```js
{
    "params": { "EnvId": `env`, ...WritableLoginConfig, "AnonymousLogin": true },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

---

### 3. Username/Password Login

1. Get `LoginConfig` (see Scenario 1)
2. Set `LoginConfig.UserNameLogin = true` (on) or `false` (off)
3. Update:
```js
{
    "params": { "EnvId": `env`, ...WritableLoginConfig, "UserNameLogin": true },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

---

### 4. SMS Login

1. Get `LoginConfig` (see Scenario 1)
2. Modify:
   - **Turn on**: `LoginConfig.PhoneNumberLogin = true`
   - **Turn off**: `LoginConfig.PhoneNumberLogin = false`
   - **Config** (optional):
     ```js
     LoginConfig.SmsVerificationConfig = {
         Type: 'default',      // 'default' or 'apis'
         Name: 'method_53978f9f96a35', // required when Type = 'apis'
         Method: 'SendVerificationCode',
         SmsDayLimit: 30       // -1 = unlimited
     }
     ```
3. Update:
```js
{
    "params": {
        "EnvId": `env`,
        ...WritableLoginConfig,
        "PhoneNumberLogin": true,
        "SmsVerificationConfig": {
            "Type": "default",
            "SmsDayLimit": 30
        }
    },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

**Use custom apis to send SMS**:
```js
{
    "params": {
        "EnvId": `env`,
        ...WritableLoginConfig,
        "PhoneNumberLogin": true,
        "SmsVerificationConfig": {
            "Type": "apis",
            "Name": "method_53978f9f96a35",
            "Method": "SendVerificationCode",
            "SmsDayLimit": 20
        }
    },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

---

### 5. Email Login

Email has two layers of configuration:

- `ModifyLoginConfig.EmailLogin`: controls whether email/password login is enabled
- `ModifyProvider(Id="email")`: controls the email sender channel and SMTP configuration
- In Web auth code, this maps to `auth.signInWithOtp({ email })` and `auth.signUp({ email })`

**Turn on email/password login**:
```js
{
    "params": { "EnvId": `env`, ...WritableLoginConfig, "EmailLogin": true },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

**Turn off email/password login**:
```js
{
    "params": { "EnvId": `env`, ...WritableLoginConfig, "EmailLogin": false },
    "service": "tcb",
    "action": "ModifyLoginConfig"
}
```

**Configure email provider (Tencent Cloud email)**:
```js
{
    "params": {
        "EnvId": `env`,
        "Id": "email",
        "On": "TRUE",
        "EmailConfig": { "On": "TRUE", "SmtpConfig": {} }
    },
    "service": "tcb",
    "action": "ModifyProvider"
}
```

**Disable email provider**:
```js
{
    "params": { "EnvId": `env`, "Id": "email", "On": "FALSE" },
    "service": "tcb",
    "action": "ModifyProvider"
}
```

**Configure email provider (custom SMTP)**:
```js
{
    "params": {
        "EnvId": `env`,
        "Id": "email",
        "On": "TRUE",
        "EmailConfig": {
            "On": "FALSE",
            "SmtpConfig": {
                "AccountPassword": "password",
                "AccountUsername": "username",
                "SecurityMode": "SSL",
                "SenderAddress": "sender@example.com",
                "ServerHost": "smtp.qq.com",
                "ServerPort": 465
            }
        }
    },
    "service": "tcb",
    "action": "ModifyProvider"
}
```

---

### 6. WeChat Login

1. Get WeChat config:
```js
{
    "params": { "EnvId": `env` },
    "service": "tcb",
    "action": "GetProviders"
}
```
Filter by `Id == "wx_open"`, save as `WeChatProvider`.

2. Get credentials from [WeChat Open Platform](https://open.weixin.qq.com/cgi-bin/readtemplate?t=regist/regist_tmpl):
   - `AppID`
   - `AppSecret`

3. Update:
```js
{
    "params": {
        "EnvId": `env`,
        "Id": "wx_open",
        "On": "TRUE",  // "FALSE" to disable
        "Config": {
            ...WeChatProvider.Config,
            ClientId: `AppID`,
            ClientSecret: `AppSecret`
        }
    },
    "service": "tcb",
    "action": "ModifyProvider"
}
```

---

### 7. Google Login

1. Get redirect URI:
```js
{
    "params": { "EnvId": `env` },
    "service": "lowcode",
    "action": "DescribeStaticDomain"
}
```
Save `result.Data.StaticDomain` as `staticDomain`.

2. Configure at [Google Cloud Console](https://console.cloud.google.com/apis/credentials):
   - Create OAuth 2.0 Client ID
   - Set redirect URI: `https://{staticDomain}/__auth/`
   - Get `Client ID` and `Client Secret`

3. Enable:
```js
{
    "params": {
        "EnvId": `env`,
        "ProviderType": "OAUTH",
        "Id": "google",
        "On": "TRUE",  // "FALSE" to disable
        "Name": { "Message": "Google" },
        "Description": { "Message": "" },
        "Config": {
            "ClientId": `Client ID`,
            "ClientSecret": `Client Secret`,
            "Scope": "email openid profile",
            "AuthorizationEndpoint": "https://accounts.google.com/o/oauth2/v2/auth",
            "TokenEndpoint": "https://oauth2.googleapis.com/token",
            "UserinfoEndpoint": "https://www.googleapis.com/oauth2/v3/userinfo",
            "TokenEndpointAuthMethod": "CLIENT_SECRET_BASIC",
            "RequestParametersMap": {
                "RegisterUserSyncScope": "syncEveryLogin",
                "IsGoogle": "TRUE"
            }
        },
        "Picture": "https://qcloudimg.tencent-cloud.cn/raw/f9131c00dcbcbccd5899a449d68da3ba.png",
        "TransparentMode": "FALSE",
        "ReuseUserId": "TRUE",
        "AutoSignUpWithProviderUser": "TRUE"
    },
    "service": "tcb",
    "action": "ModifyProvider"
}
```

### 8. Client Configuration Boundary

Use client APIs for client metadata and token/session settings. Do not use them as a replacement for login strategy or provider management.

**Query client config**:
```js
{
    "params": { "EnvId": `env`, "Id": `env` },
    "service": "tcb",
    "action": "DescribeClient"
}
```

**Update client config**:
```js
{
    "params": {
        "EnvId": `env`,
        "Id": `env`,
        "AccessTokenExpiresIn": 7200,
        "RefreshTokenExpiresIn": 2592000,
        "MaxDevice": 3
    },
    "service": "tcb",
    "action": "ModifyClient"
}
```

### 9. Get Publishable Key

**Query existing key**:
```js
{
    "params": { "EnvId": `env`, "KeyType": "publish_key", "PageNumber": 1, "PageSize": 10 },
    "service": "lowcode",
    "action": "DescribeApiKeyTokens"
}
```
Return `PublishableKey.ApiKey` if exists (filter by `Name == "publish_key"`).

**Create new key** (if not exists):
```js
{
    "params": { "EnvId": `env`, "KeyType": "publish_key", "KeyName": "publish_key" },
    "service": "lowcode",
    "action": "CreateApiKeyToken"
}
```
If creation fails, direct user to: "https://tcb.cloud.tencent.com/dev?envId=`env`#/env/apikey"
