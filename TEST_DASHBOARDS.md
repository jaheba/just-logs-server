# Testing Dashboards Feature

## Quick Test Steps

### 1. Start the Application

```bash
# Terminal 1 - Start backend
cd backend
uv run uvicorn main:app --reload --port 8000

# Terminal 2 - Start frontend  
cd frontend
npm run dev
```

### 2. Access the Application

1. Open your browser to: http://localhost:5173
2. Login with: `admin` / `admin`

### 3. Test Dashboards

#### Navigate to Dashboards
1. Click on **"Dashboards"** in the top navigation bar
2. You should see the Dashboards page

#### Create Your First Dashboard
1. Click the **"Create Dashboard"** button
2. Fill in the form:
   - **Name:** "My First Dashboard"
   - **Description:** "Testing dashboard feature"
   - **Make this dashboard public:** (check or uncheck)
   - **Auto-refresh interval:** 60 (seconds)
3. Click **"Create Dashboard"**
4. You should see your dashboard card appear

#### View Dashboard
1. Click on your dashboard card
2. You'll see an empty dashboard (placeholder for now)
3. Try the **"Edit"** mode toggle
4. Try the **"Refresh"** button

## What Should Work

✅ **Working Features:**
- Dashboard list view
- Create dashboard
- Edit dashboard settings
- Delete dashboard  
- Duplicate dashboard
- Public/Private visibility
- Owner permissions (edit/delete only for owner)
- Empty states
- Loading states
- Responsive design

📦 **Placeholder Features (Phase 2):**
- Actual widgets (shows placeholders)
- Widget data visualization
- Charts and graphs
- Drag & drop layout

## Troubleshooting

### Issue: Can't see Dashboards in navigation
**Solution:** Icons were missing. This has been fixed. Rebuild frontend:
```bash
cd frontend
npm run build
```

### Issue: Dashboard tables don't exist
**Solution:** Run migrations manually:
```bash
cd backend
cat migrations/20260501000000_add_dashboards.sql | awk '/^-- up$/,/^-- down$/' | grep -v "^-- down$" | sqlite3 jlo.db
```

### Issue: 404 when accessing /dashboards
**Check:**
1. Frontend is running on port 5173
2. Router has dashboard routes (should be there)
3. Check browser console for errors

### Issue: Can't create dashboard
**Check browser console for:**
- Network errors (API call failures)
- Authentication errors
- Validation errors

## API Testing (Optional)

### Create Dashboard via API
```bash
# Login first
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' \
  -c cookies.txt

# Create dashboard
curl -X POST http://localhost:8000/api/dashboards \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Test Dashboard",
    "description": "Created via API",
    "is_public": false,
    "refresh_interval": 60
  }'

# List dashboards
curl -X GET http://localhost:8000/api/dashboards -b cookies.txt
```

## Database Checks

```bash
cd backend

# Check dashboards exist
sqlite3 jlo.db "SELECT * FROM dashboards"

# Check widgets exist
sqlite3 jlo.db "SELECT * FROM dashboard_widgets"

# Check saved queries
sqlite3 jlo.db "SELECT * FROM saved_queries"

# Check environment column in apps
sqlite3 jlo.db "PRAGMA table_info(apps)"

# Check environment retention policies
sqlite3 jlo.db "SELECT * FROM environment_retention_policies"
```

## Expected Console Output

### Backend (Terminal 1)
```
INFO:     Started server process
INFO:     Waiting for application startup.
SQLite optimizations applied:
  - Journal mode: wal
  - Synchronous: 1
  - Cache size: -64000 pages

Running database migrations...
...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Frontend (Terminal 2)
```
  VITE v7.3.1  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Next Steps

Once dashboards are working:
1. Continue with environment-based retention (in progress)
2. Implement actual widgets (Phase 2)
3. Add chart visualizations (Phase 2)
4. Add drag & drop layout (Phase 3)

## Success Indicators

✅ You can:
- See "Dashboards" link in navigation
- Access /dashboards page
- Create a new dashboard
- See dashboard card in the list
- Click dashboard to view it (even if empty)
- Edit dashboard settings
- Delete your own dashboards
- See public/private badges

If all above work, dashboards MVP is successfully deployed!
