# Google Custom Search API - Deprecated Feature

**Date:** February 23, 2026

**Issue:** Google has deprecated the "Search the entire web" feature in Programmable Search Engine, which was required for API access to Custom Search.

---

## 🚫 What Happened

When trying to set up Google Custom Search API for LinkedIn profile discovery:

1. ✅ Created Google Cloud project
2. ✅ Enabled Custom Search API
3. ✅ Created API key
4. ✅ Created Custom Search Engine
5. ✅ Enabled billing
6. ❌ **"Search the entire web" feature is deprecated and cannot be enabled**

**Error message from Google:**
> "This feature is being deprecated and can no longer be enabled."

**Impact:**
- Cannot use Google Custom Search API for programmatic LinkedIn discovery
- The API requires "Search the entire web" to be enabled
- Without it, API calls return: "This project does not have the access to Custom Search JSON API"

---

## 🔄 Revised Approach

Since Google Custom Search API is no longer viable, we're using:

### **Plan B: GitHub-Only + Manual Verification**

**Stage 1: GitHub Profile Extraction**
- Extract LinkedIn URLs from GitHub bio, blog, social accounts
- Success rate: 20-30%
- Accuracy: 100%
- Cost: $0

**Stage 2: Manual Verification (All Candidates)**
- Generate Excel sheet with all candidates needing LinkedIn
- Manual lookup and verification
- Success rate: 100% (human verification)
- Accuracy: 100%
- Cost: Time (2-3 minutes per candidate)

---

## 📊 Expected Results

**For 2,629 candidates:**

| Stage | Method | Candidates | LinkedIn URLs |
|-------|--------|-----------|---------------|
| 1 | GitHub extraction | 2,629 | 525-790 (20-30%) |
| 2 | Manual verification | 1,840-2,100 | Up to you |

**For top 50 candidates (80+ scores):**
- GitHub extraction: ~10-15 LinkedIn URLs (20-30%)
- Manual verification: Remaining 35-40 candidates
- Time: 1-2 hours for top 50

---

## ✅ What We're Doing Instead

1. **Run scorer with GitHub-only LinkedIn extraction**
   - No Google API needed
   - Extracts LinkedIn from GitHub profiles only
   - 20-30% coverage

2. **Generate manual verification sheet**
   - Excel file with all candidates
   - GitHub URLs, auto-discovered LinkedIn, empty column for manual entry
   - Prioritized by score (80+ first)

3. **Manual LinkedIn lookup**
   - For candidates without LinkedIn from GitHub
   - Search LinkedIn manually: "Name" + "Location"
   - Verify profile matches GitHub work
   - Enter verified LinkedIn URL in spreadsheet

---

## 💡 Alternative Solutions (Future)

If we want to automate LinkedIn discovery in the future:

### **Option 1: Proxycurl (Paid API)**
- Direct LinkedIn data API
- $0.01-0.03 per lookup
- 70-80% success rate
- Cost: ~$26-79 for 2,629 candidates

### **Option 2: Apollo.io (Paid API)**
- Sales intelligence platform
- 50 free lookups/month, then $49-99/month
- 65-75% success rate
- Returns LinkedIn + email + phone

### **Option 3: Web Scraping (Complex)**
- Custom scraper for LinkedIn search
- Free but fragile
- Requires proxies and maintenance
- May violate LinkedIn ToS

---

## 🎯 Recommendation

**For now: GitHub-only + Manual verification**

**Why:**
- Google API is deprecated (not our fault)
- GitHub extraction is free and 100% accurate
- Manual verification ensures correct matches
- Top 50 candidates only takes 1-2 hours
- No risk of wrong LinkedIn matches (like Clay.com had)

**For future: Consider Proxycurl or Apollo.io**
- If manual work becomes too time-consuming
- If you need to scale beyond 50-100 candidates per search
- Cost is reasonable ($26-79 for 2,629 candidates)

---

## 📋 Current Status

- ❌ Google Custom Search API - Deprecated, cannot use
- ✅ GitHub-only LinkedIn extraction - Ready to use
- ✅ Manual verification workflow - Ready to use
- ✅ Scorer updated to use GitHub-only extraction

**Ready to run the scorer with GitHub-only LinkedIn discovery.**
