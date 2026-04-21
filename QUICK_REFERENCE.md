# 🚀 Quick Migration Reference Card

## Essential Commands

```bash
# 1. Update domain URLs
python update_domain.py yourdomain.com

# 2. Review changes
git diff

# 3. Commit and push
git add .
git commit -m "Migrate to custom domain on Vercel"
git push origin main

# 4. Check deployment status
# Visit your Vercel dashboard - auto-deploys on push!
```

---

## DNS Records (Add at your domain registrar)

**For apex domain (example.com):**
```
Type: A
Name: @
Value: 76.76.21.21
TTL: Auto
```

**For www subdomain:**
```
Type: CNAME  
Name: www
Value: cname.vercel-dns.com
TTL: Auto
```

---

## Files That Need Updating

1. ✅ `sitemap.xml` - All URLs
2. ✅ `index.html` - og:url meta tag
3. ✅ `home.html` - og:url meta tag

**Use the automated script:** `python update_domain.py yourdomain.com`

---

## Private Repo Settings

**Before making private, check:**

1. Settings → Actions → General
2. Ensure "Allow all actions and reusable workflows" is selected
3. Verify you have GitHub Actions minutes (free: 2000/month)

**After making private:**
- Vercel still has access ✅
- GitHub Actions still run ✅
- Everything works the same ✅

---

## Vercel Configuration Files

- ✅ `vercel.json` - Already created for you
- ✅ `.gitignore` - Updated with .vercel

**No other config needed!** Vercel auto-detects static sites.

---

## AdSense After Migration

**3 Simple Steps:**

1. **Add domain:** AdSense → Sites → Add site → Enter yourdomain.com
2. **Wait:** 24-48 hours for verification (code already in HTML)
3. **Activate ads:** Create ad units, replace placeholders

**Your publisher ID:** `ca-pub-9520776475659458` ✅ (stays the same)

---

## Critical Timeline

| Action | Time Required |
|--------|---------------|
| Vercel deployment | 30 seconds ⚡ |
| DNS propagation | 1-48 hours ⏳ |
| AdSense verification | 24-48 hours ⏳ |
| Google indexing | 1-7 days 🔍 |

---

## Important URLs to Bookmark

- **Vercel:** https://vercel.com/dashboard
- **AdSense:** https://adsense.google.com
- **Search Console:** https://search.google.com/search-console
- **DNS Checker:** https://dnschecker.org

---

## Cost Summary

**One-Time:**
- Domain: ~$10-15/year 💵

**Monthly:**
- Vercel: $0 (free tier) ✅
- GitHub: $0 (free tier) ✅
- AdSense: $0 ✅

**Total: ~$1.25/month** (domain only)

**Expected AdSense Revenue:** Varies, but could exceed domain cost! 💰

---

## Quick Troubleshooting

**Problem:** GitHub Actions fail after private
- **Fix:** Settings → Actions → Enable for private repo

**Problem:** Domain not loading
- **Fix:** Wait for DNS (check dnschecker.org)

**Problem:** Vercel can't access repo
- **Fix:** Vercel settings → Git → Reconnect

**Problem:** AdSense not showing ads
- **Fix:** Wait 24-48 hours, check domain verified

---

## Success Indicators ✅

After migration, verify:
- [ ] Custom domain loads with HTTPS
- [ ] All pages work correctly
- [ ] GitHub Actions run 4x daily
- [ ] Results update automatically
- [ ] AdSense shows impressions
- [ ] Mobile responsive works

---

## Getting Help

**Vercel Support:** 
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support
- Very responsive! Usually < 1 hour

**GitHub Support:**
- Docs: https://docs.github.com
- Community: https://github.community

**AdSense Help:**
- Help Center: https://support.google.com/adsense
- Forum: https://support.google.com/adsense/community

---

## Pro Tips 💡

1. **Test on vercel.app first** before adding custom domain
2. **Keep GitHub Pages active** with redirect for 1 month
3. **Monitor Core Web Vitals** in Search Console
4. **Enable Vercel Analytics** (free, insightful)
5. **Set up email alerts** in AdSense and Search Console

---

**Print this card or keep it handy during migration! 🎯**
