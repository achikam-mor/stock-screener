#!/usr/bin/env python3
"""
Automated Domain Update Script
Updates all URLs in your project files from old domain to new custom domain.

Usage:
    python update_domain.py yourdomain.com
    python update_domain.py mystockscreener.com
"""

import sys
import re
from pathlib import Path

def update_domain(new_domain):
    """Update domain in all relevant files"""
    
    # Remove protocol if provided
    new_domain = new_domain.replace('https://', '').replace('http://', '').strip('/')
    
    # Files to update
    files_to_update = {
        'sitemap.xml': {
            'pattern': r'https://achikam-mor\.github\.io/stock-screener',
            'replacement': f'https://{new_domain}'
        },
        'index.html': {
            'pattern': r'<meta property="og:url" content="https://achikam-mor\.github\.io/stock-screener/"',
            'replacement': f'<meta property="og:url" content="https://{new_domain}/"'
        },
        'home.html': {
            'pattern': r'<meta property="og:url" content="https://achikam-mor\.github\.io/stock-screener/"',
            'replacement': f'<meta property="og:url" content="https://{new_domain}/"'
        }
    }
    
    print(f"🚀 Updating domain to: {new_domain}\n")
    
    updates_made = 0
    errors = []
    
    for filename, config in files_to_update.items():
        filepath = Path(filename)
        
        if not filepath.exists():
            errors.append(f"❌ {filename} not found")
            continue
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count matches
            matches = len(re.findall(config['pattern'], content))
            
            if matches == 0:
                print(f"⚠️  {filename}: No URLs found to update (already updated?)")
                continue
            
            # Replace
            new_content = re.sub(config['pattern'], config['replacement'], content)
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ {filename}: Updated {matches} URL(s)")
            updates_made += matches
            
        except Exception as e:
            errors.append(f"❌ Error updating {filename}: {str(e)}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Successfully updated {updates_made} URL(s)")
    
    if errors:
        print(f"\n⚠️  Errors encountered:")
        for error in errors:
            print(f"   {error}")
    
    print(f"\n📝 Next steps:")
    print(f"   1. Review changes: git diff")
    print(f"   2. Test locally if possible")
    print(f"   3. Commit: git add . && git commit -m 'Update domain to {new_domain}'")
    print(f"   4. Push: git push origin main")
    print(f"   5. Vercel will auto-deploy!")
    print(f"\n🎯 Don't forget to:")
    print(f"   - Add {new_domain} to Vercel dashboard")
    print(f"   - Configure DNS records at your registrar")
    print(f"   - Add {new_domain} to Google AdSense")
    print(f"   - Submit sitemap to Google Search Console")

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python update_domain.py yourdomain.com")
        print("\nExample:")
        print("   python update_domain.py mystockscreener.com")
        sys.exit(1)
    
    new_domain = sys.argv[1]
    
    # Validate domain format
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$', new_domain):
        print(f"❌ Invalid domain format: {new_domain}")
        print("   Expected format: example.com or subdomain.example.com")
        sys.exit(1)
    
    # Confirm
    print(f"\n⚠️  This will update all URLs in your project files")
    print(f"   Old: https://achikam-mor.github.io/stock-screener")
    print(f"   New: https://{new_domain}")
    
    confirm = input("\n   Continue? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled")
        sys.exit(0)
    
    print()
    update_domain(new_domain)

if __name__ == "__main__":
    main()
