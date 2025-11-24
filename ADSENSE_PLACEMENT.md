# Google AdSense Placement Strategy

## Ad Locations Overview

### 1. **Home Page (index.html / home.html)**
   - **Top Banner Ad**: Placed between the search box and the welcome content
   - **Position**: After summary cards, highly visible
   - **Ad Type**: 728x90 Leaderboard (desktop) / 320x50 Mobile Banner
   - **Rationale**: Catches user attention after they view the summary statistics

### 2. **Hot Stocks Page (hot-stocks.html)**
   - **Content Banner Ad**: Placed between page info and stock listings
   - **Position**: Above stock cards, after pagination info
   - **Ad Type**: 728x90 Leaderboard (desktop) / 320x50 Mobile Banner
   - **Rationale**: High engagement area - users are actively browsing stocks

### 3. **Watch List Page (watch-list.html)**
   - **Content Banner Ad**: Placed between page info and stock listings
   - **Position**: Same as Hot Stocks for consistency
   - **Ad Type**: 728x90 Leaderboard (desktop) / 320x50 Mobile Banner
   - **Rationale**: Consistent placement across stock list pages

### 4. **Export Page (export.html)**
   - **Top Banner Ad**: Above export options
   - **Bottom Banner Ad**: Below all export sections
   - **Position**: Strategic placement for download page
   - **Ad Type**: 728x90 Leaderboard (desktop) / 320x50 Mobile Banner
   - **Rationale**: Users spend time on this page choosing downloads

### 5. **Failed Tickers Page (failed-tickers.html)**
   - **No ads currently**: Low engagement page
   - **Future consideration**: Could add footer banner if traffic increases

## Responsive Design

### Desktop (>768px):
- Ad size: 728x90 (Leaderboard)
- Full width banner style
- Centered with max-width constraint

### Mobile (≤768px):
- Ad size: 320x50 (Mobile Banner)
- Reduced height (50px vs 90px)
- Maintains center alignment
- Reduced padding for better UX

## CSS Implementation

```css
.ad-container {
    display: flex;
    justify-content: center;
    margin: 20px 0;
}

.ad-banner {
    min-height: 90px;
    background: var(--bg-card);
    border: 1px dashed var(--border-color);
    border-radius: 8px;
    width: 100%;
    max-width: 728px;
}

@media (max-width: 768px) {
    .ad-container.ad-banner {
        min-height: 50px;
        margin: 15px 0;
    }
}
```

## Next Steps to Activate Ads

Once your Google AdSense account is verified (24-48 hours):

1. **Replace placeholders** with actual AdSense code:
   ```html
   <!-- Replace this: -->
   <div class="ad-placeholder">Advertisement</div>
   
   <!-- With this: -->
   <ins class="adsbygoogle"
        style="display:block"
        data-ad-client="ca-pub-9520776475659458"
        data-ad-slot="YOUR_AD_SLOT_ID"
        data-ad-format="auto"
        data-full-width-responsive="true"></ins>
   <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
   </script>
   ```

2. **Create ad units** in AdSense dashboard:
   - Home Banner
   - Stock List Banner
   - Export Top Banner
   - Export Bottom Banner

3. **Test on mobile** to ensure ads don't disrupt UX

4. **Monitor performance** in AdSense dashboard

## Best Practices Implemented

✅ **Non-intrusive**: Ads don't block content or navigation
✅ **Responsive**: Different sizes for mobile vs desktop
✅ **Strategic placement**: High visibility without disrupting user flow
✅ **Limited quantity**: 1-2 ads per page to maintain user experience
✅ **Visual separation**: Clear borders and spacing around ad containers
✅ **Accessibility**: Proper semantic HTML structure maintained

## Performance Considerations

- Ads load asynchronously (won't block page rendering)
- Placeholder divs maintain layout stability
- Mobile users get smaller, less intrusive ad sizes
- Ad placement optimized for viewability metrics
