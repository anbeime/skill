---
name: cloudbase-platform
description: CloudBase platform knowledge and best practices. Use this skill for general CloudBase platform understanding, including storage, hosting, authentication, cloud functions, database permissions, and data models.
alwaysApply: false
---

## When to use this skill

Use this skill for **CloudBase platform knowledge** when you need to:

- Understand CloudBase storage and hosting concepts
- Configure authentication for different platforms (Web vs Mini Program)
- Deploy and manage cloud functions
- Understand database permissions and access control
- Work with data models (MySQL and NoSQL)
- Access CloudBase console management pages

**This skill provides foundational knowledge** that applies to all CloudBase projects, regardless of whether they are Web, Mini Program, or backend services.

---

## How to use this skill (for a coding agent)

1. **Understand platform differences**
   - Web and Mini Program have completely different authentication approaches
   - Must strictly distinguish between platforms
   - Never mix authentication methods across platforms

2. **Follow best practices**
   - Use SDK built-in authentication features (Web)
   - Understand natural login-free feature (Mini Program)
   - Configure appropriate database permissions
   - Use cloud functions for cross-collection operations

3. **Use correct SDKs and APIs**
   - Different platforms require different SDKs for data models
   - MySQL data models must use models SDK, not collection API
   - Use `envQuery` tool to get environment ID

4. **Use CloudBase MCP via mcporter (CLI) when IDE MCP is not available**
   - You do **not** need to hard-code Secret ID / Secret Key / Env ID in config
   - CloudBase MCP will support device-code login via the `auth` tool, so credentials can be obtained interactively
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

---

# CloudBase Platform Knowledge

## Storage and Hosting

1. **Static Hosting vs Cloud Storage**:
   - CloudBase static hosting and cloud storage are two different buckets
   - Generally, publicly accessible files can be stored in static hosting, which provides a public web address
   - Static hosting supports custom domain configuration (requires console operation)
   - Cloud storage is suitable for files with privacy requirements, can get temporary access addresses via temporary file URLs
   - If the task needs COS SDK polling, file metadata lookup, or temporary URLs for an uploaded object, use cloud storage tools (`manageStorage` / `queryStorage`), not `uploadFiles`

2. **Static Hosting Domain**:
   - CloudBase static hosting domain can be obtained via `getWebsiteConfig` tool
   - Combine with static hosting file paths to construct final access addresses
   - **Important**: If access address is a directory, it must end with `/`

## Environment and Authentication

1. **SDK Initialization**:
   - CloudBase SDK initialization requires environment ID
   - Can query environment ID via `envQuery` tool
   - For Web, always initialize synchronously:
     - `import cloudbase from "@cloudbase/js-sdk"; const app = cloudbase.init({ env: "xxxx-yyy" });`
     - Do **not** use dynamic imports like `import("@cloudbase/js-sdk")` or async wrappers such as `initCloudBase()` with internal `initPromise`
   - Then proceed with login, for example using anonymous login

## Authentication Best Practices

**Important: Authentication methods for different platforms are completely different, must strictly distinguish!**

### Web Authentication
- **Must use SDK built-in authentication**: CloudBase Web SDK provides complete authentication features
- **Recommended method**: SMS login with `auth.getVerification()`, for detailed, refer to web auth related docs
- **Forbidden behavior**: Do not use cloud functions to implement login authentication logic
- **User management**: After login, get user information via `auth.getCurrentUser()`

### Mini Program Authentication
- **Login-free feature**: Mini program CloudBase is naturally login-free, no login flow needed
- **User identifier**: In cloud functions, get `wxContext.OPENID` via wx-server-sdk
- **User management**: Manage user data in cloud functions based on openid
- **Forbidden behavior**: Do not generate login pages or login flow code

## Cloud Functions

1. **Node.js Cloud Functions**:
   - Node.js cloud functions need to include `package.json`, declaring required dependencies
   - Can use `manageFunctions(action="createFunction")` to create functions
   - Use `manageFunctions(action="updateFunctionCode")` to deploy cloud functions
   - Prioritize cloud dependency installation, do not upload node_modules
   - `functionRootPath` refers to the parent directory of function directories, e.g., `cloudfunctions` directory

## Database Permissions

**⚠️ CRITICAL: Always configure permissions BEFORE writing database operation code!**

1. **Permission Model**:
   - CloudBase database access has permissions
   - Default basic permissions include:
     - **READONLY**: Everyone can read, only creator/admin can write
     - **PRIVATE**: Only creator/admin can read/write
     - **ADMINWRITE**: Everyone can read, **only admin can write** (⚠️ NOT for Web SDK write!)
     - **ADMINONLY**: Only admin can read/write
     - **CUSTOM**: Fine-grained control with custom rules

2. **Platform Compatibility** (CRITICAL):
   - ⚠️ **Web SDK cannot use `ADMINWRITE` or `ADMINONLY` for write operations**
   - ✅ For user-generated content in Web apps, use **CUSTOM** rules
   - ✅ For admin-managed data (products, settings), use **READONLY**
   - ✅ Cloud functions have full access regardless of permission type

3. **Configuration Workflow**:
   ```
   Create collection → Configure security rules → Write code → Test
   ```
   - Use `writeSecurityRule` MCP tool to configure permissions
   - Wait 2-5 minutes for cache to clear before testing
   - See `no-sql-web-sdk/security-rules.md` for detailed examples

4. **Common Scenarios**:
   - **E-commerce products**: `READONLY` (admin manages via cloud functions)
   - **Shopping carts**: `CUSTOM` with `auth.uid` check (users manage their own)
   - **Orders**: `CUSTOM` with ownership validation
   - **System logs**: `PRIVATE` or `ADMINONLY`

5. **Cross-Collection Operations**:
   - If user has no special requirements, operations involving cross-database collections must be implemented via cloud functions

3. **Cloud Function Optimization**:
   - If involving cloud functions, while ensuring security, can minimize the number of cloud functions as much as possible
   - For example: implement one cloud function for client-side requests, implement one cloud function for data initialization

## Data Models

1. **Get Data Model Operation Object**:
   - **Mini Program**: Need `@cloudbase/wx-cloud-client-sdk`, initialize `const client = initHTTPOverCallFunction(wx.cloud)`, use `client.models`
   - **Cloud Function**: Need `@cloudbase/node-sdk@3.10+`, initialize `const app = cloudbase.init({env})`, use `app.models`
   - **Web**: Need `@cloudbase/js-sdk`, initialize `const app = cloudbase.init({env})`, after login use `app.models`

2. **Data Model Query**:
   - Can call MCP `manageDataModel` tool to:
     - Query model list
     - Get model detailed information (including Schema fields)
     - Get specific models SDK usage documentation

3. **MySQL Data Model Invocation Rules**:
   - MySQL data models cannot use collection method invocation, must use data model SDK
   - **Wrong**: `db.collection('model_name').get()`
   - **Correct**: `app.models.model_name.list({ filter: { where: {} } })`
   - Use `manageDataModel` tool's `docs` method to get specific SDK usage

## Console Management

After creating/deploying resources, provide corresponding console management page links. All console URLs follow the pattern: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/{path}`

### Core Function Entry Points

1. **Overview (概览)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/overview`
   - Main dashboard showing environment status, resource usage, and quick access to key features
   - Displays overview of all CloudBase services and their status

2. **Template Center (模板中心)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/template`
   - Access project templates for React, Vue, Mini Program, UniApp, and backend frameworks
   - AI Builder templates for rapid application generation
   - Framework templates: React, Vue, Miniapp, UniApp, Gin, Django, Flask, SpringBoot, Express, NestJS, FastAPI

3. **Document Database (文档型数据库)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/db/doc`
   - Manage NoSQL document database collections
   - **Collection Management**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/db/doc/collection/${collectionName}`
     - View, edit, and manage collection data
     - Configure security rules and permissions
   - **Data Model Management**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/db/doc/model/${modelName}`
     - Create and manage data models with relationships
     - View model schema and field definitions

4. **MySQL Database (MySQL 数据库)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/db/mysql`
   - Manage MySQL relational database
   - **Table Management**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/db/mysql/table/default/`
     - Create, modify, and manage database tables
     - Execute SQL queries and manage table structure
   - **Important**: Must enable MySQL database in console before use

5. **Cloud Functions (云函数)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/scf`
   - Manage and deploy Node.js cloud functions
   - **Function List**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/scf`
   - **Function Detail**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/scf/detail?id=${functionName}&NameSpace=${envId}`
     - View function code, logs, and configuration
     - Manage function triggers and environment variables
     - Monitor function invocations and performance

6. **CloudRun (云托管)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/cloudrun`
   - Manage containerized backend services
   - Deploy services using Function mode or Container mode
   - Configure service scaling, access types, and environment variables
   - View service logs and monitoring data

7. **Cloud Storage (云存储)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/storage`
   - Manage file storage buckets
   - Upload, download, and organize files
   - Configure storage permissions and access policies
   - Generate temporary access URLs for private files

8. **AI+**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/ai`
   - Access AI capabilities and services
   - AI Builder for generating templates and code
   - AI image recognition and other AI features

9. **Static Website Hosting (静态网站托管)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/hosting`
   - Deploy and manage static websites
   - Alternative URL: `https://console.cloud.tencent.com/tcb/hosting`
   - Configure custom domains and CDN settings
   - View deployment history and access logs

10. **Identity Authentication (身份认证)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/identity`
    - Configure authentication methods and user management
    - **Login Management**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/identity/login-manage`
      - Enable/disable login methods (SMS, Email, Username/Password, WeChat, Custom Login)
      - Configure SMS/Email templates
      - Manage security domain whitelist
    - **Token Management**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/identity/token-management`
      - Manage API Keys and Publishable Keys
      - View and manage access tokens

11. **Weida Low-Code (微搭低代码)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/weida`
    - Access Weida low-code development platform
    - Build applications using visual drag-and-drop interface

12. **Logs & Monitoring (日志监控)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/logs`
    - View logs from cloud functions, CloudRun services, and other resources
    - Monitor resource usage, performance metrics, and error rates
    - Set up alerts and notifications

13. **Environment Settings (环境配置)**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/settings`
    - Configure environment-level settings
    - Manage security domains and CORS settings
    - Configure environment variables and secrets
    - View environment information and resource quotas

### URL Construction Guidelines

- **Base URL Pattern**: `https://tcb.cloud.tencent.com/dev?envId=${envId}#/{path}`
- **Replace Variables**: Always replace `${envId}` with the actual environment ID queried via `envQuery` tool
- **Resource-Specific URLs**: For specific resources (collections, functions, models), replace resource name variables with actual values
- **Usage**: After creating/deploying resources, provide these console links to users for management operations

### Quick Reference

When directing users to console pages:
- Use the full URL with environment ID
- Explain what they can do on each page
- Provide context about why they need to access that specific page
- For configuration pages (like login management), guide users through the setup process
