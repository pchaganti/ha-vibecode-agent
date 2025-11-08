# Changelog

All notable changes to this project will be documented in this file.

## [1.0.9] - 2025-11-08

### 🔒 Security & UX Improvements

**Breaking Change:** API authentication changed from Home Assistant Long-Lived Token to dedicated API Key.

### Added
- **Dedicated API Key system** - separate from HA tokens
  - Auto-generates secure API key (32 bytes, cryptographically secure)
  - Optional: set custom API key in add-on configuration
  - Stored in `/config/.ha_cursor_agent_key`
- **Ingress Panel** - beautiful web UI in Home Assistant sidebar
  - Shows current API key (masked by default, click to reveal)
  - Copy to clipboard button
  - Step-by-step setup instructions
  - Direct links to documentation
- **Optional notifications** - get notified when API key is generated
  - Configurable in add-on settings

### Changed
- **Authentication simplified** - no need to create HA Long-Lived Token
- **Ingress enabled** - panel appears in sidebar as "API Key"
- **Panel icon** changed to `mdi:key-variant`
- Agent now uses dedicated API key instead of user's HA token
- Agent still uses SUPERVISOR_TOKEN internally for HA API operations

### Security
- ✅ No more transmitting HA Long-Lived Token over network
- ✅ API key is independent from HA authentication
- ✅ Can regenerate key without affecting HA access
- ✅ Simpler security model

### Migration
If upgrading from v1.0.8 or earlier:
1. Update add-on to v1.0.9
2. Open Sidebar → API Key (new panel will appear)
3. Copy your new API key
4. Update `~/.cursor/mcp.json` with new key
5. Restart Cursor

Old HA tokens will no longer work (this is intentional for security).

## [1.0.8] - 2025-11-08

### Added
- **CLIMATE_CONTROL_BEST_PRACTICES.md** - Comprehensive guide with 10+ real-world edge cases
  - TRV state changes during cooldown (with solution)
  - Sensor update delay after state changes (10 second rule)
  - Minimum boiler runtime protection (buffer radiators)
  - Predictive shutdown timing (0.3°C threshold)
  - Adaptive cooldown duration based on runtime
  - Multiple trigger automations for reliability
  - State tracking with input helpers
  - Buffer radiators coordination
  - System enable/disable transitions
  - Periodic check as safety net
- **Climate Control section in AI Instructions:**
  - Mandatory checklist for TRV/boiler automations
  - Critical edge cases to handle
  - Required sensors and helpers
  - Core automations (Priority 1, 2, 3)
  - Timing guidelines
  - Common mistakes to avoid
  - Testing checklist

### Documentation
- Added comprehensive climate control best practices based on production testing
- Real-world performance data (7+ days continuous operation)
- Architecture patterns for state-based automations
- Golden rules for reliable automation
- Lessons applicable to ANY state-based automation system

### Impact
- AI agents will now implement climate control with proven edge case handling
- Prevents common failures (stuck states, missed triggers, short-cycling)
- Saves debugging time by implementing solutions from day one
- Applicable to other automation systems beyond climate control

## [1.0.7] - 2025-11-08

### Changed
- **AI-controlled reload workflow:** Files API no longer auto-reloads after writes
  - Safer: AI must explicitly check config validity before reload
  - Faster: Batch multiple changes → single reload at the end
  - More control: AI decides when to reload based on change scope

### Added
- **Comprehensive modification workflow in AI Instructions:**
  - 6-step process: Backup → Write → Check → Reload → Verify → Commit
  - Configuration validation before reload (prevents broken HA state)
  - Rollback guidance if validation fails
  - Example workflows for common scenarios

### Fixed
- **Safety improvement:** Removed automatic reload that could apply invalid configurations
- **Performance:** No more multiple reloads when making batch changes

## [1.0.6] - 2025-11-08

### Changed
- **Updated documentation for MCP integration** - New recommended way to connect Cursor AI
- Added link to [@coolver/mcp-home-assistant](https://www.npmjs.com/package/@coolver/mcp-home-assistant) NPM package
- Simplified connection instructions using Model Context Protocol
- Updated README with MCP badge and links

### Documentation
- Replaced old prompt-based connection method with MCP configuration
- Added step-by-step MCP setup guide
- Added examples of natural language usage with MCP

## [1.0.5] - 2025-11-08

### Added
- **GET /api/helpers/list** endpoint to list all input helpers
- Better agent logs support with level filtering (DEBUG, INFO, WARNING, ERROR)

### Changed
- Improved MCP client logs handling with proper parameter names (limit, level)
- Updated tool descriptions for better clarity

## [1.0.4] - 2025-11-08

### Fixed
- **Token validation in add-on mode:** Fixed "Invalid token" errors when using Long-Lived Access Tokens
- Agent no longer tries to validate user tokens through supervisor URL (which doesn't accept them)
- In add-on mode, agent simply checks that a token is provided and uses SUPERVISOR_TOKEN for HA API operations

### Changed
- Simplified token validation logic for better reliability
- Improved token validation logging

## [1.0.3] - 2025-11-08

### Added
- **Enhanced debugging:** Detailed logging for token configuration at startup
- **Token validation logging:** Logs token validation attempts with response details
- **HA API request logging:** Logs all HA API requests with token preview
- **HAClient initialization logging:** Shows which token source is being used
- **Success/failure indicators:** Visual ✅/❌ indicators in logs

### Changed
- Version bumped to 1.0.3
- Improved error messages with token context for easier debugging

### Fixed
- Made "Invalid token" errors much easier to diagnose with detailed logging
- Added visibility into SUPERVISOR_TOKEN vs DEV_TOKEN usage

## [1.0.1] - 2024-11-07

### Fixed
- Fixed Docker base images to use correct Python 3.12-alpine3.20 versions
- Now builds successfully on Raspberry Pi (aarch64, armv7) and all other architectures
- Resolved "base image not found" error during add-on installation

### Added
- Cursor AI integration guide in README with ready-to-use prompt templates
- Example use cases for autonomous Home Assistant management
- Proper Cursor branding icons (icon.png, logo.png)

### Changed
- Removed unnecessary GitHub Actions builder workflow  
- Cleaned up documentation (removed redundant files)
- Integrated Quick Start guide directly into README
- Updated to multi-architecture support with build.json

## [1.0.0] - 2024-11-07

### Added
- Initial release of HA Cursor Agent
- FastAPI REST API with 29 endpoints
- File management (read/write/list/append/delete)
- Home Assistant integration (entities, services, reloads)
- Component management (helpers, automations, scripts)
- Git versioning with automatic backups
- Rollback functionality
- Agent logs API
- Health check endpoint
- Swagger UI documentation (`/docs`)
- Multi-architecture Docker support
- Home Assistant Add-on configuration

### Features
- **Files API**: Manage configuration files
- **Entities API**: Query devices and entities
- **Helpers API**: Create/delete input helpers
- **Automations API**: Manage automations
- **Scripts API**: Manage scripts
- **System API**: Reload components, check config
- **Backup API**: Git commit, history, rollback
- **Logs API**: Agent operation logs

### Documentation
- README with installation guide
- DOCS with full API reference
- INSTALLATION guide
- Quick Start guide
- Changelog
