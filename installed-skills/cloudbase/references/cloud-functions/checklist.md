# Cloud Functions Execution Checklist

Use this checklist before creating or updating a CloudBase function.

## Required checks

1. Decide whether this is an Event Function or an HTTP Function.
   - Event Function: `exports.main(event, context)`, SDK/timer driven
   - HTTP Function: `req` / `res`, listens on port `9000`
2. Pick the runtime before creation and state it explicitly.
3. For HTTP Functions, confirm `scf_bootstrap` exists and the service listens on port `9000`.
4. Confirm the function root path points to the parent directory, not the function directory itself.
5. If the request is really for a long-running container service, reroute to `cloudrun-development`.

## Common failure patterns

- Choosing the wrong function type and compensating later.
- Mixing Event Function and HTTP Function handler shapes in the same implementation.
- Forgetting that runtime cannot be changed after creation.
- Treating Cloud Functions as the default answer for Web authentication.

## Done criteria

- Function type and runtime are explicit.
- Packaging constraints are checked.
- The task is confirmed to be a function workflow rather than CloudRun.
