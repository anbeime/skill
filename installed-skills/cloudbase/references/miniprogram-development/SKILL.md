---
name: miniprogram-development
description: WeChat Mini Program development skill for building, debugging, previewing, testing, publishing, and optimizing mini program projects. This skill should be used when users ask to create, develop, modify, debug, preview, test, deploy, publish, launch, review, or optimize WeChat Mini Programs, mini program pages, components, routing, project structure, project configuration, project.config.json, appid setup, device preview, real-device validation, WeChat Developer Tools workflows, miniprogram-ci preview/upload flows, or mini program release processes. It should also be used when users explicitly mention CloudBase, wx.cloud, Tencent CloudBase, 腾讯云开发, or 云开发 in a mini program project.
alwaysApply: false
---

## Activation Contract

### Use this first when

- The request is about WeChat Mini Program structure, pages, preview, publishing, or CloudBase mini program integration.

### Read before writing code if

- The user mentions `wx.cloud`, CloudBase mini programs, OPENID, or mini program deployment/debug workflows.

### Then also read

- CloudBase auth -> `../auth-wechat/SKILL.md`
- CloudBase document DB -> `../no-sql-wx-mp-sdk/SKILL.md`
- UI generation -> `../ui-design/SKILL.md` first

### Do NOT use for

- Web auth flows or Web SDK-specific frontend implementation.

### Common mistakes / gotchas

- Generating a Web-style login flow for mini programs.
- Mixing Web SDK assumptions into `wx.cloud` projects.
- Applying CloudBase constraints before confirming the project actually uses CloudBase.

## When to use this skill

Use this skill for **WeChat Mini Program development** when you need to:

- Build or modify mini program pages and components
- Organize mini program project structure and configuration
- Debug, preview, or publish mini program projects
- Work with WeChat Developer Tools workflows
- Handle mini program runtime behavior, assets, or page config files
- Integrate CloudBase in a mini program project when explicitly needed

**Do NOT use for:**
- Web frontend development (use `web-development`)
- Pure backend service development (use `cloudrun-development` or `cloud-functions` as appropriate)
- UI design-only tasks without mini program development context (use `ui-design`)

---

## How to use this skill (for a coding agent)

1. **Start with the general mini program workflow**
   - Treat WeChat Mini Program development as the default scope
   - Do not assume the project uses CloudBase unless the user or codebase indicates it

2. **Follow mini program project conventions**
   - Keep mini program source under the configured mini program root
   - Ensure page files include the required configuration file such as `index.json`
   - Check `project.config.json` before suggesting preview or IDE workflows

3. **Route by scenario**
   - If the task involves CloudBase, `wx.cloud`, cloud functions, CloudBase database/storage, or CloudBase identity handling, read [CloudBase integration reference](references/cloudbase-integration.md)
   - If the task involves debugging, previewing, publishing, WeChat Developer Tools, or no-DevTools workflows, read [debug and preview reference](references/devtools-debug-preview.md)

4. **Use CloudBase rules only when applicable**
   - CloudBase is an important mini program integration path, but not a universal requirement
   - Only apply CloudBase-specific auth, database, storage, or cloud function constraints when the project is using CloudBase

5. **Recommend the right preview/debug path**
   - Prefer WeChat Developer Tools for simulator, panel-based debugging, preview, and real-device validation
   - If WeChat Developer Tools is unavailable, use `miniprogram-ci` for preview, upload, and npm build workflows where appropriate

---

# WeChat Mini Program Development Rules

## General Project Rules

1. **Project Structure**
   - Mini program code should follow the project root configured in `project.config.json`
   - Keep page-level files complete, including `.json` configuration files
   - Ensure referenced local assets actually exist to avoid compile failures

2. **Configuration Checks**
   - Check `project.config.json` before opening, previewing, or publishing a project
   - Confirm `appid` is available when a real preview, upload, or WeChat Developer Tools workflow is required
   - Confirm `miniprogramRoot` and related path settings are correct

3. **Resource Handling**
   - When generating local asset references such as icons, ensure the files are downloaded into the project
   - Keep file paths stable and consistent with mini program config files

## CloudBase as a Mini Program Sub-Scenario

- If the user explicitly uses CloudBase, `wx.cloud`, Tencent CloudBase, 腾讯云开发, or 云开发, follow the CloudBase integration reference
- In CloudBase mini program projects, use `wx.cloud` APIs and CloudBase environment configuration appropriately
- Do not apply CloudBase-specific rules to non-CloudBase mini program projects

## Debugging, Preview, and Publishing

- If WeChat Developer Tools is available, use it as the primary path for simulator debugging, panel inspection, preview, and device validation
- If WeChat Developer Tools is not available, use `miniprogram-ci` as the fallback path for preview, upload, and npm build-related automation
- For detailed workflows, read [debug and preview reference](references/devtools-debug-preview.md)

## References

- [CloudBase Mini Program Integration](references/cloudbase-integration.md) — use this when the mini program project explicitly integrates CloudBase
- [WeChat DevTools Debug and Preview](references/devtools-debug-preview.md) — use this for debugging, preview, publishing, and no-DevTools fallback workflows
