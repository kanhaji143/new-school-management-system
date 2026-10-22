# PythonAnywhere deployment (free tier, no credit card)

This is a manual, step-by-step deployment of the Django API. The Next.js
frontend is already live on Firebase Hosting.

## 0. Accounts

- PythonAnywhere: <https://www.pythonanywhere.com/signup/> (free "Beginner" plan)
- Firebase (already done): project `new-school-management-system`

---

## 1. Upload the backend

1. Sign in to PythonAnywhere, open the **Files** tab.
2. Create a folder named `school`.
3. Upload `deploy/pythonanywhere/school-backend.zip` into that folder.
4. Open the **Bash console** and run:

   ```bash
   cd ~/school
   unzip school-backend.zip -d backend
   ls backend | head
   ```

   You should see `manage.py`, `config/`, `attendance/`, `assessments/`, …

## 2. Bootstrap the app

Still in the Bash console:

```bash
cd ~/school/backend
bash ../setup.py   # or: python3 setup.py
```

This creates the virtualenv `~/.virtualenvs/schoolapi`, installs the
dependencies, runs migrations, collects static files and seeds the demo data.

If `python3 setup.py` is not found, use `python3.9 setup.py` / `python3.10 setup.py`.

## 3. Create the web app

1. Open the **Web** tab → **Add a new web app** → **Manual configuration**.
2. Choose Python 3.10 (or newer) and the domain
   `<username>.pythonanywhere.com`.
3. Replace the generated WSGI file content with the template from
   `deploy/pythonanywhere/wsgi_template.py` (inside the uploaded zip) and edit:

   - `DJANGO_SECRET_KEY` → a long random string (50+ characters)
   - `DJANGO_ALLOWED_HOSTS` → `<username>.pythonanywhere.com`
   - `DJANGO_CORS_ALLOWED_ORIGINS` → `https://new-school-management-system.web.app`

4. Save, then **Reload** the web app.

## 4. Verify the API

Open in a browser:

```
https://<username>.pythonanywhere.com/health/
```

You should see `{"status": "ok"}`.

Login check:

```bash
curl -X POST https://<username>.pythonanywhere.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.school","password":"Demo@12345"}'
```

## 5. Point the live frontend at the API

The deployed frontend reads its API host from `runtime-config.js`, so no
rebuild is needed:

1. Edit `frontend/public/runtime-config.js`:

   ```js
   window.__APP_CONFIG__ = {
     apiBaseUrl: "https://<username>.pythonanywhere.com/api",
   };
   ```

2. Redeploy hosting:

   ```bash
   cd frontend
   npx firebase-tools deploy --only hosting --project new-school-management-system
   ```

3. Open https://new-school-management-system.web.app and sign in with
   `admin@demo.school` / `Demo@12345`.

---

## Notes / limits of the free tier

- Free accounts get one web app; SQLite is used (no separate database).
- The app spins down when idle, so the first request after a pause can take
  ~30 seconds.
- Uploads go to `~/media` on the server (not shared with the local machine).
- A custom domain needs the paid plan; `pythonanywhere.com` works on free.
