---
name: auth-web-cloudbase
description: CloudBase Web Authentication Quick Guide for frontend integration after auth-tool has already been checked. Provides concise and practical Web authentication solutions with multiple login methods and complete user management.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The task is a CloudBase Web login, registration, session, or user profile flow built with `@cloudbase/js-sdk` and the auth provider setup has already been checked.

### Read before writing code if

- The user needs a login page, auth modal, session handling, or protected Web route. Read `auth-tool` first to ensure providers are enabled, then return here for frontend integration.

### Then also read

- `../auth-tool/SKILL.md` for provider setup
- `../web-development/SKILL.md` for Web project structure and deployment

### Do not start here first when

- The request is a Web auth flow but provider configuration has not been verified yet.
- In that case, activate `auth-tool-cloudbase` before `auth-web-cloudbase`.

### Do NOT use for

- Mini program auth, native App auth, or server-side auth setup.

### Common mistakes / gotchas

- Skipping publishable key and provider checks.
- Replacing built-in Web auth with cloud function login logic.
- Reusing this flow in Flutter, React Native, or native iOS/Android code.
- Creating a detached helper file with `auth.signUp` / `verifyOtp` but never wiring it into the existing form handlers, so the actual button clicks still do nothing.

## Overview

**Prerequisites**: CloudBase environment ID (`env`)
**Prerequisites**: CloudBase environment Region (`region`)

---

## Core Capabilities

**Use Case**: Web frontend projects using `@cloudbase/js-sdk@2.24.0+` for user authentication  
**Key Benefits**: Compatible with `supabase-js` API, supports phone, email, anonymous, username/password, and third-party login methods
**Official `@cloudbase/js-sdk` CDN**: `https://static.cloudbase.net/cloudbase-js-sdk/latest/cloudbase.full.js`

Use the same CDN address as `web-development`. Prefer npm installation in modern bundler projects, and use the CDN form for static HTML, no-build demos, or low-friction examples.

## Prerequisites

- Automatically use `auth-tool-cloudbase` to get `publishable key` and configure login methods. 
- If `auth-tool-cloudbase` failed, let user go to `https://tcb.cloud.tencent.com/dev?envId={env}#/env/apikey` to get `publishable key` and `https://tcb.cloud.tencent.com/dev?envId={env}#/identity/login-manage` to set up login methods

### Parameter map

- `auth.signInWithOtp({ phone })` and `auth.signUp({ phone })` use the phone number in a `phone` field, not `phone_number`
- `auth.signInWithOtp({ email })` and `auth.signUp({ email })` use `email`
- `verifyOtp({ token })` expects the SMS or email code in `token`
- `accessKey` is the publishable key from `auth-tool-cloudbase`, not a secret key
- If the task mentions provider setup, stop and read `auth-tool-cloudbase` before writing frontend code

## Quick Start

```js
import cloudbase from '@cloudbase/js-sdk'

const app = cloudbase.init({
  env: `env`, // CloudBase environment ID
  region: `region`,  // CloudBase environment Region, default 'ap-shanghai'
  accessKey: 'publishable key', // required, get from auth-tool-cloudbase
  auth: { detectSessionInUrl: true }, // required
})

const auth = app.auth
``

---

## Login Methods

**1. Phone OTP (Recommended)**
- Automatically use `auth-tool-cloudbase` turn on `SMS Login`
```js
const { data, error } = await auth.signInWithOtp({ phone: '13800138000' })
const { data: loginData, error: loginError } = await data.verifyOtp({ token:'123456' })
```

**2. Email OTP**
- Automatically use `auth-tool-cloudbase` turn on `Email Login`
```js
const { data, error } = await auth.signInWithOtp({ email: 'user@example.com' })
const { data: loginData, error: loginError } = await data.verifyOtp({ token: '654321' })
```

**3. Password**
```js
const { data, error } = await auth.signInWithPassword({ username: 'test_user', password: 'pass123' })
const { data, error } = await auth.signInWithPassword({ email: 'user@example.com', password: 'pass123' })
const { data, error } = await auth.signInWithPassword({ phone: '13800138000', password: 'pass123' })
```

**4. Registration (Smart: auto-login if exists)**
- Only support email and phone otp registration
- Automatically use `auth-tool-cloudbase` turn on `Email Login` or `SMS Login`
- Use `phone` or `email` in the sign-up payload; do not invent `phone_number`
```js
// Email Otp
const { data, error } = await auth.signUp({ email: 'new@example.com', nickname: 'User' })
const { data: loginData, error: loginError } = await data.verifyOtp({ token: '123456' })

// Phone Otp
const { data, error } = await auth.signUp({ phone: '13800138000', nickname: 'User' })
const { data: loginData, error: loginError } = await data.verifyOtp({ token: '123456' })
```

When the project already has `handleSendCode` / `handleRegister` or similar UI handlers, wire the SDK calls there directly instead of leaving them commented out in `App.tsx`.

```tsx
const handleSendCode = async () => {
  const { data, error } = await auth.signUp({
    email,
    name: username || email.split('@')[0],
  })
  if (error) throw error
  setSignUpData(data)
}

const handleRegister = async () => {
  if (!signUpData?.verifyOtp) throw new Error('Please send the code first')
  const { error } = await signUpData.verifyOtp({
    email,
    token: code,
    type: 'signup',
  })
  if (error) throw error
}
```

**5. Anonymous**
- Automatically use `auth-tool-cloudbase` turn on `Anonymous Login`
```js
const { data, error } = await auth.signInAnonymously()
```

**6. OAuth (Google/WeChat)**
- Automatically use `auth-tool-cloudbase` turn on `Google Login` or `WeChat Login`
```js
const { data, error } = await auth.signInWithOAuth({ provider: 'google' })
window.location.href = data.url // Auto-complete after callback
```

**7. Custom Ticket**
```js
await auth.signInWithCustomTicket(async () => {
  const res = await fetch('/api/ticket')
  return (await res.json()).ticket
})
```

**8. Upgrade Anonymous**
```js
const { data, error } = await auth.getSession()
const { data: signUpData, error: signUpError} = await auth.signUp({
  phone: '13800000000',
  anonymous_token: data.session.access_token,
})
await signUpData.verifyOtp({ token: '123456' })
```

---

## User Management

```js
// Sign out
const { data, error } = await auth.signOut()

// Get user
const { data, error } = await auth.getUser()
console.log(data.user.email, data.user.phone, data.user.user_metadata?.nickName)

// Update user (except email, phone)
const { data, error } = await auth.updateUser({ nickname: 'New Name', gender: 'MALE', avatar_url: 'url' })

// Update user (email or phone)
const { data, error } = await auth.updateUser({ email: 'new@example.com' })
const { data, error } = await data.verifyOtp({ email: "new@example.com", token: "123456" });

// Change password (logged in)
const { data, error } = await auth.resetPasswordForOld({ old_password: 'old', new_password: 'new' })

// Reset password (forgot)
const { data, error } = await auth.reauthenticate()
const { data, error } = await data.updateUser({ nonce: '123456', password: 'new' })

// Link third-party
const { data, error } = await auth.linkIdentity({ provider: 'google' })

// View/Unlink identities
const { data, error } = await auth.getUserIdentities()
const { data, error } = await auth.unlinkIdentity({ provider: data.identities[0].id })

// Delete account
const { data, error } = await auth.deleteMe({ password: 'current' })

// Listen to state changes
const { data, error } = auth.onAuthStateChange((event, session, info) => {
  // INITIAL_SESSION, SIGNED_IN, SIGNED_OUT, TOKEN_REFRESHED, USER_UPDATED, PASSWORD_RECOVERY, BIND_IDENTITY
})

// Get access token
const { data, error } = const { data, error } = await auth.getSession()
fetch('/api/protected', { headers: { Authorization: `Bearer ${data.session?.access_token}` } })

// Refresh user
const { data, error } = await auth.refreshUser()
```

---

## User Type

```ts
declare type User = {
  id: any
  aud: string
  role: string[]
  email: any
  email_confirmed_at: string
  phone: any
  phone_confirmed_at: string
  confirmed_at: string
  last_sign_in_at: string
  app_metadata: {
    provider: any
    providers: any[]
  }
  user_metadata: {
    name: any
    picture: any
    username: any
    gender: any
    locale: any
    uid: any
    nickName: any
    avatarUrl: any
    location: any
    hasPassword: any
  }
  identities: any
  created_at: string
  updated_at: string
  is_anonymous: boolean
}
```

---

## Complete Example

```js
class PhoneLoginPage {
  async sendCode() {
    const phone = document.getElementById('phone').value
    if (!/^1[3-9]\d{9}$/.test(phone)) return alert('Invalid phone')

    const { data, error } = await auth.signInWithOtp({ phone })
    if (error) return alert('Send failed: ' + error.message)

    this.verifyFunction = data.verify
    document.getElementById('codeSection').style.display = 'block'
    this.startCountdown(60)
  }

  async verifyCode() {
    const code = document.getElementById('code').value
    if (!code) return alert('Enter code')

    const { data, error } = await this.verifyFunction(code)
    if (error) return alert('Verification failed: ' + error.message)

    console.log('Login successful:', data.user)
    window.location.href = '/dashboard'
  }

  startCountdown(seconds) {
    let countdown = seconds
    const btn = document.getElementById('resendBtn')
    btn.disabled = true

    const timer = setInterval(() => {
      countdown--
      btn.innerText = `Resend in ${countdown}s`
      if (countdown <= 0) {
        clearInterval(timer)
        btn.disabled = false
        btn.innerText = 'Resend'
      }
    }, 1000)
  }
}
```

---

## WeChat Mini Program

```js
// Silent login with OpenID
const { data, error } = await auth.signInWithOpenId() // WeChat Cloud mode (default)
const { data, error } = await auth.signInWithOpenId({ useWxCloud: false }) // HTTP mode

// Phone authorization login
const { data, error } = await auth.signInWithPhoneAuth({ phoneCode: 'xxx' })
```

---
