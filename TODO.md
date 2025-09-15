# Frontend Rebuild and Backend Integration TODO

## Overview
Rebuild the frontend keeping content and styles, fix build errors, and ensure proper communication with backend and database.

## Steps

### 1. Fix Authentication Integration
- [x] Update FlipLoginSignup.tsx to use AuthContext for login/logout
- [x] Ensure AuthContext uses apiClient for backend calls
- [x] Fix API URLs in AuthContext (use full paths with apiClient)

### 2. Verify API Client Configuration
- [ ] Check apiClient.ts base URL and interceptors
- [ ] Ensure consistent use of apiClient across components

### 3. Fix Build Errors
- [ ] Run npm run build and identify errors
- [ ] Fix TypeScript issues, missing imports, etc.
- [ ] Remove unused imports (e.g., flip-card.css if not needed)

### 4. Test Backend Communication
- [ ] Verify login works with backend /api/auth/login
- [ ] Test recommendations fetch in /learn page
- [ ] Ensure database operations work through backend

### 5. Preserve Styles and Content
- [ ] Ensure all existing UI components and styles remain intact
- [ ] Verify flip-card animations and responsive design
- [ ] Check accessibility features

### 6. Final Testing
- [ ] Run frontend in dev mode
- [ ] Test full user flow: login -> dashboard -> recommendations
- [ ] Confirm no build errors
