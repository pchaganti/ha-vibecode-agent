# 🧪 Home Assistant Agent - Comprehensive Test Suite

**Version:** 2.7.7  
**Purpose:** Complete testing of all HA Cursor Agent MCP functions  
**Usage:** Say "запусти тест Home Assistant Agent" to run full suite

---

## 📋 Test Categories

- [Files](#1-file-operations-4-tests) (4 tests)
- [Entities](#2-entity-operations-2-tests) (2 tests)
- [Helpers](#3-helper-operations-2-tests) (2 tests)
- [Automations](#4-automation-operations-2-tests) (2 tests)
- [Scripts](#5-script-operations-2-tests) (2 tests)
- [Git/Backup](#6-gitbackup-operations-4-tests) (4 tests)
- [System](#7-system-operations-4-tests) (4 tests)
- [HACS](#8-hacs-operations-8-tests) (8 tests)
- [Add-ons](#9-add-on-operations-13-tests) (13 tests)
- [Dashboards](#10-dashboard-operations-4-tests) (4 tests)
- [Repositories](#11-repository-operations-2-tests) (2 tests)
- [Logbook](#12-logbook-operations-1-test) (1 test)

**Total:** 48 tests

---

## Test Execution Instructions

### How to Run

1. **Full Suite:** "запусти тест Home Assistant Agent"
2. **Category:** "запусти тесты [Files/Entities/Helpers/...]"
3. **Single Test:** "запусти тест [test_name]"

### Success Criteria

✅ **PASS:** Function returns expected data/success message  
❌ **FAIL:** Error, timeout, or unexpected response  
⚠️ **SKIP:** Test cannot run (missing dependencies, etc.)

### Test Output Format

```
✅ test_read_configuration_yaml - PASS (125ms)
   Response: File content retrieved successfully
   
❌ test_create_invalid_helper - FAIL (50ms)
   Error: Invalid helper configuration
   Expected: Validation error message
   
⚠️ test_hacs_install - SKIP
   Reason: HACS not installed
```

---

## 1. File Operations (4 tests)

### test_list_files_root
**Function:** `ha_list_files`  
**Parameters:** `{ directory: "/" }`  
**Expected:** List of files in root directory  
**Success:** Returns array with files like `configuration.yaml`, `automations.yaml`

### test_read_configuration_yaml
**Function:** `ha_read_file`  
**Parameters:** `{ path: "configuration.yaml" }`  
**Expected:** File content as string  
**Success:** Returns YAML content starting with `default_config:`

### test_write_and_read_test_file
**Function:** `ha_write_file` then `ha_read_file`  
**Steps:**
1. Write: `{ path: "test_agent.txt", content: "Test from HA Agent" }`
2. Read: `{ path: "test_agent.txt" }`  
**Expected:** Read returns written content  
**Cleanup:** Delete test file after

### test_delete_test_file
**Function:** `ha_delete_file`  
**Parameters:** `{ path: "test_agent.txt" }`  
**Expected:** File deleted successfully  
**Success:** Subsequent read fails with "not found"

---

## 2. Entity Operations (2 tests)

### test_list_all_entities
**Function:** `ha_list_entities`  
**Parameters:** `{}`  
**Expected:** Array of all entities  
**Success:** Returns entities with `entity_id`, `state`, `attributes`

### test_list_climate_entities
**Function:** `ha_list_entities`  
**Parameters:** `{ domain: "climate" }`  
**Expected:** Array of climate entities only  
**Success:** All returned entities start with `climate.`

### test_get_entity_state
**Function:** `ha_get_entity_state`  
**Parameters:** `{ entity_id: "sun.sun" }`  
**Expected:** Entity state object  
**Success:** Returns state (`above_horizon` or `below_horizon`)

---

## 3. Helper Operations (2 tests)

### test_list_helpers
**Function:** `ha_list_helpers`  
**Parameters:** `{}`  
**Expected:** List of existing helpers  
**Success:** Returns array (may be empty)

### test_create_input_boolean_helper
**Function:** `ha_create_helper`  
**Parameters:**
```json
{
  "type": "input_boolean",
  "config": {
    "name": "Test Agent Helper",
    "icon": "mdi:test-tube"
  }
}
```
**Expected:** Helper created successfully  
**Success:** Helper appears in list, entity_id exists  
**Cleanup:** Delete helper after test

---

## 4. Automation Operations (2 tests)

### test_list_automations
**Function:** `ha_list_automations`  
**Parameters:** `{}`  
**Expected:** List of automations  
**Success:** Returns array with automation objects

### test_create_test_automation
**Function:** `ha_create_automation`  
**Parameters:**
```json
{
  "config": {
    "id": "test_agent_automation",
    "alias": "Test Agent Automation",
    "trigger": [
      {
        "platform": "state",
        "entity_id": "sun.sun"
      }
    ],
    "action": [
      {
        "service": "notify.persistent_notification",
        "data": {
          "message": "Test from Agent"
        }
      }
    ]
  }
}
```
**Expected:** Automation created  
**Success:** Automation appears in list  
**Cleanup:** Delete automation after

---

## 5. Script Operations (2 tests)

### test_list_scripts
**Function:** `ha_list_scripts`  
**Parameters:** `{}`  
**Expected:** List of scripts  
**Success:** Returns array (may be empty)

### test_create_test_script
**Function:** `ha_create_script`  
**Parameters:**
```json
{
  "config": {
    "test_agent_script": {
      "alias": "Test Agent Script",
      "sequence": [
        {
          "service": "notify.persistent_notification",
          "data": {
            "message": "Test script executed"
          }
        }
      ]
    }
  }
}
```
**Expected:** Script created  
**Success:** Script appears in list  
**Cleanup:** Delete script after

---

## 6. Git/Backup Operations (4 tests)

### test_git_history
**Function:** `ha_git_history`  
**Parameters:** `{ limit: 5 }`  
**Expected:** Last 5 commits  
**Success:** Returns array with commit objects (hash, message, date)

### test_git_commit
**Function:** `ha_git_commit`  
**Parameters:** `{ message: "Test commit from HA Agent" }`  
**Expected:** Commit created  
**Success:** Returns commit hash

### test_git_diff_last_two_commits
**Function:** `ha_git_diff`  
**Steps:**
1. Get history to find last 2 commit hashes
2. Call `ha_git_diff` with those hashes  
**Expected:** Diff between commits  
**Success:** Returns diff text

### test_git_rollback_and_restore
**Function:** `ha_git_rollback`  
**Steps:**
1. Note current commit hash
2. Rollback to previous commit
3. Verify rollback
4. Rollback back to original  
**Expected:** Successful rollback and restore  
**Success:** System returns to original state

---

## 7. System Operations (4 tests)

### test_check_config
**Function:** `ha_check_config`  
**Parameters:** `{}`  
**Expected:** Configuration validation result  
**Success:** Returns `valid: true` or list of errors

### test_get_logs
**Function:** `ha_get_logs`  
**Parameters:** `{ limit: 10 }`  
**Expected:** Last 10 log entries  
**Success:** Returns array of log entries

### test_reload_config_core
**Function:** `ha_reload_config`  
**Parameters:** `{ component: "core" }`  
**Expected:** Core config reloaded  
**Success:** Returns success message  
**Note:** Does NOT restart HA

### test_health_check
**Function:** Direct API call to `/api/health`  
**Expected:** Health status  
**Success:** Returns `{ status: "ok", version, git_enabled }`

---

## 8. HACS Operations (8 tests)

### test_hacs_status
**Function:** `ha_hacs_status`  
**Parameters:** `{}`  
**Expected:** HACS installation status  
**Success:** Returns installed/not installed status

### test_install_hacs
**Function:** `ha_install_hacs`  
**Parameters:** `{}`  
**Expected:** HACS installed  
**Success:** HACS appears in integrations  
**Note:** Only run if not installed

### test_hacs_list_repositories
**Function:** `ha_hacs_list_repositories`  
**Parameters:** `{}`  
**Expected:** List of available HACS repos  
**Success:** Returns array of repositories  
**Prerequisite:** HACS installed

### test_hacs_search_integration
**Function:** `ha_hacs_search`  
**Parameters:**
```json
{
  "query": "xiaomi",
  "category": "integration"
}
```
**Expected:** Search results  
**Success:** Returns repos matching query  
**Prerequisite:** HACS installed

### test_hacs_repository_details
**Function:** `ha_hacs_repository_details`  
**Parameters:** `{ repository_id: "hacs/integration" }`  
**Expected:** Detailed repo info  
**Success:** Returns stars, authors, version  
**Prerequisite:** HACS installed

### test_hacs_install_repository
**Function:** `ha_hacs_install_repository`  
**Parameters:**
```json
{
  "repository": "test/repo",
  "category": "integration"
}
```
**Expected:** Repository installed  
**Success:** Repo appears in installed list  
**Note:** Use test repo or skip  
**Cleanup:** Uninstall after

### test_hacs_update_all
**Function:** `ha_hacs_update_all`  
**Parameters:** `{}`  
**Expected:** All HACS repos updated  
**Success:** Returns update results  
**Note:** May take several minutes

### test_uninstall_hacs
**Function:** `ha_uninstall_hacs`  
**Parameters:** `{}`  
**Expected:** HACS uninstalled  
**Success:** HACS removed from integrations  
**Note:** Only run in test environment

---

## 9. Add-on Operations (13 tests)

### test_list_store_addons
**Function:** `ha_list_store_addons`  
**Parameters:** `{}`  
**Expected:** All available add-ons from store  
**Success:** Returns large array with all store add-ons

### test_list_available_addons
**Function:** `ha_list_addons`  
**Parameters:** `{}`  
**Expected:** Available add-ons (limited list)  
**Success:** Returns array of add-ons

### test_list_installed_addons
**Function:** `ha_list_installed_addons`  
**Parameters:** `{}`  
**Expected:** Currently installed add-ons  
**Success:** Returns array (includes HA Cursor Agent)

### test_get_addon_info
**Function:** `ha_addon_info`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Detailed add-on information  
**Success:** Returns name, version, state, options

### test_get_addon_options
**Function:** `ha_get_addon_options`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on configuration options  
**Success:** Returns options object

### test_get_addon_logs
**Function:** `ha_addon_logs`  
**Parameters:** `{ slug: "core_mosquitto", lines: 20 }`  
**Expected:** Last 20 log lines  
**Success:** Returns log text

### test_install_addon
**Function:** `ha_install_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on installed  
**Success:** Add-on appears in installed list  
**Note:** Use lightweight add-on  
**Cleanup:** Uninstall after

### test_start_addon
**Function:** `ha_start_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on started  
**Success:** Add-on state changes to "started"  
**Prerequisite:** Add-on installed

### test_stop_addon
**Function:** `ha_stop_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on stopped  
**Success:** Add-on state changes to "stopped"

### test_restart_addon
**Function:** `ha_restart_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on restarted  
**Success:** Add-on restarts successfully

### test_set_addon_options
**Function:** `ha_set_addon_options`  
**Parameters:**
```json
{
  "slug": "core_mosquitto",
  "options": {
    "logins": [],
    "anonymous": true
  }
}
```
**Expected:** Options updated  
**Success:** Get options returns new values

### test_update_addon
**Function:** `ha_update_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on updated to latest version  
**Success:** Version updated (or already latest)  
**Note:** May take several minutes

### test_uninstall_addon
**Function:** `ha_uninstall_addon`  
**Parameters:** `{ slug: "core_mosquitto" }`  
**Expected:** Add-on uninstalled  
**Success:** Add-on removed from installed list  
**Note:** Only run after install test

---

## 10. Dashboard Operations (4 tests)

### test_analyze_entities_for_dashboard
**Function:** `ha_analyze_entities_for_dashboard`  
**Parameters:** `{}`  
**Expected:** Entity analysis for dashboard creation  
**Success:** Returns entities grouped by domain

### test_preview_existing_dashboard
**Function:** `ha_preview_dashboard`  
**Parameters:** `{}`  
**Expected:** Current dashboard configuration  
**Success:** Returns lovelace config or empty

### test_apply_dashboard
**Function:** `ha_apply_dashboard`  
**Parameters:**
```json
{
  "dashboard_config": {
    "title": "Test Dashboard",
    "views": [
      {
        "title": "Test View",
        "path": "test-view",
        "cards": [
          {
            "type": "markdown",
            "content": "Test from Agent"
          }
        ]
      }
    ]
  },
  "filename": "test-agent-dashboard.yaml",
  "register_dashboard": true,
  "create_backup": true
}
```
**Expected:** Dashboard created and registered  
**Success:** Dashboard file exists, appears in sidebar  
**Cleanup:** Delete dashboard after

### test_delete_dashboard
**Function:** `ha_delete_dashboard`  
**Parameters:**
```json
{
  "filename": "test-agent-dashboard.yaml",
  "remove_from_config": true,
  "create_backup": true
}
```
**Expected:** Dashboard deleted  
**Success:** Dashboard file removed, unregistered

---

## 11. Repository Operations (2 tests)

### test_list_addon_repositories
**Function:** `ha_list_repositories`  
**Parameters:** `{}`  
**Expected:** List of add-on repositories  
**Success:** Returns array with repository URLs

### test_add_and_remove_repository
**Function:** `ha_add_repository`  
**Parameters:**
```json
{
  "repository_url": "https://github.com/hassio-addons/repository"
}
```
**Expected:** Repository added  
**Success:** Repository appears in list  
**Cleanup:** May need manual removal

---

## 12. Logbook Operations (1 test)

### test_logbook_recent_scripts
**Function:** `ha_logbook_entries`  
**Parameters:**
```json
{
  "domains": ["script"],
  "lookback_minutes": 120,
  "limit": 25
}
```
**Expected:** Recent logbook entries for scripts plus summary info  
**Success:** Response includes `entries` array with script events and `summary.scripts` data

---

## 🎯 Test Execution Strategy

### Phase 1: Read-Only Tests (Safe)
- All list/get/analyze operations
- Config checking
- Log reading
- Entity queries

### Phase 2: Non-Destructive Writes (Safe)
- Create test files
- Git commits
- Create helpers/automations/scripts for testing

### Phase 3: Reversible Operations (Caution)
- Install/uninstall test add-ons
- Dashboard creation/deletion
- Git rollback (with restore)

### Phase 4: System Operations (Warning)
- Config reload
- Add-on start/stop
- HACS operations

### Phase 5: Destructive Operations (Skip in Production)
- HA restart
- HACS uninstall
- Repository modifications

---

## 📊 Test Metrics

Track these metrics during test execution:

- **Total Tests:** 48
- **Passed:** Count
- **Failed:** Count
- **Skipped:** Count
- **Execution Time:** Total duration
- **Coverage:** % of functions tested

---

## 🔧 Test Configuration

### Prerequisites
- Home Assistant running
- HA Cursor Agent installed and running
- MCP server connected
- Git initialized in /config
- Test mode recommended (not production)

### Environment Variables
```bash
HA_AGENT_URL=http://homeassistant.local:8099
HA_AGENT_KEY=<your-token>
```

### Cleanup After Tests
- Delete test files (`test_agent.txt`, etc.)
- Remove test helpers
- Remove test automations
- Remove test scripts
- Remove test dashboards
- Rollback to pre-test git commit (optional)

---

## 📝 Test Report Template

```markdown
# Test Execution Report

**Date:** YYYY-MM-DD HH:MM
**Version:** 2.7.7
**Environment:** Development/Production

## Summary
- Total: 48
- Passed: XX
- Failed: XX
- Skipped: XX
- Duration: XX seconds

## Failed Tests
1. test_name - Error message
2. ...

## Skipped Tests
1. test_name - Reason
2. ...

## Performance Notes
- Slowest test: test_name (XX seconds)
- Average duration: XX ms

## Recommendations
- [Any issues found]
- [Suggested fixes]
```

---

**Last Updated:** 2025-11-11  
**Test Suite Version:** 1.0.0  
**Compatible with:** HA Cursor Agent v2.7.7+

