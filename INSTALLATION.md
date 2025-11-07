# HA Cursor Agent - Installation Guide

**Complete guide to installing and configuring the agent**

---

## 📦 Prerequisites

- Home Assistant OS or Supervised
- Access to Add-on Store
- Long-Lived Access Token (for external access)

---

## 🚀 Installation Steps

### Step 1: Copy Add-on to Home Assistant

**Option A: Via File Editor / SSH**

1. Copy the entire `ha_cursor_agent` folder to:
   ```
   /addons/home-assistant-cursor-agent/
   ```

2. Structure should be:
   ```
   /addons/
   └── home-assistant-cursor-agent/
       ├── config.yaml
       ├── Dockerfile
       ├── run.sh
       ├── requirements.txt
       ├── app/
       └── README.md
   ```

**Option B: Via Samba Share**

1. Open `\\homeassistant.local\addons\`
2. Create folder `ha_cursor_agent`
3. Copy all files into it

---

### Step 2: Reload Add-on Store

1. Open Home Assistant
2. Go to **Supervisor** → **Add-on Store**
3. Click **⋮** (three dots top-right)
4. Select **Reload**
5. Wait 10-20 seconds

---

### Step 3: Install Add-on

1. Scroll down to **Local Add-ons** section
2. Find **HA Cursor Agent**
3. Click on it
4. Click **INSTALL** button
5. Wait for installation to complete (1-2 minutes)

---

### Step 4: Configure Add-on

1. Go to **Configuration** tab
2. Set options:
   ```yaml
   port: 8099
   log_level: info
   enable_git_versioning: true
   auto_backup: true
   max_backups: 50
   ```
3. **SAVE**

---

### Step 5: Start Add-on

1. Go to **Info** tab
2. Toggle **Start on boot** (recommended)
3. Click **START**
4. Wait 10-20 seconds
5. Check logs for "Starting HA Cursor Agent..."

---

### Step 6: Verify Installation

**Check Health:**
```bash
curl http://homeassistant.local:8099/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "config_path": "/config",
  "git_enabled": true
}
```

---

### Step 7: Get API Token

**For AI/External Access:**

1. Home Assistant → **Profile** (click your name)
2. Scroll to **Long-Lived Access Tokens**
3. Click **CREATE TOKEN**
4. Name it: `HA Cursor Agent`
5. Copy the token
6. **Save it securely!**

---

### Step 8: Test API

**Test with curl:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://homeassistant.local:8099/api/entities/list?domain=climate
```

**Or open in browser:**
```
http://homeassistant.local:8099/docs
```

(Will ask for token - enter it there)

---

## ✅ Verification Checklist

- [ ] Add-on folder copied to `/addons/home-assistant-cursor-agent/`
- [ ] Add-on visible in Local Add-ons
- [ ] Add-on installed successfully
- [ ] Add-on started without errors
- [ ] Health endpoint responds
- [ ] Long-Lived Token created
- [ ] API responds with token
- [ ] Swagger UI accessible at `/docs`

---

## 🔧 Configuration Options

### port
- **Default:** 8099
- **Description:** API server port
- **Range:** 1024-65535

### log_level
- **Default:** info
- **Options:** debug, info, warning, error
- **Description:** Logging verbosity

### enable_git_versioning
- **Default:** true
- **Description:** Enable Git-based backups
- **Recommendation:** ✅ Keep enabled

### auto_backup
- **Default:** true
- **Description:** Auto-commit after each change
- **Recommendation:** ✅ Keep enabled

### max_backups
- **Default:** 50
- **Range:** 10-1000
- **Description:** Maximum commits to retain

---

## 🐛 Troubleshooting

### Add-on not appearing in store

**Solution:**
1. Check folder is in correct location (`/addons/`)
2. Reload add-on store (⋮ → Reload)
3. Check Supervisor logs for errors

### Add-on won't start

**Check logs:** Supervisor → HA Cursor Agent → **Logs**

**Common issues:**
- Port 8099 already in use → Change port in config
- Invalid config.yaml → Check YAML syntax
- Missing permissions → Check add-on has `config:rw` mapping

### API returns 401 Unauthorized

**Check:**
- Token is correct
- Authorization header format: `Bearer TOKEN`
- Token hasn't expired

### Git initialization fails

**Check logs for:**
- `/config` directory permissions
- Git errors

**Solution:**
- Restart add-on
- Or disable Git versioning temporarily

---

## 🔄 Updating Add-on

### Manual Update

1. Stop the add-on
2. Replace files in `/addons/home-assistant-cursor-agent/`
3. Reload add-on store
4. Click **REBUILD** (if available)
5. Start add-on

### Via Git (if add-on supports)

Future feature - automatic updates

---

## 🗑️ Uninstallation

1. **Stop add-on**
2. **Uninstall** (button in add-on page)
3. **Remove folder** `/addons/home-assistant-cursor-agent/` (optional)
4. **Remove Git repo** `/config/.git/` if you want (⚠️ loses all history!)

---

## 📞 Support

**Logs:** Supervisor → HA Cursor Agent → Logs  
**API Docs:** http://homeassistant.local:8099/docs  
**Agent Logs:** GET `/api/logs/`

---

**Installation complete! Your AI agent is ready to manage Home Assistant!** 🎉

