# LinkedIn Profile Discovery Alternatives to Clay.com

**Date:** February 23, 2026

---

## 🎯 The Problem

**Current situation:**
- GitHub profiles don't always contain LinkedIn URLs
- Guessing LinkedIn URLs from GitHub usernames doesn't work (URLs don't exist)
- Clay.com works but requires manual upload and processing
- Need automated way to find LinkedIn profiles for candidates

---

## 🔍 Alternative Methods to Discover LinkedIn Profiles

### **1. GitHub Profile Data (Current - Limited Success)**

**What we extract:**
- Bio/description field
- Blog/website field
- Social accounts (GitHub API)

**Success rate:** ~20-30% (only if developer explicitly links LinkedIn)

**Pros:**
- Free
- Fast
- No API limits

**Cons:**
- Low coverage
- Many developers don't link LinkedIn

---

### **2. Google Search API (Automated)**

**How it works:**
```python
# Search Google for: "GitHub username" + "LinkedIn"
query = f'"{github_username}" site:linkedin.com/in'
# Or: "Full Name" + "Location" + "LinkedIn"
query = f'"{full_name}" "{location}" site:linkedin.com/in'
```

**APIs available:**
- Google Custom Search API (100 free queries/day, $5/1000 after)
- SerpAPI ($50/month for 5,000 searches)
- ScraperAPI + Google ($29/month for 10,000 requests)

**Success rate:** ~50-60% (if name + location available)

**Pros:**
- Automated
- Good success rate with name + location
- Relatively cheap

**Cons:**
- Requires API key
- Rate limits
- May return wrong person (common names)
- Needs verification

---

### **3. Hunter.io (Email → LinkedIn)**

**How it works:**
```python
# 1. Use Hunter.io to find email from GitHub name + company
email = hunter.find_email(name="Michael Merrill", company="Google")

# 2. Search LinkedIn by email (if accessible)
# Or use email to verify LinkedIn profile
```

**Pricing:**
- Free: 25 searches/month
- Starter: $49/month for 500 searches
- Growth: $99/month for 2,500 searches

**Success rate:** ~40-50% (if company known)

**Pros:**
- You already have Hunter.io API key
- Good for finding emails
- Can help verify LinkedIn profiles

**Cons:**
- Requires company information
- Limited free tier
- Doesn't directly find LinkedIn

---

### **4. Proxycurl (LinkedIn API Alternative)**

**What it is:** LinkedIn data API (scrapes LinkedIn legally)

**How it works:**
```python
# Search for LinkedIn profile by name + company
profile = proxycurl.search_person(
    name="Michael Merrill",
    company="Google",
    location="New York"
)
# Returns LinkedIn URL + full profile data
```

**Pricing:**
- $0.01 per profile lookup
- $0.03 per full profile enrichment
- No monthly minimum

**Success rate:** ~70-80% (with name + company)

**Pros:**
- Direct LinkedIn access
- High success rate
- Pay-per-use (no monthly fee)
- Returns full profile data (experience, skills, etc.)

**Cons:**
- Costs money ($0.01-0.03 per candidate)
- Requires name + company for best results
- May violate LinkedIn ToS (gray area)

---

### **5. RocketReach**

**What it is:** Contact information database

**How it works:**
- Search by name + company
- Returns email, phone, LinkedIn URL

**Pricing:**
- Essentials: $53/month for 170 lookups
- Pro: $105/month for 375 lookups
- Ultimate: $249/month for 1,000 lookups

**Success rate:** ~60-70%

**Pros:**
- Returns email + phone + LinkedIn
- Good database coverage
- Automated API

**Cons:**
- Expensive
- Monthly commitment
- Lower success rate than Proxycurl

---

### **6. Apollo.io**

**What it is:** Sales intelligence platform with LinkedIn data

**How it works:**
- Search by name + company + title
- Returns LinkedIn URL + contact info

**Pricing:**
- Free: 50 credits/month
- Basic: $49/month for 1,200 credits
- Professional: $99/month for 12,000 credits

**Success rate:** ~65-75%

**Pros:**
- Good free tier (50/month)
- Returns contact info + LinkedIn
- Good for B2B/recruiting

**Cons:**
- Requires company/title for best results
- Credits system can be confusing

---

### **7. Clearbit (Name + Email → LinkedIn)**

**What it is:** Data enrichment API

**How it works:**
```python
# Enrich email to get LinkedIn
profile = clearbit.enrich(email="michael@example.com")
# Returns LinkedIn URL + company + title
```

**Pricing:**
- $99/month for 2,500 enrichments
- $249/month for 10,000 enrichments

**Success rate:** ~50-60% (requires email)

**Pros:**
- Good enrichment data
- Returns LinkedIn + company info

**Cons:**
- Requires email first
- Expensive
- Lower success rate

---

### **8. Custom Web Scraping (Advanced)**

**How it works:**
```python
# 1. Search Google for LinkedIn profile
# 2. Scrape LinkedIn search results
# 3. Verify profile matches (name, location, company)
```

**Tools:**
- Selenium + BeautifulSoup
- Playwright
- Scrapy

**Success rate:** ~60-70% (with good matching logic)

**Pros:**
- Free (except infrastructure)
- Full control
- Can customize matching logic

**Cons:**
- Complex to build
- Fragile (breaks when sites change)
- May violate ToS
- Requires proxies to avoid blocking
- Time-consuming to maintain

---

## 🎯 Recommended Solution

### **For Your Use Case (2,629 candidates):**

**Option 1: Proxycurl (Best ROI)**
- **Cost:** $26-79 for 2,629 candidates ($0.01-0.03 each)
- **Success rate:** 70-80%
- **Result:** ~1,850-2,100 LinkedIn URLs
- **Pros:** Pay-per-use, high success, full profile data
- **Cons:** Costs money, gray area legally

**Option 2: Google Custom Search API (Cheapest)**
- **Cost:** $10-15 for 2,629 searches ($5/1000)
- **Success rate:** 50-60%
- **Result:** ~1,300-1,575 LinkedIn URLs
- **Pros:** Cheap, automated, legal
- **Cons:** Needs verification, may find wrong people

**Option 3: Apollo.io Free Tier + Paid (Balanced)**
- **Cost:** $0 for first 50, then $49-99/month
- **Success rate:** 65-75%
- **Result:** ~1,700-1,970 LinkedIn URLs
- **Pros:** Good free tier, contact info included
- **Cons:** Monthly commitment, requires company/title

---

## 💡 Hybrid Approach (Recommended)

**Step 1: GitHub Profile Extraction (Free)**
- Extract LinkedIn from bio/blog/social
- Success: ~500-600 candidates (20-25%)
- Cost: $0

**Step 2: Google Custom Search API (Cheap)**
- Search for remaining ~2,000 candidates
- Success: ~1,000-1,200 more (50-60% of remaining)
- Cost: ~$10

**Step 3: Clay.com for Remaining (Manual)**
- Upload ~800 candidates without LinkedIn
- Clay finds ~300-400 more
- Cost: Clay credits

**Total Result:**
- ~1,800-2,200 LinkedIn URLs (70-85% coverage)
- Cost: ~$10 + Clay credits
- Time: Mostly automated

---

## 🚀 Implementation Plan

### **Quick Win (1 hour):**
1. Keep GitHub profile extraction (already done)
2. Add Google Custom Search API integration
3. Re-score with verified LinkedIn URLs only

### **Complete Solution (3 hours):**
1. GitHub profile extraction
2. Google Custom Search API
3. Proxycurl for high-value candidates (80+ scores)
4. Clay.com for remaining

---

## 📊 Cost Comparison

| Method | Cost for 2,629 candidates | Success Rate | LinkedIn URLs Found |
|--------|---------------------------|--------------|---------------------|
| GitHub only | $0 | 20-25% | 500-650 |
| + Google Search | $10 | 50-60% | 1,300-1,575 |
| + Proxycurl | $36 | 70-80% | 1,850-2,100 |
| + Clay.com | $10 + Clay | 75-85% | 1,970-2,235 |

---

## 🎯 My Recommendation

**Use Google Custom Search API:**

**Why:**
- Cheap ($10 for all 2,629 candidates)
- Automated (no manual work)
- Legal (using Google's official API)
- Good success rate (50-60%)
- Easy to implement (1 hour)

**Implementation:**
```python
from googleapiclient.discovery import build

def find_linkedin_via_google(name, location, github_username):
    # Search: "Name Location site:linkedin.com/in"
    query = f'"{name}" "{location}" site:linkedin.com/in'
    results = google_search(query)
    # Return first LinkedIn URL found
    return extract_linkedin_from_results(results)
```

**Want me to implement Google Custom Search API integration?**
