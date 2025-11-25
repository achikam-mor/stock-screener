# 🚀 Vercel Migration Checklist

Use this checklist to track your migration progress from GitHub Pages to Vercel with custom domain.

---

## Phase 1: Pre-Migration ⏳

- [ ] Google AdSense verified on GitHub Pages
- [ ] Custom domain purchased (e.g., mystockscreener.com)
- [ ] Domain DNS control panel access confirmed
- [ ] Vercel account created
- [ ] All current features tested and working on GitHub Pages

**Status:** _____ / 5 completed

---

## Phase 2: Vercel Setup 🔧

- [ ] Connected GitHub account to Vercel
- [ ] Imported stock-screener repository to Vercel
- [ ] First deployment successful on vercel.app subdomain
- [ ] Tested all pages on vercel.app URL
- [ ] Verified GitHub Actions still running

**Status:** _____ / 5 completed

**Vercel URL:** https://_________________.vercel.app

---

## Phase 3: Domain Configuration 🌐

- [ ] Added custom domain in Vercel dashboard
- [ ] Added www subdomain in Vercel dashboard
- [ ] Configured A record at domain registrar (@ → 76.76.21.21)
- [ ] Configured CNAME record (www → cname.vercel-dns.com)
- [ ] DNS propagation completed (check: dnschecker.org)
- [ ] Custom domain loads correctly with HTTPS

**Status:** _____ / 6 completed

**Custom Domain:** https://_________________

**DNS Propagation Check:** https://dnschecker.org/?domain=_________________

---

## Phase 4: Update Code 📝

- [ ] Ran `python update_domain.py yourdomain.com`
- [ ] Reviewed changes with `git diff`
- [ ] Verified sitemap.xml updated
- [ ] Verified index.html og:url updated
- [ ] Verified home.html og:url updated
- [ ] Committed changes
- [ ] Pushed to GitHub
- [ ] Vercel auto-deployed new version

**Status:** _____ / 8 completed

**Commands used:**
```bash
python update_domain.py _________________
git add .
git commit -m "Update domain to custom domain"
git push origin main
```

---

## Phase 5: Make Repository Private 🔒

- [ ] Verified GitHub Actions settings for private repo
- [ ] Confirmed GitHub Actions minutes available (free: 2000/month)
- [ ] Changed repository visibility to Private
- [ ] Verified Vercel still has access
- [ ] Tested a deployment after making private
- [ ] Confirmed GitHub Actions still run 4x daily

**Status:** _____ / 6 completed

**Repository Status:** [ ] Public  [ ] Private

---

## Phase 6: Google AdSense 💰

- [ ] Logged into AdSense account
- [ ] Added new custom domain to Sites
- [ ] Waited 24-48 hours for verification
- [ ] Received domain verification confirmation email
- [ ] Created ad units for each page (4 total)
- [ ] Replaced ad placeholders with live ad code
- [ ] Tested ads display on all pages
- [ ] Verified clicks and impressions in AdSense dashboard

**Status:** _____ / 8 completed

**Ad Units Created:**
- [ ] Home Page Banner (index.html) - Slot ID: __________
- [ ] Hot Stocks Banner (hot-stocks.html) - Slot ID: __________
- [ ] Watch List Banner (watch-list.html) - Slot ID: __________
- [ ] Export Top Banner (export.html) - Slot ID: __________
- [ ] Export Bottom Banner (export.html) - Slot ID: __________

---

## Phase 7: SEO Setup 🔍

- [ ] Added site to Google Search Console
- [ ] Verified domain ownership in Search Console
- [ ] Submitted sitemap.xml to Search Console
- [ ] Requested indexing for main pages
- [ ] Set up URL removal for old GitHub Pages URLs
- [ ] Added redirect on old GitHub Pages (optional)
- [ ] Verified no crawl errors in Search Console

**Status:** _____ / 7 completed

**Search Console:** https://search.google.com/search-console

---

## Phase 8: Final Testing ✅

### Functionality Tests
- [ ] Home page loads correctly
- [ ] Hot Stocks page displays and paginates
- [ ] Watch List page displays and paginates
- [ ] Export page downloads work (JSON & CSV)
- [ ] Failed Tickers page displays
- [ ] Search functionality works across pages
- [ ] Navigation between pages works
- [ ] Timestamp displays correctly (New York time)
- [ ] GitHub Actions run on schedule (4x daily Mon-Fri)
- [ ] Results update automatically

**Status:** _____ / 10 completed

### Mobile Tests
- [ ] Home page responsive on mobile
- [ ] Stock cards display properly on mobile
- [ ] Navigation menu works on mobile
- [ ] Search works on mobile
- [ ] Pagination works on mobile (10 stocks/page)
- [ ] Export buttons work on mobile
- [ ] Ads display correctly on mobile

**Status:** _____ / 7 completed

### Performance Tests
- [ ] Page load speed < 2 seconds
- [ ] All images/resources load
- [ ] No console errors in browser
- [ ] HTTPS certificate valid
- [ ] All external links work

**Status:** _____ / 5 completed

---

## Phase 9: Monitoring 📊

### Week 1 Checks
- [ ] Day 1: All pages accessible
- [ ] Day 2: GitHub Actions ran successfully
- [ ] Day 3: AdSense impressions showing
- [ ] Day 4: Search Console indexing started
- [ ] Day 7: Check Google Analytics (if added)

### Week 2 Checks
- [ ] Day 10: Review AdSense earnings
- [ ] Day 12: Check Search Console for errors
- [ ] Day 14: Verify mobile usability report

### Monthly Checks
- [ ] Month 1: Review site performance
- [ ] Month 1: Optimize based on AdSense data
- [ ] Month 1: Check Core Web Vitals

---

## 🎯 Success Metrics

**Traffic Goals:**
- Search Console impressions: _____ (target)
- Average daily visitors: _____ (target)

**AdSense Goals:**
- Daily impressions: _____ (target)
- Click-through rate: _____ % (target)
- Monthly earnings: $_____ (target)

**Performance Goals:**
- Page load time: < 2 seconds ✅
- Mobile friendly score: 100/100 ✅
- SEO score: _____ / 100

---

## 📞 Important Links

**Vercel:**
- Dashboard: https://vercel.com/dashboard
- Project: https://vercel.com/_________/stock-screener
- Analytics: https://vercel.com/_________/stock-screener/analytics

**Google Services:**
- AdSense: https://adsense.google.com
- Search Console: https://search.google.com/search-console
- Analytics: https://analytics.google.com (if added)

**Domain:**
- Registrar: _________________
- DNS Management: _________________

**GitHub:**
- Repository: https://github.com/achikam-mor/stock-screener
- Actions: https://github.com/achikam-mor/stock-screener/actions

---

## 🚨 Troubleshooting

### If GitHub Actions fail:
1. Check Settings → Actions → General
2. Verify Actions enabled for private repo
3. Check Actions minutes usage
4. Review workflow logs

### If Vercel deployment fails:
1. Check build logs in Vercel dashboard
2. Verify Git integration is connected
3. Try manual deployment
4. Contact Vercel support

### If AdSense not showing:
1. Wait 24-48 hours after adding code
2. Check domain is verified in AdSense
3. Verify ad slot IDs are correct
4. Check browser ad-blocker isn't blocking

### If domain not loading:
1. Check DNS propagation: dnschecker.org
2. Verify DNS records are correct
3. Clear browser cache
4. Wait up to 48 hours

---

## ✅ Migration Complete!

**Date Completed:** _______________

**Final URL:** https://_________________

**Deployment Status:** 
- [ ] Live on custom domain
- [ ] HTTPS active
- [ ] Repository private
- [ ] AdSense monetized
- [ ] GitHub Actions running
- [ ] SEO optimized

**Congratulations! Your stock screener is now professional, private, and monetized! 🎉**

---

## 📝 Notes

Use this space for any issues, observations, or reminders:

_______________________________________________

_______________________________________________

_______________________________________________

_______________________________________________
