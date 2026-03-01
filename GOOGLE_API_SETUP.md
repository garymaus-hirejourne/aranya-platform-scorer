# Google Custom Search API Setup Guide

**Goal:** Enable automated LinkedIn profile discovery using Google search

**Cost:** $5 per 1,000 searches (100 free per day)

---

## 📋 Step-by-Step Setup

### **Step 1: Create Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name: `linkedin-finder` (or any name)
4. Click "Create"
5. Wait for project creation (~30 seconds)

---

### **Step 2: Enable Custom Search API**

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for: `Custom Search API`
3. Click on "Custom Search API"
4. Click "Enable"
5. Wait for API to be enabled (~10 seconds)

---

### **Step 3: Create API Key**

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the API key (starts with `AIza...`)
4. Click "Restrict Key" (recommended)
5. Under "API restrictions":
   - Select "Restrict key"
   - Choose "Custom Search API"
6. Click "Save"

**Save this API key - you'll add it to .env file**

---

### **Step 4: Create Custom Search Engine**

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" or "Create a new search engine"
3. Fill in the form:
   - **Search engine name:** `LinkedIn Profile Finder`
   - **What to search:** Select "Search specific sites"
   - **Sites to search:** Enter `linkedin.com/in/*`
4. Click "Create"
5. On the next page, click "Customize"
6. Under "Basic" tab, find "Search engine ID"
7. Copy the Search Engine ID (looks like: `a1b2c3d4e5f6g7h8i`)

**Save this CSE ID - you'll add it to .env file**

---

### **Step 5: Configure Search Engine Settings**

1. In the "Customize" page, go to "Setup" tab
2. Under "Sites to search", verify: `linkedin.com/in/*`
3. Under "Search the entire web", select "OFF" (only search LinkedIn)
4. Click "Update"

---

### **Step 6: Add Credentials to .env File**

1. Open your `.env` file in the project root
2. Add these two lines:

```
GOOGLE_API_KEY=AIza...your_api_key_here
GOOGLE_CSE_ID=a1b2c3d4e5f6g7h8i...your_cse_id_here
```

3. Save the file

---

### **Step 7: Install Required Package**

Run this command in your terminal:

```bash
pip install google-api-python-client
```

---

### **Step 8: Test the Setup**

Run the test script:

```bash
python google_linkedin_finder.py
```

**Expected output:**
```
Testing Google LinkedIn Finder...
================================================================================

API credentials found. Testing search...

Searching for: Michael Merrill, New York
Result: https://www.linkedin.com/in/mmerrill3

Searching for: Satya Nadella, Microsoft
Result: https://www.linkedin.com/in/satyanadella
```

If you see LinkedIn URLs, it's working! ✅

---

## 💰 Pricing & Limits

### **Free Tier:**
- 100 queries per day
- $0 cost

### **Paid Tier:**
- $5 per 1,000 queries
- No daily limit

### **For Your 2,629 Candidates:**
- Cost: ~$13 (2,629 queries)
- Time: ~4-5 minutes (with 0.1s delay between requests)

---

## 🔧 Troubleshooting

### **Error: "API key not valid"**
- Make sure you copied the full API key (starts with `AIza`)
- Check that Custom Search API is enabled
- Verify API key restrictions allow Custom Search API

### **Error: "Invalid CSE ID"**
- Make sure you copied the full Search Engine ID
- Verify the search engine is created and active
- Check that it's searching `linkedin.com/in/*`

### **Error: "Rate limit exceeded"**
- You've hit the 100 queries/day free limit
- Wait 24 hours or enable billing
- Script will automatically retry after 60 seconds

### **No results found**
- Check that the search engine is searching LinkedIn only
- Verify "Search the entire web" is OFF
- Try searching manually at programmablesearchengine.google.com

---

## 🎯 Next Steps

Once setup is complete:

1. ✅ Test with sample candidates
2. ✅ Integrate with deep_scorer_v3.py
3. ✅ Re-score all 2,629 candidates with LinkedIn discovery
4. ✅ Review results and LinkedIn URL coverage

---

## 📞 Need Help?

If you encounter issues:
1. Check the error message carefully
2. Verify all credentials are correct in .env
3. Test with the standalone script first
4. Check Google Cloud Console for API usage/errors

**The setup should take 10-15 minutes total.**
