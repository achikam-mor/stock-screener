# 🚀 Quick Start Guide

Follow these simple steps to deploy your stock screener:

## ✅ Step 1: Create GitHub Account (if needed)
Go to https://github.com/signup and create a free account.

## ✅ Step 2: Create New Repository

1. Visit https://github.com/new
2. Repository name: `stock-screener` (or any name)
3. Description: "Daily automated stock screening"
4. Select **Public** (required for free GitHub Pages)
5. ✅ Check "Add a README file"
6. Click **"Create repository"**

## ✅ Step 3: Push Your Code

Open PowerShell in your project directory:

```powershell
# Navigate to project
cd C:\Users\amor\Downloads\PythonProject\PythonProject

# Initialize git (if needed)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Automated stock screener"

# Add remote (REPLACE with your details!)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Important**: Replace `YOUR_USERNAME` and `YOUR_REPO` with your actual GitHub username and repository name!

## ✅ Step 4: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **"Actions"** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**

## ✅ Step 5: Set Workflow Permissions

1. In your repository, go to **Settings** → **Actions** → **General**
2. Scroll to **"Workflow permissions"**
3. Select **"Read and write permissions"**
4. ✅ Check **"Allow GitHub Actions to create and approve pull requests"**
5. Click **"Save"**

## ✅ Step 6: Enable GitHub Pages

1. Go to **Settings** → **Pages** (left sidebar)
2. Under **"Source"**:
   - Branch: `main`
   - Folder: `/ (root)`
3. Click **"Save"**
4. Wait 1-2 minutes, then refresh
5. You'll see: **"Your site is live at https://YOUR_USERNAME.github.io/YOUR_REPO/"**

## ✅ Step 7: Test Manual Run

1. Go to **"Actions"** tab
2. Click **"Daily Stock Screening"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait 1-2 minutes for completion
5. Visit your website!

## 🎉 You're Done!

Your site URL: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

### ⏰ Automatic Schedule
- Runs daily at **23:40 Jerusalem time**
- Results update automatically
- No maintenance required

### 🛠️ Need Help?

- Check the **Actions** tab for workflow logs
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
- Make sure all files are committed and pushed

---

## 📝 Important Files Created

✅ **Backend (Python)**
- `main.py` - Updated to save JSON
- `results_manager.py` - Added JSON export
- `.github/workflows/daily-screening.yml` - Automation

✅ **Frontend (Website)**
- `index.html` - Dashboard UI
- `styles.css` - Beautiful styling
- `script.js` - Dynamic data loading

✅ **Documentation**
- `DEPLOYMENT.md` - Full deployment guide
- `README.md` - Project overview
- `QUICKSTART.md` - This file!

✅ **Sample Data**
- `sample-results.json` - Example results for testing

---

## 🔍 Troubleshooting

**Problem**: Push fails with "authentication failed"
**Solution**: Use a Personal Access Token instead of password
- Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
- Generate new token with `repo` permissions
- Use token as password when prompted

**Problem**: Workflow fails
**Solution**: Check Step 5 - Workflow permissions must be "Read and write"

**Problem**: Website shows 404
**Solution**: Wait 2-3 minutes after enabling GitHub Pages

---

## 💡 Pro Tips

1. **View your website locally**: Copy `sample-results.json` to `results.json` and open `index.html` in a browser
2. **Manual trigger**: Use the "Run workflow" button to test immediately
3. **Check logs**: Click on any workflow run to see detailed logs
4. **Update schedule**: Edit `.github/workflows/daily-screening.yml` to change the time

---

**Ready to deploy? Start with Step 1!** 🚀
