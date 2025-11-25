# Custom Domain Migration Guide
## From GitHub Pages to Vercel with Custom Domain

This guide covers migrating your stock screener from `achikam-mor.github.io/stock-screener` to your custom domain on Vercel.

---

## 📋 Pre-Migration Checklist

- [ ] Google AdSense account verified and approved on GitHub Pages
- [ ] Custom domain purchased (e.g., `mystockscreener.com`)
- [ ] Vercel account created (free plan works great)
- [ ] Domain DNS access available

---

## 🚀 Step-by-Step Migration Process

### Phase 1: Prepare Vercel Deployment

#### 1.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub account
3. Grant Vercel access to your repositories

#### 1.2 Import Your Repository (While Still Public)
1. Click "Add New" → "Project"
2. Select `stock-screener` repository
3. Configure build settings:
   - **Framework Preset:** Other
   - **Build Command:** (leave empty - static site)
   - **Output Directory:** `./` (root directory)
   - **Install Command:** (leave empty)
4. Click "Deploy"
5. Wait for initial deployment (gets a vercel.app URL)

#### 1.3 Test on Vercel
- Visit your `your-project.vercel.app` URL
- Test all pages work correctly
- Verify GitHub Actions still run (they work with private repos if you keep Actions enabled)

### Phase 2: Domain Configuration

#### 2.1 Add Custom Domain to Vercel
1. In Vercel dashboard, go to your project
2. Settings → Domains
3. Add your domain: `mystockscreener.com`
4. Also add: `www.mystockscreener.com` (recommended)

#### 2.2 Configure DNS Records
Vercel will show you DNS records to add. At your domain registrar (GoDaddy, Namecheap, etc.):

**For apex domain (mystockscreener.com):**
```
Type: A
Name: @
Value: 76.76.21.21
```

**For www subdomain:**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**Wait 24-48 hours for DNS propagation** (usually faster)

### Phase 3: Update Your Code

#### 3.1 Update URLs in Your Files

Run the provided `update_domain.py` script (see below) or manually update:

**Files to update:**
1. `sitemap.xml` - All URLs
2. `index.html` - `og:url` meta tag
3. `home.html` - `og:url` meta tag

#### 3.2 Commit and Push Changes
```bash
git add .
git commit -m "Update domain to mystockscreener.com"
git push origin main
```

Vercel auto-deploys on every push!

### Phase 4: Make Repository Private

#### 4.1 Enable GitHub Actions for Private Repo
**IMPORTANT:** Before making private, ensure GitHub Actions will continue:

1. Go to repository Settings → Actions → General
2. Under "Fork pull request workflows from outside collaborators":
   - Select "Require approval for all outside collaborators"
3. Ensure you have GitHub Actions minutes available (free tier: 2000 min/month)

#### 4.2 Make Repository Private
1. Go to repository Settings → General
2. Scroll to bottom: "Danger Zone"
3. Click "Change visibility" → "Make private"
4. Confirm the action

#### 4.3 Verify Vercel Still Has Access
1. Vercel should maintain access to private repos
2. Check deployments continue to work
3. If issues, reconnect in Vercel → Account Settings → Git Integration

### Phase 5: Google AdSense Setup

#### 5.1 Add New Domain to AdSense
1. Log into [adsense.google.com](https://adsense.google.com)
2. Go to Sites → Add site
3. Enter your new domain: `mystockscreener.com`
4. Click "Save and continue"

#### 5.2 Verify New Domain
- Your existing AdSense code is already in the HTML files ✅
- Google will crawl your new domain automatically
- Verification typically takes 24-48 hours
- You'll receive email when approved

#### 5.3 Activate Ad Units
Once verified, replace ad placeholders with live ads:

**In each HTML file, replace:**
```html
<!-- Current placeholder: -->
<div class="ad-placeholder">Advertisement</div>

<!-- Replace with: -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-9520776475659458"
     data-ad-slot="YOUR_AD_SLOT_ID_HERE"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
```

**Create ad units in AdSense dashboard:**
- Home Page Banner
- Stock List Banner  
- Export Page Top Banner
- Export Page Bottom Banner

Copy each ad unit's `data-ad-slot` ID into the corresponding HTML file.

### Phase 6: SEO & Analytics

#### 6.1 Google Search Console
1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Add new property: `mystockscreener.com`
3. Verify domain ownership (DNS TXT record or HTML file)
4. Submit sitemap: `https://mystockscreener.com/sitemap.xml`
5. Request indexing for main pages

#### 6.2 Update Old GitHub Pages (Optional)
Add a redirect page to your old GitHub Pages site:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=https://mystockscreener.com">
    <title>Redirecting...</title>
</head>
<body>
    <p>This site has moved to <a href="https://mystockscreener.com">mystockscreener.com</a></p>
</body>
</html>
```

---

## 🛠️ Automated Domain Update Script

Save this as `update_domain.py` in your project root:

```python
# See update_domain.py file
```

**Usage:**
```bash
python update_domain.py mystockscreener.com
```

---

## ✅ Post-Migration Verification

### Test Everything:
- [ ] All pages load on new domain
- [ ] Navigation works correctly
- [ ] Search functionality works
- [ ] Export downloads work
- [ ] GitHub Actions still run 4x daily
- [ ] Results update properly
- [ ] Mobile responsive design intact
- [ ] AdSense ads display (after approval)

### Monitor Performance:
- [ ] Google Search Console shows no errors
- [ ] AdSense dashboard shows impressions
- [ ] Check Core Web Vitals in Search Console
- [ ] Monitor uptime (Vercel has 99.99% uptime)

---

## 🎯 Vercel Benefits vs GitHub Pages

| Feature | GitHub Pages | Vercel |
|---------|--------------|--------|
| Custom Domain | ✅ | ✅ |
| HTTPS/SSL | ✅ | ✅ Better (auto) |
| Private Repo | ❌ | ✅ Yes! |
| Build Time | Slower | ⚡ Super fast |
| Global CDN | Limited | ✅ Excellent |
| Analytics | Need 3rd party | ✅ Built-in |
| Serverless Functions | ❌ | ✅ Available |
| Preview Deployments | ❌ | ✅ For every PR |
| Deploy Speed | ~2 min | ⚡ ~30 sec |

---

## 💰 Cost Breakdown

### Free Forever:
- ✅ Vercel Hobby Plan (perfect for your use case)
- ✅ GitHub private repository
- ✅ GitHub Actions (2000 min/month free)
- ✅ Vercel bandwidth (100 GB/month)
- ✅ SSL certificate (auto-renewed)

### You Only Pay For:
- 💵 Domain name (~$10-15/year)
- 💵 Optional: Vercel Pro if you exceed free tier ($20/month)

**For your stock screener:** Free tier is more than enough!

---

## 🚨 Common Issues & Solutions

### Issue: GitHub Actions fail after making repo private
**Solution:** Ensure Actions are enabled in Settings → Actions

### Issue: Vercel can't access private repo
**Solution:** Reconnect in Vercel Settings → Git Integration → Reinstall

### Issue: DNS not propagating
**Solution:** Wait 24-48 hours, check with [dnschecker.org](https://dnschecker.org)

### Issue: AdSense not showing ads
**Solution:** 
1. Check domain is verified in AdSense
2. Verify ad code has correct `data-ad-slot` ID
3. Wait 24 hours after adding code
4. Check AdSense account isn't limited

### Issue: Old GitHub Pages still showing in Google
**Solution:** 
1. Submit new domain to Search Console
2. Request removal of old URLs in Search Console
3. Add 301 redirect on old site
4. Wait 2-4 weeks for Google to update

---

## 📞 Support Resources

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **Vercel Support:** [vercel.com/support](https://vercel.com/support)
- **AdSense Help:** [support.google.com/adsense](https://support.google.com/adsense)
- **Domain DNS Help:** Your registrar's support

---

## 🎉 Success Checklist

Once complete, you'll have:
- ✅ Professional custom domain
- ✅ Private repository (code protected)
- ✅ Faster deployments with Vercel
- ✅ Global CDN for better performance
- ✅ Google AdSense monetization active
- ✅ Automatic HTTPS/SSL
- ✅ GitHub Actions still running
- ✅ Better SEO with custom domain

**Estimated Total Migration Time:** 2-4 hours (plus DNS/AdSense wait times)

---

## 📝 Quick Reference Commands

```bash
# Test locally
python main.py

# Update domain URLs
python update_domain.py yourdomain.com

# Commit changes
git add .
git commit -m "Migrate to custom domain"
git push origin main

# Check deployment
# Vercel auto-deploys, check dashboard
```

---

**Questions?** Feel free to ask! 🚀
