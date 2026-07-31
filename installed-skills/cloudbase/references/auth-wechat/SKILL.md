---
name: auth-wechat-miniprogram
description: Complete guide for WeChat Mini Program authentication with CloudBase - native login, user identity, and cloud function integration.
alwaysApply: false
---

## When to use this skill

Use this skill for **WeChat Mini Program (小程序) authentication** in a CloudBase project.

Use it when you need to:

- Implement WeChat Mini Program login with CloudBase
- Access user identity (openid, unionid) in cloud functions
- Understand how WeChat authentication integrates with CloudBase
- Build Mini Program features that require user identification

**Key advantage:** WeChat Mini Program authentication with CloudBase is **seamless and automatic** - no complex OAuth flows needed. When a Mini Program calls a cloud function, the user's `openid` is automatically injected and verified by WeChat.

**Do NOT use for:**

- Web-based WeChat login (use the **auth-web** skill)
- Server-side auth with Node SDK (use the **auth-nodejs** skill)
- Non-WeChat authentication methods (use appropriate auth skills)

---

## How to use this skill (for a coding agent)

1. **Confirm CloudBase environment**
   - Ask the user for:
     - `env` – CloudBase environment ID
     - Confirm the Mini Program is linked to the CloudBase environment

2. **Understand the authentication flow**
   - WeChat Mini Program authentication is **native and automatic**
   - No explicit login API calls needed in most cases
   - User identity is automatically available in cloud functions
   - CloudBase handles all authentication verification

3. **Pick a scenario from this file**
   - For basic user identity in cloud functions, use **Scenario 2**
   - For Mini Program initialization, use **Scenario 1**
   - For calling a cloud function from the Mini Program and receiving user identity, use **Scenario 3**
   - For testing authentication, use **Scenario 4**

4. **Follow CloudBase API shapes exactly**
   - Use `wx-server-sdk` in cloud functions
   - Use `wx.cloud` in Mini Program client code
   - Treat method names and parameter shapes in this file as canonical

5. **If you're unsure about an API**
   - Consult the official CloudBase Mini Program documentation
   - Only use methods that appear in official documentation

---

## Core concepts

### How WeChat Mini Program authentication works with CloudBase

1. **Automatic authentication:**
   - When a Mini Program user calls a cloud function, WeChat automatically injects the user's identity
   - No need for complex OAuth flows or token management
   - CloudBase verifies the authenticity of the identity

2. **User identifiers:**
   - `OPENID` – Unique identifier for the user in this specific Mini Program
   - `APPID` – The Mini Program's App ID
   - `UNIONID` – (Optional) Unique identifier across all apps under the same WeChat Open Platform account
     - Only available when the Mini Program is bound to a WeChat Open Platform account
     - Useful for identifying the same user across multiple Mini Programs or Official Accounts

3. **Security:**
   - The `openid`, `appid`, and `unionid` are **verified and trustworthy**
   - WeChat has already completed authentication
   - Developers can directly use these identifiers without additional verification

4. **No explicit login required:**
   - Users are automatically authenticated when they use the Mini Program
   - No need to call login APIs in most cases
   - Identity is available immediately in cloud functions

---

## Scenarios – WeChat Mini Program auth patterns

### Scenario 1: Initialize CloudBase in Mini Program

Use this in your Mini Program's `app.js` or entry point:

```js
// app.js
App({
  onLaunch: function () {
    // Initialize CloudBase
    wx.cloud.init({
      env: 'your-env-id',  // Your CloudBase environment ID
      traceUser: true      // Optional: track user access in console
    })
  }
})
```

**Key points:**

- Call `wx.cloud.init()` once when the Mini Program launches
- Set `env` to your CloudBase environment ID
- `traceUser: true` enables user access tracking in CloudBase console (optional but recommended)

---

### Scenario 2: Get user identity in a cloud function

Use this when you need to know **who is calling** your cloud function:

```js
// Cloud function: cloudfunctions/getUserInfo/index.js
const cloud = require('wx-server-sdk')

// Initialize cloud with dynamic environment
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
})

exports.main = async (event, context) => {
  // Get user identity - this is automatically injected by WeChat
  const { OPENID, APPID, UNIONID } = cloud.getWXContext()

  console.log('User identity:', { OPENID, APPID, UNIONID })

  // Use OPENID for user-specific operations
  // For example: query user data, check permissions, etc.

  return {
    openid: OPENID,
    appid: APPID,
    unionid: UNIONID  // May be undefined if not available
  }
}
```

**Key points:**

- Use `cloud.getWXContext()` to get user identity
- `OPENID` is always available and uniquely identifies the user
- `APPID` identifies the Mini Program
- `UNIONID` is only available when:
  - The Mini Program is bound to a WeChat Open Platform account
  - The user has authorized the Mini Program
- These values are **verified and trustworthy** - no need to validate them
- Use `cloud.DYNAMIC_CURRENT_ENV` to automatically use the current environment

**Best practices:**

- Store `OPENID` in your database to associate data with users
- Use `OPENID` for authorization and access control
- Use `UNIONID` when you need to identify users across multiple Mini Programs or Official Accounts
- Never expose `OPENID` to other users (it's a private identifier)

---

### Scenario 3: Call cloud function from Mini Program

Use this in your Mini Program to call a cloud function and get user identity:

```js
// In Mini Program page
Page({
  onLoad: function() {
    this.getUserInfo()
  },

  getUserInfo: function() {
    wx.cloud.callFunction({
      name: 'getUserInfo',  // Cloud function name
      data: {},             // Optional parameters
      success: res => {
        console.log('User info from cloud function:', res.result)
        // res.result contains { openid, appid, unionid }

        // Use the user info
        this.setData({
          openid: res.result.openid
        })
      },
      fail: err => {
        console.error('Failed to get user info:', err)
      }
    })
  }
})
```

**Key points:**

- Use `wx.cloud.callFunction()` to call cloud functions
- User identity is automatically passed to the cloud function
- No need to manually send user credentials
- Handle both success and error cases

---

### Scenario 4: Test authentication - Simple test function

**Cloud function (cloudfunctions/test/index.js):**

```js
const cloud = require('wx-server-sdk')

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
})

exports.main = async (event, context) => {
  // Get verified user identity - automatically injected by WeChat
  const { OPENID, APPID, UNIONID } = cloud.getWXContext()

  console.log('User identity:', { OPENID, APPID, UNIONID })

  return {
    success: true,
    message: 'Authentication successful',
    identity: {
      openid: OPENID,
      appid: APPID,
      unionid: UNIONID || 'Not available'
    },
    timestamp: new Date().toISOString()
  }
}
```

**Mini Program code:**

```js
// pages/index/index.js
Page({
  data: {
    userIdentity: null
  },

  onLoad: function() {
    this.testAuth()
  },

  testAuth: function() {
    console.log('Testing authentication...')

    wx.cloud.callFunction({
      name: 'test',
      success: res => {
        console.log('Authentication test result:', res.result)

        this.setData({
          userIdentity: res.result.identity
        })

        wx.showToast({
          title: 'Auth successful',
          icon: 'success'
        })
      },
      fail: err => {
        console.error('Authentication test failed:', err)
        wx.showToast({
          title: 'Auth failed',
          icon: 'error'
        })
      }
    })
  }
})
```

**Key points:**

- No explicit login API call needed
- User identity is automatically available in cloud function
- `OPENID` is always present and verified
- `UNIONID` may be undefined if not available
- Use this pattern to verify authentication is working correctly

---

## Best practices

### 1. Always use cloud.DYNAMIC_CURRENT_ENV

```js
cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
})
```

This ensures the cloud function uses the correct environment automatically.

### 2. Store OPENID for user identification

- Use `OPENID` as the primary user identifier
- Store it in your database to associate data with users
- Never expose `OPENID` to other users

### 3. Handle UNIONID availability

```js
const { OPENID, UNIONID } = cloud.getWXContext()

if (UNIONID) {
  // User has UNIONID - can be used for cross-app identification
  console.log('UNIONID available:', UNIONID)
} else {
  // UNIONID not available - use OPENID only
  console.log('Using OPENID only:', OPENID)
}
```

### 4. Use OPENID for user-specific operations

- Use `OPENID` to identify and authorize users
- Store `OPENID` when you need to associate data with users
- Use `OPENID` in queries to ensure users only access their own data

### 5. Error handling

Always handle errors when calling cloud functions:

```js
wx.cloud.callFunction({
  name: 'myFunction',
  success: res => {
    // Handle success
  },
  fail: err => {
    console.error('Cloud function error:', err)
    // Show user-friendly error message
    wx.showToast({
      title: 'Operation failed',
      icon: 'error'
    })
  }
})
```

### 6. Initialize CloudBase early

Initialize CloudBase in `app.js` `onLaunch`:

```js
App({
  onLaunch: function () {
    wx.cloud.init({
      env: 'your-env-id',
      traceUser: true
    })
  }
})
```

---

## Common patterns

### Pattern 1: Get and return user identity

```js
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async (event, context) => {
  const { OPENID, APPID, UNIONID } = cloud.getWXContext()

  return {
    openid: OPENID,
    appid: APPID,
    unionid: UNIONID || null
  }
}
```

### Pattern 2: Use OPENID for authorization

```js
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async (event, context) => {
  const { OPENID } = cloud.getWXContext()

  // Check if user is authorized
  if (OPENID === event.resourceOwnerId) {
    // User is authorized to access this resource
    return { authorized: true }
  } else {
    return { authorized: false, error: 'Unauthorized' }
  }
}
```

### Pattern 3: Handle UNIONID availability

```js
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

exports.main = async (event, context) => {
  const { OPENID, UNIONID } = cloud.getWXContext()

  if (UNIONID) {
    // Can use UNIONID for cross-app user identification
    console.log('User has UNIONID:', UNIONID)
  } else {
    // Fall back to OPENID only
    console.log('Using OPENID only:', OPENID)
  }

  return { openid: OPENID, hasUnionId: !!UNIONID }
}
```

---

## Summary

WeChat Mini Program authentication with CloudBase is **simple and secure**:

1. **No explicit login needed** - authentication is automatic
2. **User identity is verified** - `OPENID`, `APPID`, and `UNIONID` are trustworthy
3. **Easy to use** - just call `cloud.getWXContext()` in cloud functions
4. **Secure by default** - WeChat handles all authentication verification

**Key takeaways:**

- Initialize CloudBase with `wx.cloud.init()` in Mini Program
- Use `cloud.getWXContext()` to get user identity in cloud functions
- Use `OPENID` for user identification and authorization
- Handle `UNIONID` availability appropriately
- No explicit login API calls needed - authentication is automatic

For more complex authentication scenarios or integration with other systems, consider using CloudBase custom login in combination with WeChat authentication.
