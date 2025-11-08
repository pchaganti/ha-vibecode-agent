# Release v1.0.3 - Enhanced Debugging & Token Logging

**Release Date:** 2025-11-08  
**Type:** Bug fix & debugging enhancement

---

## 🐛 What Was Fixed

### Issue: "Invalid token" errors in logs

**Problem:**
Users reported seeing `"Invalid token: HA API returned 401"` errors even when using valid Long-Lived Access Tokens. The issue was difficult to diagnose due to insufficient logging.

**Root Cause:**
The agent wasn't clearly logging:
- Which tokens were available at startup (SUPERVISOR_TOKEN vs HA_TOKEN)
- Which token was being used for HA API requests
- Detailed information about token validation failures

---

## ✨ What's New

### 1. **Enhanced Startup Logging**
Agent now logs token configuration at startup:
```
=== Token Configuration ===
SUPERVISOR_TOKEN: PRESENT
DEV_TOKEN (HA_TOKEN): MISSING
HA_URL: http://supervisor/core
Mode: Add-on (using SUPERVISOR_TOKEN for HA API)
============================
```

### 2. **Detailed Token Validation Logging**
Every token validation attempt now logs:
- Token being validated (first 20 chars + ...)
- URL being tested
- HA API response status and body
- Success/failure with clear ✅/❌ indicators

Example:
```
Add-on mode: Validating user token eyJhbGciOiJIUzI1NiI... against HA API
Testing token at: http://supervisor/core/api/
HA API response: 200 - {"message":"API running."}
✅ Token validated successfully: eyJhbGciOiJIUzI1NiI...
```

### 3. **HA Client Request Logging**
Every HA API request now logs:
- HTTP method and URL
- Token being used (preview)
- Response status
- Error details with token info

Example:
```
HA API Request: GET http://supervisor/core/api/states, Token: eyJhbGciOiJIUzI1NiI...
HA API success: GET http://supervisor/core/api/states -> 200
```

### 4. **HA Client Initialization Logging**
HAClient now logs its configuration:
```
HAClient initialized - URL: http://supervisor/core, Token source: SUPERVISOR_TOKEN, Token: eyJhbGciOiJIUzI1NiI...
```

---

## 🔍 Debugging Guide

If you see "Invalid token" errors after this update, check the logs:

### 1. **Check Startup Logs**
Look for `=== Token Configuration ===` block:
- If `SUPERVISOR_TOKEN: MISSING` → Home Assistant didn't provide the token (check `homeassistant_api: true` in config.yaml)
- If `DEV_TOKEN: PRESENT` → You're in development mode (not recommended for production)

### 2. **Check Token Validation**
Look for token validation attempts:
- ✅ = Token validated successfully
- ❌ = Token rejected by HA API

If ❌, check:
- Is the token from a valid Long-Lived Access Token?
- Does the token have required permissions?
- Has the token expired or been deleted?

### 3. **Check HA API Requests**
Look for `HA API Request` and `HA API error` messages:
- Compare token preview with expected token
- Check if URL is correct
- Look at error response from HA

---

## 📦 How to Update

### Method 1: From Home Assistant UI (Recommended)

1. Go to **Settings** → **Add-ons** → **HA Cursor Agent**
2. Click **Update** button
3. Wait for update to complete
4. Click **Restart**
5. Check logs for new startup messages

### Method 2: Manual Update (Advanced)

If you're developing locally:

```bash
cd /path/to/home-assistant-cursor-agent
git pull origin main

# If running in Docker
docker-compose down
docker-compose up --build -d

# If running locally
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8099
```

---

## 🧪 Testing

After update, test MCP connection:

1. **Check agent logs** in Home Assistant:
   - Look for `=== Token Configuration ===`
   - Verify SUPERVISOR_TOKEN is PRESENT

2. **Make a test request** from Cursor (or terminal):
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://homeassistant.local:8099/api/entities/list
```

3. **Check logs** for:
   - Token validation: `✅ Token validated successfully`
   - HA API request: `HA API success: GET http://...`

---

## 🔐 Security Note

This version logs token previews (first 20 characters) for debugging. This is safe because:
- Full tokens are never logged
- 20 characters is insufficient to use the token
- Logs are only accessible to Home Assistant admin

If you're concerned, set `LOG_LEVEL: info` instead of `debug` in add-on configuration.

---

## 📝 Changelog

### Added
- Startup logging for token configuration
- Detailed token validation logging with response body
- HA API request/response logging
- HAClient initialization logging
- Success/failure indicators (✅/❌)

### Changed
- Version bumped to 1.0.3
- Improved error messages with token context

### Fixed
- Made token-related issues easier to diagnose

---

## 🙏 Feedback

If you still experience token issues after this update, please:

1. **Set log level to DEBUG** in add-on configuration
2. **Restart the agent**
3. **Make a failing request**
4. **Copy the relevant logs** (with token previews redacted if sharing publicly)
5. **Report the issue** with logs

---

## 🔗 Links

- **GitHub:** https://github.com/Coolver/home-assistant-cursor-agent
- **Issues:** https://github.com/Coolver/home-assistant-cursor-agent/issues
- **Documentation:** [README.md](README.md)

---

**Enjoy better debugging! 🎉**

