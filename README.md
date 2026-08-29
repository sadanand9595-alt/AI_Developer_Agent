# AI Command Center

Production-grade autonomous AI agent platform.

## Purpose

AI Command Center is designed to understand user requests, create execution plans, select appropriate agents and tools, execute tasks, validate results, and perform controlled self-correction.

The system is designed to operate independently from GEETA AI IDE.

GEETA integration will be added later through a dedicated connector/API/MCP interface.

## Core Workflow

User
    ↓
Command Center
    ↓
Planner
    ↓
Agent Router
    ↓
Agent
    ↓
Tools / MCP
    ↓
Permission Check
    ↓
Execution
    ↓
Validation
    ↓
Self-Correction
    ↓
Final Result

## Self-Coding Workflow

The development agent will be capable of:

1. Understand the requested task
2. Inspect the workspace
3. Create an implementation plan
4. Write or modify code
5. Run tests
6. Read errors
7. Diagnose failures
8. Apply controlled fixes
9. Run tests again
10. Validate the final result

Maximum retry attempts are controlled by configuration.

## Safety Rules

The agent must not blindly execute dangerous operations.

Human approval is required for:

- Production deployment
- Destructive database operations
- File deletion outside the allowed workspace
- Secret changes
- External write operations
- Payment or financial actions
- Security-sensitive changes

## Architecture

### Applications

- `apps/api` — API and Command Center backend
- `apps/worker` — Background agent execution
- `apps/web` — Web dashboard

### Core Modules

- `core`
- `agents`
- `planner`
- `router`
- `tools`
- `mcp`
- `rag`
- `memory`
- `security`
- `execution`
- `validation`
- `database`
- `integrations`
- `observability`

## Development Rules

1. Architecture must be reviewed before implementation.
2. Files are created sequentially.
3. Existing working files must not be regenerated unnecessarily.
4. Every major implementation must pass validation before proceeding.
5. Tests must be added for production functionality.
6. Secrets must never be committed.
7. Agents must operate within explicit permissions.
8. Self-correction must have retry limits.
9. Destructive operations require approval.
10. GEETA integration remains isolated until the Command Center is stable.

## Project Status

Current stage:

Foundation

Next:

Core configuration and application bootstrap.