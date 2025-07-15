
# 🚀 Manual Upload Instructions

Since Railway doesn't support direct file uploads via script, you need to:

## Option 1: Use Railway CLI (Recommended)
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Link to your project: `railway link`
4. Copy files: `railway run cp uploads/* /app/uploads/`

## Option 2: Re-upload via Web Interface
1. Go to your Railway app
2. Upload scan images through the web interface
3. This will recreate the files in the volume

## Option 3: Use Railway Shell
1. `railway shell`
2. Manual file creation/upload

## Verify Volume is Working
After setting up the volume, your scan history should work properly.
