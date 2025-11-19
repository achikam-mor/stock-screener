# 🚀 Deployment Guide - Stock Screener to GitHub Pages

This guide will help you deploy your Python stock screener to run automatically every day at 23:40 Jerusalem time and display results on a public website.

## 📋 Prerequisites

- GitHub account (free - [Sign up here](https://github.com/signup))
- Git installed on your computer ([Download Git](https://git-scm.com/downloads))

---

## 🔧 Step-by-Step Deployment

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon (top-right) → **"New repository"**
3. Fill in the details:
   - **Repository name**: `stock-screener` (or any name you prefer)
   - **Description**: "Daily automated stock screening with SMA150 analysis"
   - **Visibility**: Choose **Public** (required for free GitHub Pages)
   - ✅ **Check** "Add a README file"
4. Click **"Create repository"**

### Step 2: Push Your Code to GitHub

Open PowerShell in your project directory and run:

```powershell
# Navigate to your project directory
cd C:\Users\amor\Downloads\PythonProject\PythonProject

# Initialize git (if not already initialized)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Stock screener with GitHub Actions"

# Add your GitHub repository as remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Important**: Replace `YOUR_USERNAME` with your GitHub username and `YOUR_REPO` with your repository name.

### Step 3: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on the **"Actions"** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**
4. You should see your workflow: **"Daily Stock Screening"**

### Step 4: Enable GitHub Pages

1. In your repository, click **"Settings"** (top menu)
2. Scroll down and click **"Pages"** (left sidebar)
3. Under **"Source"**, select:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
4. Click **"Save"**
5. Wait 1-2 minutes, then refresh the page
6. You'll see: **"Your site is live at https://YOUR_USERNAME.github.io/YOUR_REPO/"**

### Step 5: Grant Workflow Permissions

1. In your repository, go to **"Settings"** → **"Actions"** → **"General"**
2. Scroll to **"Workflow permissions"**
3. Select **"Read and write permissions"**
4. ✅ Check **"Allow GitHub Actions to create and approve pull requests"**
5. Click **"Save"**

---

## ⚙️ How It Works

### Automatic Daily Execution

- **Schedule**: Every day at **23:40 Jerusalem time** (20:40 UTC)
- **GitHub Actions** runs your Python script automatically
- Results are saved to `results.json`
- File is committed back to the repository
- Website updates automatically

### Manual Trigger (Optional)

You can also run the screening manually:

1. Go to your repository → **"Actions"** tab
2. Click **"Daily Stock Screening"** workflow
3. Click **"Run workflow"** button → **"Run workflow"**

---

## 🌐 Access Your Website

Your stock screener dashboard will be available at:

```
https://YOUR_USERNAME.github.io/YOUR_REPO/
```

Example: `https://johndoe.github.io/stock-screener/`

---

## 📂 Project Structure

```
PythonProject/
├── .github/
│   └── workflows/
│       └── daily-screening.yml    # GitHub Actions workflow
├── data_loader.py                 # Data fetching logic
├── stock_analyzer.py              # Technical analysis
├── stock_screener.py              # Screening logic
├── results_manager.py             # Results handling & JSON export
├── models.py                      # Data models
├── main.py                        # Main execution script
├── requirements.txt               # Python dependencies
├── AllStocks.txt                  # Stock tickers list
├── index.html                     # Website homepage
├── styles.css                     # Website styling
├── script.js                      # Website functionality
└── results.json                   # Generated results (auto-created)
```

---

## 🔍 Testing Before First Run

Before waiting for the scheduled run, test manually:

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Run the script
python main.py
```

This should create `results.json` in your project directory.

---

## 🛠️ Troubleshooting

### Issue: Workflow fails with "permission denied"
**Solution**: Check Step 5 - Workflow permissions must be set to "Read and write"

### Issue: Website shows "404 Not Found"
**Solution**: 
- Ensure GitHub Pages is enabled (Step 4)
- Wait 2-3 minutes after enabling
- Check that `index.html` is in the root directory

### Issue: Results not updating
**Solution**:
- Check the **"Actions"** tab for workflow runs
- Click on a failed run to see error logs
- Verify `requirements.txt` includes all dependencies

### Issue: Timezone is wrong
**Solution**: The workflow uses UTC time internally but displays Jerusalem time on the website. The cron is set to `40 20 * * *` (20:40 UTC = 23:40 Jerusalem in summer).

For winter time adjustment, change in `.github/workflows/daily-screening.yml`:
```yaml
- cron: '40 21 * * *'  # 21:40 UTC = 23:40 Jerusalem in winter
```

---

## 🔐 Security Notes

✅ **No API keys needed** - yfinance is free and doesn't require authentication

✅ **No sensitive data** - All code and results are public

✅ **GitHub tokens** - Automatically provided by GitHub Actions (no setup needed)

---

## 📊 Features of Your Dashboard

- **Real-time data display** - Shows latest screening results
- **Responsive design** - Works on desktop, tablet, and mobile
- **Auto-refresh** - Page refreshes every 5 minutes
- **Summary cards** - Quick overview of results
- **Hot stocks** - Stocks above SMA150
- **Watch list** - Stocks below SMA150
- **Failed tickers** - Stocks that couldn't be analyzed

---

## 🎨 Customization

### Change Screening Time

Edit `.github/workflows/daily-screening.yml`:

```yaml
schedule:
  - cron: '40 20 * * *'  # Change these numbers
```

Cron format: `minute hour * * *` (UTC time)

### Modify Stock List

Edit `AllStocks.txt` or update the `tickers` list in `main.py`

### Change Website Appearance

Edit `styles.css` to customize colors, fonts, and layout

---

## 📞 Need Help?

If you encounter issues:

1. Check the **Actions** tab logs in GitHub
2. Verify all files are committed and pushed
3. Ensure GitHub Pages is enabled and pointing to `main` branch
4. Test locally first with `python main.py`

---

## ✅ Deployment Checklist

- [ ] GitHub account created
- [ ] Repository created and code pushed
- [ ] GitHub Actions enabled
- [ ] Workflow permissions set to "Read and write"
- [ ] GitHub Pages enabled (Branch: main, Folder: root)
- [ ] First manual workflow run successful
- [ ] Website accessible at your GitHub Pages URL
- [ ] Results.json generated successfully

---

## 🎉 You're Done!

Your stock screener is now:
- ✅ Running automatically every day at 23:40 Jerusalem time
- ✅ Saving results to a file
- ✅ Displaying results on a public website
- ✅ Completely free and automated

Visit your website to see the results: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

**Note**: The first scheduled run will occur at the next 23:40 Jerusalem time. You can trigger a manual run immediately from the Actions tab to see it working right away!
