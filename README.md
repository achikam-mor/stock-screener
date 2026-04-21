# 📈 Stock Screener Dashboard

An automated stock screening tool that analyzes stocks based on SMA150 and ATR14 technical indicators. Runs daily at 23:40 Jerusalem time and displays results on a beautiful web dashboard.

## 🌟 Features

- **Automated Daily Analysis** - Runs automatically via GitHub Actions
- **SMA150 Screening** - Identifies stocks above/below 150-day moving average
- **ATR14 Calculation** - Measures stock volatility
- **Beautiful Dashboard** - Clean, responsive web interface
- **Real-time Updates** - Results update daily automatically
- **100% Free** - No API keys or servers required

## 📊 Live Demo

Visit the live dashboard: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Git
- GitHub account

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the screener:
```bash
python main.py
```

This will generate `results.json` with the screening results.

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed step-by-step instructions on deploying to GitHub Pages.

**Quick deployment steps:**
1. Create GitHub repository
2. Push code to GitHub
3. Enable GitHub Actions
4. Enable GitHub Pages
5. Set workflow permissions to "Read and write"

## 📁 Project Structure

```
├── .github/workflows/
│   └── daily-screening.yml    # Automated workflow
├── data_loader.py             # Fetch stock data
├── stock_analyzer.py          # Technical analysis
├── stock_screener.py          # Screening logic
├── results_manager.py         # Export results
├── models.py                  # Data models
├── main.py                    # Main script
├── index.html                 # Dashboard UI
├── styles.css                 # Dashboard styling
├── script.js                  # Dashboard logic
├── requirements.txt           # Python dependencies
└── AllStocks.txt              # Stock tickers list
```

## 🔧 Configuration

### Change Screening Time

Edit `.github/workflows/daily-screening.yml`:
```yaml
schedule:
  - cron: '40 20 * * *'  # 20:40 UTC = 23:40 Jerusalem Time
```

### Modify Stock List

Edit the `tickers` list in `main.py` or update `AllStocks.txt`

### Customize Dashboard

Edit `styles.css` to change colors, fonts, and layout

## 📊 How It Works

1. **GitHub Actions** triggers daily at 23:40 Jerusalem time
2. **Python script** fetches stock data from Yahoo Finance
3. **Analysis** calculates SMA150 and ATR14 indicators
4. **Screening** categorizes stocks as "Hot" (above SMA) or "Watch" (below SMA)
5. **Export** saves results to `results.json`
6. **Commit** pushes updated results to repository
7. **Display** GitHub Pages serves the dashboard with latest data

## 🛠️ Technical Details

- **Data Source**: Yahoo Finance (via yfinance library)
- **Analysis Period**: 500 days of historical data
- **Indicators**: SMA150, ATR14
- **Update Frequency**: Daily at 23:40 Jerusalem time
- **Hosting**: GitHub Pages (free)
- **Automation**: GitHub Actions (free)

## 📦 Dependencies

- `yfinance` - Stock data retrieval
- `pandas` - Data manipulation
- `numpy` - Numerical computations
- `aiohttp` - Async HTTP requests
- `pytest` - Testing

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_stock_analyzer.py
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is open source and available for educational purposes.

## ⚠️ Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## 📞 Support 

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for setup help
2. Review GitHub Actions logs for errors
3. Open an issue on GitHub

## 🎯 Roadmap

- [ ] Add more technical indicators (RSI, MACD)
- [ ] Email notifications for hot stocks
- [ ] Historical performance tracking
- [ ] Advanced filtering options
- [ ] Mobile app

---

Made with ❤️ using Python, GitHub Actions, and GitHub Pages
