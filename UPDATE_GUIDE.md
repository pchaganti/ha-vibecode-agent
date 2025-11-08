# How to Update HA Cursor Agent to v1.0.3

## 🎯 Quick Update (5 minutes)

### Step 1: Copy Files to Home Assistant

You need to copy the updated files to your Home Assistant add-on:

1. **Via SSH/Terminal** (if you have SSH access):

```bash
# Connect to Home Assistant
ssh root@homeassistant.local

# Navigate to add-ons directory
cd /addons/home_assistant_cursor_agent

# Backup current version (optional but recommended)
cp -r app app_backup_$(date +%Y%m%d)

# Exit and copy files from your dev machine
exit

# From your development machine:
scp -r /Users/Coolver_1/Projects/smart-home/home-assistant-cursor-agent/app \
    root@homeassistant.local:/addons/home_assistant_cursor_agent/

scp /Users/Coolver_1/Projects/smart-home/home-assistant-cursor-agent/config.yaml \
    root@homeassistant.local:/addons/home_assistant_cursor_agent/
```

2. **Via Samba/File Share** (easier):
   - Open `\\homeassistant.local\addons` in your file browser
   - Navigate to `home_assistant_cursor_agent`
   - Replace `app/` folder with updated version
   - Replace `config.yaml`

### Step 2: Rebuild the Add-on

1. Go to **Settings** → **Add-ons** → **HA Cursor Agent**
2. Click **⋮** (three dots) → **Rebuild**
3. Wait for rebuild to complete (may take 2-5 minutes)
4. Click **Restart**

### Step 3: Verify Update

1. Check **Log** tab in the add-on
2. Look for:
```
=== Token Configuration ===
SUPERVISOR_TOKEN: PRESENT
...
```

3. If you see this, the update is successful! ✅

---

## 🧪 Test MCP Connection

After updating, test that everything works:

### From Cursor AI

Just ask me (the AI) to list your entities:
```
List all my light entities
```

If I can do it without errors, it works! ✅

### From Terminal (optional)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://homeassistant.local:8099/api/health

# Should return:
# {"status":"healthy","version":"1.0.3",...}
```

---

## 🐛 If You See Errors

### Error: "Invalid token: HA API returned 401"

**Check the logs** for detailed information:

1. Go to add-on **Log** tab
2. Set **LOG_LEVEL** to `debug` in Configuration tab
3. Restart the add-on
4. Look for:

```
=== Token Configuration ===
SUPERVISOR_TOKEN: MISSING  ← This is the problem!
```

**Fix:**
- Make sure `homeassistant_api: true` in `config.yaml`
- Rebuild the add-on
- Restart

### Error: "Connection refused" or "Not Found"

**The agent is not running:**

1. Check add-on status (should be green "Running")
2. Check port 8099 is exposed
3. Restart the add-on

---

## 🔄 Rollback (if needed)

If something goes wrong, rollback to previous version:

```bash
# Via SSH
ssh root@homeassistant.local
cd /addons/home_assistant_cursor_agent
rm -rf app
mv app_backup_YYYYMMDD app  # Replace YYYYMMDD with your backup date
exit
```

Then rebuild the add-on.

---

## 📝 What Changed in v1.0.3

### Added Enhanced Logging:
- ✅ Token configuration at startup
- ✅ Detailed token validation
- ✅ HA API request/response logging
- ✅ Clear error messages

### Why This Helps:
- Easier to diagnose "Invalid token" errors
- See which token is being used (SUPERVISOR_TOKEN vs DEV_TOKEN)
- Track every HA API request

---

## 🚀 Ready to Test!

After updating, try these commands through Cursor AI:

1. "List all my climate entities"
2. "Show me the state of sensor.bedroom_temperature"
3. "List all my automations"

If these work, your MCP connection is perfect! 🎉

---

## 💡 Tips

### Enable Debug Logging (temporarily)

For detailed troubleshooting:

1. Go to add-on **Configuration** tab
2. Change `log_level: debug`
3. Click **Save**
4. Restart

**Remember to change back to `info` after debugging!**

### Check Token Validity

Test your token directly:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://homeassistant.local:8123/api/

# Should return:
# {"message": "API running."}
```

If this fails, your token is invalid or expired.

---

## 📞 Need Help?

If you're still stuck:

1. **Check logs** with `debug` level
2. **Copy relevant log lines** (redact token values!)
3. **Report issue** with:
   - Log excerpts
   - What you tried
   - Expected vs actual behavior

---

**Happy debugging! 🎯**

