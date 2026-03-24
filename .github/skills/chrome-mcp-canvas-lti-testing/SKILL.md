---
name: chrome-mcp-canvas-lti-testing
description: "Use when validating this Canvas LTI 1.3 tool through an authenticated Canvas browser session via Chrome MCP remote debugging. Triggers: Chrome MCP, Canvas LTI launch testing, forwarded URL changes, beta/test/dev Canvas environments, direct launch UX testing outside Canvas iframe."
---

# Chrome MCP Canvas LTI 1.3 Testing Skill

## Purpose
Use this skill to test and navigate the local Instructor Tools app as a Canvas LTI 1.3 tool by attaching to an already-authenticated Chrome session and launching the tool directly (not inside the Canvas iframe shell).

## 1. Context Summary
- This project is a local Canvas LTI 1.3 app exposed through a temporary port-forwarded HTTPS URL.
- The human developer is responsible for all Canvas SSO/Okta authentication steps.
- The agent uses Chrome MCP against a remote-debuggable Chrome session where Canvas auth is already active.
- UI testing is performed on the directly launched tool page, not inside Canvas course navigation iframe chrome.

## 2. Pre-Flight Checklist (User Actions)
The user must complete all of these before agent-driven UI testing:

1. Start the local backend stack.
- Recommended for this repo:
```bash
docker-compose down
docker-compose build
docker-compose up
```

2. Start a port-forwarding service and obtain an HTTPS public URL.
- Any tunnel provider is acceptable.
- Keep the local app target mapped to the running backend.

3. Update Canvas LTI Developer Key configuration with the new forwarded URL.
- Update Redirect URIs to include the forwarded launch URL(s).
- Update Target Link URI to the forwarded launch URI.
- Keep OIDC Initiation URL aligned with the same forwarded origin.

4. Launch Chrome with remote debugging enabled.
- Example (macOS):
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-canvas-mcp
```

5. Ensure Canvas session is already authenticated and ready
- Complete all login, MFA, and account selection steps manually.
- Use your configured Canvas environment (test, beta, or dev/prod equivalent for your institution).

6. In chrome instance, begin a successful LTI launch of the app in the course of your choice

## 3. Initialization Protocol (Agent Actions)
This is mandatory and must happen first in every testing session using this skill.

1. First action requirement:
- Ask exactly: "What is your current port-forwarded URL?"

2. URL capture requirement:
- Wait for user response.
- Explicitly acknowledge the received value.
- Store it in session context as the canonical base URL for all generated links and checks during the session.
- Treat the provided value as the exact launch URL; do not append `/lti/login/`, `/lti/launch/`, or any other path unless the user explicitly asks.
- If the user later provides a new forwarded URL, replace the stored value and rebase all launch/config guidance.

## 4. Canvas LTI 1.3 + Environment Notes (Research-Based)
Use these facts while debugging launch/config issues:

- LTI 1.3 launch flow is OIDC initiated login plus signed id_token launch.
- Required LTI launch claims include message_type (LtiResourceLinkRequest), version (1.3.0), deployment_id, target_link_uri, and roles.
- Canvas uses environment-specific OIDC/JWKS infrastructure for cloud environments.
- Canvas documentation lists environment-specific JWKS endpoints:
  - Production: https://sso.canvaslms.com/api/lti/security/jwks
  - Beta: https://sso.beta.canvaslms.com/api/lti/security/jwks
  - Test: https://sso.test.canvaslms.com/api/lti/security/jwks
- Canvas LTI 1.3 tooling does not use the old LTI 1.1 environments config switch; environment routing should be handled by the LTI/OIDC request context (including canvas_environment behavior) and correct registration data.
- Canvas test environment data is overwritten from production on a recurring schedule (commonly every third Saturday per Canvas docs).
- If an institution has a separate dev environment, treat it as its own issuer/domain and ensure registration values exactly match that environment.

## 5. Project-Specific LTI Configuration Notes (PyLTI1p3)
This repository uses PyLTI1p3 Django integration and stores tool config in DB-backed models.

- LTI endpoints in this app:
  - /lti/login/
  - /lti/launch/
  - /lti/jwks/
  - /lti/config/
- The code uses DjangoOIDCLogin and DjangoMessageLaunch (with cookie-check helper and cache-backed launch storage).
- Tool and key persistence is managed via PyLTI1p3 DB models (LtiTool, LtiToolKey).
- Repo command for maintaining tool/key rows:
```bash
docker exec -it instructor_tools python manage.py manage_pylti \
  --platform <canvas-platform-domain> \
  --client_id <canvas_client_id> \
  --title "Instructor Tools" \
  --tool_key <key_name> \
  --deployment_ids <deployment_id_1> <deployment_id_2>
```
- This command writes/updates issuer/client/tool key/deployment mappings used by launch validation.

## 6. Connection & Direct Launch Protocol
After pre-flight and initialization are complete, execute this flow:

1. Attach to Chrome MCP against the existing remote debugging browser instance.
2. Reuse the tab/session where Canvas is already authenticated.
3. Launch from the stored forwarded URL exactly as provided by the user.
- Do not add or alter path segments.
- Example: if user provides `https://jkrooss-it.loophole.site`, navigate to exactly that URL.

4. Navigate to that exact forwarded URL in the authenticated browser context.
- This should follow OIDC redirects through Canvas and return to the tool.
- Do not require testing inside Canvas iframe unless user explicitly asks.

5. Validate final loaded page origin is the forwarded tool domain and that expected app routes/components render.

## 6.1 Recovery Path: Missing OIDC/Canvas Session Context
If direct navigation to the forwarded URL or `/lti/login/` yields errors such as `Could not find issuer`, Django login pages, or Canvas/OIDC dead-end redirects, do not continue blind retries.

Use this deterministic recovery flow:

1. Agent instruction: Do not attempt any recovery navigation or launch actions in Canvas for this flow.
2. User-only action: In the same Chrome remote-debugging instance, manually log into the target Canvas environment (user performs auth/MFA).
3. User-only action: From within Canvas UI, navigate to the correct course/context and launch the installed LTI tool at least once.
4. User-only action: Confirm the tool successfully renders in that browser profile.
5. Agent instruction: Wait for explicit user confirmation that steps 2-4 are complete before taking any further navigation or UX test action.
6. After explicit user confirmation, re-run the agent's direct navigation and UX test steps.

Rationale:
- Canvas-initiated launch establishes the correct OIDC/LTI request context and session linkage required by PyLTI1p3 validation.
- Retrying the forwarded URL without this context can repeatedly produce issuer/claim validation errors.

## 7. UX Testing Boundaries
When using this skill, testing scope is intentionally narrow and concrete:

- In scope:
  - DOM-level validation of the directly launched app.
  - Clicking links/buttons, filling fields, and observing UI state transitions.
  - Capturing visible errors, permission failures, missing data states, and regressions.
  - Reporting concise visual/functional findings and likely cause hypotheses.

- Out of scope by default:
  - Performing user credential entry, Duo pushes, or SSO steps.
  - Changing institutional Canvas settings without explicit user request.
  - Treating Canvas shell/iframe chrome as the primary UX under test.

## 8. Agent Reporting Format
For each run, report:

1. Stored forwarded base URL used for the run.
2. Canvas environment inferred from URLs or launch behavior (test/beta/dev/prod-like).
3. Launch result:
- success/failure
- last successful URL reached
- any blocking error text
4. UX findings from direct app DOM interactions.
5. Recommended next fix/check, prioritized by likely impact.

## 9. Safety and Reliability Rules
- Never ask the user for passwords, MFA codes, or secrets.
- If launch fails with registration or claim mismatch, request only non-secret config values (issuer, client_id, deployment_id, target_link_uri, redirect URI).
- If the forwarded URL changes mid-session, stop and rebase all URLs/config assumptions immediately.
- Prefer deterministic repro steps over one-off clicks; always include exact path and action sequence in findings.
- When missing issuer/session-context errors appear, explicitly instruct the user to authenticate Canvas and launch the tool from Canvas first in the same debug browser profile, then retry.
