# Stockreport Reader - Troubleshooting Guide

## Common Issues and Solutions

### 1. "Failed to load PDF file" Error

**Symptoms:**
- PDF viewer shows "Failed to load PDF file"
- Console shows CORS or network errors

**Solutions:**

1. **Check if all services are running:**
   ```bash
   # Check Upload API (port 9000)
   curl http://localhost:9000/health
   
   # Check Supervisor API (port 8000)
   curl http://localhost:8000/health
   ```

2. **Verify CORS is enabled:**
   - Both backend services have CORS middleware configured
   - Check browser console for CORS errors

3. **Check the PDF URL in browser console:**
   - Open browser DevTools (F12)
   - Look for the PDF URL being requested
   - Try accessing the URL directly in browser

4. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Clear site data in DevTools > Application > Storage

### 2. Chat Messages Not Showing

**Symptoms:**
- Messages sent but no response appears
- Console shows network errors

**Solutions:**

1. **Check the Network tab in DevTools:**
   - Look for POST request to `/query`
   - Check response status and data

2. **Verify backend response format:**
   - The backend returns JSON with `{success, answer, ...}`
   - Frontend expects this format

3. **Check console logs:**
   - Look for "Sending query request" and "Received response" logs
   - Check for any error messages

### 3. Services Won't Start

**Symptoms:**
- `start-services.bat` shows errors
- Ports already in use

**Solutions:**

1. **Kill existing processes:**
   ```bash
   # Windows - Kill processes on ports
   netstat -ano | findstr :8000
   netstat -ano | findstr :9000
   netstat -ano | findstr :5173
   
   # Then kill the process
   taskkill /PID <process_id> /F
   ```

2. **Check conda environment:**
   ```bash
   conda activate py311-base
   python --version  # Should be 3.11.x
   ```

3. **Reinstall dependencies:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   pnpm install
   ```

## Quick Debug Steps

1. **Open browser console (F12)** and check for errors
2. **Check Network tab** for failed requests
3. **Look at the Console tab** for JavaScript errors
4. **Verify all 3 services are running:**
   - Frontend: http://localhost:5173
   - Upload API: http://localhost:9000/docs
   - Supervisor API: http://localhost:8000/docs

## Testing Individual Components

### Test PDF Upload:
```javascript
// In browser console
fetch('http://localhost:9000/health')
  .then(r => r.json())
  .then(console.log)
```

### Test Query API:
```javascript
// In browser console
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'test'})
})
  .then(r => r.json())
  .then(console.log)
```

## Need More Help?

1. Check the browser console for detailed error messages
2. Look at the terminal windows running each service for server-side errors
3. Ensure all environment variables are set correctly in `.env` files 