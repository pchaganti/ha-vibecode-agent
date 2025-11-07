# Changelog

## [1.0.0] - 2025-11-03

### Added
- Initial release
- FastAPI REST API
- Files API (read/write/list/append/delete)
- Entities API (list/state/services)
- Helpers API (create/delete)
- Automations API (create/delete/list)
- Scripts API (create/delete/list)
- System API (reload/check_config/restart)
- Backup API (commit/rollback/history/diff)
- Logs API (get/clear)
- Git versioning integration
- Automatic backups before modifications
- Swagger UI documentation
- Authentication via HA token
- Comprehensive logging
- Health check endpoint

### Features
- ✅ Full file system access to /config
- ✅ CRUD operations for helpers, automations, scripts
- ✅ Git-based version control
- ✅ Automatic backup/rollback
- ✅ Configuration validation
- ✅ Component reload without restart
- ✅ Interactive API documentation
- ✅ Audit logs

### Security
- Path validation (restricted to /config)
- Token-based authentication
- Operation logging
- Safe rollback mechanism

---

## Future Plans

### [1.1.0] - Planned
- WebSocket support for real-time updates
- Bulk operations API
- Template validation before applying
- Dashboard management API
- Lovelace card creation
- Integration management
- Device management

### [1.2.0] - Planned
- AI-friendly natural language API
- Auto-fix configuration errors
- Dependency detection
- Impact analysis before changes
- Automated testing
- Performance optimization

---

*Stay tuned for updates!*

