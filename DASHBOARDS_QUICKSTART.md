# Dashboard Quick Start Guide

## For Developers

### Running the Application

1. **Start the backend:**
   ```bash
   cd backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend (in another terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api
   - Default login: `admin` / `admin`

### Quick Test

1. Log in to the application
2. Click "Dashboards" in the top navigation
3. Click "Create Dashboard"
4. Fill in:
   - Name: "Test Dashboard"
   - Description: "My first dashboard"
   - Leave other defaults
5. Click "Create Dashboard"
6. You should see your new dashboard in the list
7. Click on it to view (empty dashboard with placeholder)

## API Examples

### Create a Dashboard

```bash
# Login first to get session cookie
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' \
  -c cookies.txt

# Create dashboard
curl -X POST http://localhost:8000/api/dashboards \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "System Overview",
    "description": "High-level metrics",
    "is_public": false,
    "refresh_interval": 60
  }'
```

### List Dashboards

```bash
curl -X GET http://localhost:8000/api/dashboards \
  -b cookies.txt
```

### Get Dashboard with Widgets

```bash
curl -X GET http://localhost:8000/api/dashboards/1 \
  -b cookies.txt
```

### Add a Widget (Placeholder)

```bash
curl -X POST http://localhost:8000/api/dashboards/1/widgets \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "widget_type": "metric",
    "title": "Total Logs",
    "position_x": 0,
    "position_y": 0,
    "width": 4,
    "height": 3,
    "config": {
      "metric_type": "count",
      "query": {
        "level": "ERROR"
      }
    }
  }'
```

## Database Schema Quick Reference

```sql
-- Check dashboards
SELECT * FROM dashboards;

-- Check widgets
SELECT * FROM dashboard_widgets;

-- Check saved queries
SELECT * FROM saved_queries;

-- Get dashboard with widget count
SELECT d.*, COUNT(w.id) as widget_count
FROM dashboards d
LEFT JOIN dashboard_widgets w ON d.id = w.dashboard_id
GROUP BY d.id;
```

## Troubleshooting

### Database Migration Issues

If dashboards tables don't exist:
```bash
cd backend
sqlite3 jlo.db < migrations/20260501000000_add_dashboards.sql
```

### Frontend Build Issues

```bash
cd frontend
npm install  # Reinstall dependencies
npm run build  # Test build
```

### Import Errors

Test backend imports:
```bash
cd backend
uv run python -c "from main import app; print('Success!')"
```

## File Locations

### Backend Files
- Migration: `backend/migrations/20260501000000_add_dashboards.sql`
- Models: `backend/models.py` (search for "Dashboard")
- Database: `backend/database.py` (search for "# Dashboard operations")
- API: `backend/main.py` (search for "# Dashboard Endpoints")

### Frontend Files
- Dashboard List: `frontend/src/views/DashboardsList.vue`
- Dashboard View: `frontend/src/views/DashboardView.vue`
- API Client: `frontend/src/services/api.js` (search for "// Dashboards")
- Routes: `frontend/src/router/index.js`
- Navigation: `frontend/src/components/AppLayout.vue`

## What Works Now

✅ **Fully Functional:**
- Create dashboards with name, description, visibility
- List all dashboards (owned + public)
- View dashboard details
- Edit dashboard settings
- Delete dashboards (owner only)
- Duplicate dashboards
- Public/private visibility
- Auto-refresh configuration
- Permission-based UI
- Responsive design
- Empty states
- Loading states

📦 **Framework Ready (Phase 2):**
- Widget CRUD operations (backend complete)
- Widget data fetching (backend skeleton)
- Chart.js installed
- Grid layout prepared
- Saved queries (backend complete)

## Next Development Tasks

1. **Implement Widget Components** (Phase 2)
   - Create `MetricWidget.vue`
   - Create `ChartWidget.vue`
   - Create `TableWidget.vue`
   - Create `LogStreamWidget.vue`

2. **Widget Configuration** (Phase 2)
   - Widget configuration dialog
   - Query builder UI
   - Time range picker

3. **Chart Integration** (Phase 2)
   - Configure Chart.js
   - Implement data aggregation
   - Add chart types (line, bar, pie)

4. **Drag & Drop** (Phase 3)
   - Install grid layout library
   - Implement drag handlers
   - Implement resize handlers

## Support

For issues or questions:
1. Check `DASHBOARDS_MVP.md` for detailed implementation notes
2. Review API endpoints in `backend/main.py`
3. Check browser console for frontend errors
4. Check backend logs for API errors

## Quick Commands

```bash
# Run tests
cd backend && uv run pytest

# Build frontend
cd frontend && npm run build

# Database status
cd backend && uv run python -m migrations_cli status

# Start dev servers (using just)
just dev

# Stop dev servers
just dev-stop
```

Happy dashboard building! 🎉
