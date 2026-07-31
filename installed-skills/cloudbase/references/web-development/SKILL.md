---
name: web-development
description: Web frontend project development rules. Use this skill when developing web frontend pages, deploying static hosting, and integrating CloudBase Web SDK.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The request is for a CloudBase Web app, static hosting site, frontend page, or Web SDK integration.

### Read before writing code if

- The task includes frontend structure, build config, deployment, routing, or Web SDK usage.

### Then also read

- Login flow -> `../auth-tool/SKILL.md`, then `../auth-web/SKILL.md`
- UI work -> `../ui-design/SKILL.md` first
- NoSQL / MySQL data work -> matching database skill

### Do NOT use for

- Mini programs, native Apps, or container backend services.

### Common mistakes / gotchas

- Treating cloud functions as the default solution for Web authentication.
- Starting UI implementation before reading `ui-design`.
- Routing native App requests into Web SDK code paths.

## When to use this skill

Use this skill for **Web frontend project development** when you need to:

- Develop web frontend pages and interfaces
- Deploy static websites to CloudBase static hosting
- Integrate CloudBase Web SDK for database, cloud functions, and authentication
- Set up modern frontend build systems (Vite, Webpack, etc.)
- Handle routing and build configurations for static hosting

**Do NOT use for:**
- Mini-program development (use miniprogram-development skill)
- Backend service development (use cloudrun-development skill)
- UI design only (use ui-design skill, but may combine with this skill)

---

## How to use this skill (for a coding agent)

1. **Follow project structure conventions**
   - Frontend source code in `src` directory
   - Build output in `dist` directory
   - Cloud functions in `cloudfunctions` directory
   - Use modern frontend build systems (Vite, etc.)

2. **Use CloudBase Web SDK correctly**
   - Always use SDK built-in authentication features
   - Never implement login logic in cloud functions
   - Use `envQuery` tool to get environment ID
   - Mention the official CDN early when the user needs a static HTML or no-build integration

3. **Deploy and preview properly**
   - Build project first (ensure `npm install` is executed)
   - Use relative paths for `publicPath` configuration
   - Use hash routing for better static hosting compatibility
   - Deploy to subdirectory if user doesn't specify root directory

---

# Web Frontend Development Rules

## Project Structure

1. **Directory Organization**:
   - Frontend source code should be stored in `src` directory
   - Build output should be placed in `dist` directory
   - Cloud functions should be in `cloudfunctions` directory

2. **Build System**:
   - Projects should use modern frontend build systems like Vite
   - Install dependencies via npm

3. **Routing**:
   - If the frontend project involves routing, use hash routing by default
   - Hash routing solves the 404 refresh issue and is more suitable for static website hosting deployment

## Deployment and Preview

1. **Static Hosting Deployment**:
   - For frontend projects, after building, you can use CloudBase static hosting
   - First start local preview, then confirm with user if deployment to CloudBase static hosting is needed
   - When deploying, if user has no special requirements, generally do not deploy directly to root directory
   - Return deployed address in markdown link format

2. **Local Preview**:
   - To preview static web pages locally, navigate to the specified output directory and use `npx live-server`

3. **Public Path Configuration**:
   - When web projects are deployed to static hosting CDN, since paths cannot be known in advance, `publicPath` and similar configurations should use relative paths instead of absolute paths
   - This solves resource loading issues

## CloudBase Web SDK Usage

1. **SDK Integration**:
   - If user's project needs database, cloud functions, and other features, need to introduce `@cloudbase/js-sdk@latest` in the web application
   - Official CDN: `https://static.cloudbase.net/cloudbase-js-sdk/latest/cloudbase.full.js`
   - Prefer npm for React, Vue, Vite, Webpack, and other bundler-based projects
   - Prefer the CDN only for static HTML pages, quick demos, embedded snippets, or README examples where a build step is unnecessary

**CDN quick start (static HTML / no-build)**:
```html
<script src="https://static.cloudbase.net/cloudbase-js-sdk/latest/cloudbase.full.js"></script>
<script>
const app = cloudbase.init({
  env: "xxxx-yyy",
});
</script>
```

**Important: Authentication must use SDK built-in features. It is strictly forbidden to implement login authentication logic using cloud functions!**

```js
import cloudbase from "@cloudbase/js-sdk";

const app = cloudbase.init({
  env: "xxxx-yyy", // Can query environment ID via envQuery tool
});
const auth = app.auth();

// Check current login state
let loginState = await auth.getLoginState();

if (loginState && loginState.user) {
  // Logged in
  const user = await auth.getCurrentUser();
  console.log("Current user:", user);
} else {
  // Not logged in - use SDK built-in authentication features
    
  // Collect user's phone number into variable `phoneNum` by providing a input UI

  // Send SMS code
  const verificationInfo = await auth.getVerification({
    phone_number: `+86 ${phoneNum}`,
  });
  
  // Collect user's phone number into variable `verificationCode` by providing a input UI 
  
  // Sign in
  await auth.signInWithSms({
    verificationInfo,
    verificationCode,
    phoneNum,
  });
}
```

**Initialization rules (Web, @cloudbase/js-sdk):**

- Always use **synchronous initialization** with the pattern above
- Do **not** lazy-load the SDK with `import("@cloudbase/js-sdk")`
- Do **not** wrap SDK initialization in async helpers such as `initCloudBase()` with internal `initPromise` caches
- Keep a single shared `app`/`auth` instance in your frontend app; reuse it instead of re-initializing

### Web SDK API usage rules

- Only use **documented** CloudBase Web SDK methods
- Before calling any method on `app`, `auth`, `db`, or other SDK objects, **confirm it exists in the official CloudBase Web SDK documentation**
- If a method or option is **not** mentioned in the official docs (for example some guessed method name), **do NOT invent or use it**
 
## Authentication Best Practices

1. **Must use SDK built-in authentication**: CloudBase Web SDK provides complete authentication features, including login by SMS, anonymous login, custom login, etc.

2. **Forbidden to implement login using cloud functions**: Do not create cloud functions to handle login logic, this is the wrong approach

3. **User data management**: After login, user information can be obtained via `auth.getCurrentUser()`, then stored to database

4. **Error handling**: All authentication operations should include complete error handling logic

## Build Process

**Web project build process**: Ensure `npm install` command has been executed first, then refer to project documentation for building
