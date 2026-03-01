# Clay.com API Research for LinkedIn Enrichment Automation

**Date:** February 23, 2026

**Objective:** Automate LinkedIn profile discovery using Clay.com API to replace manual verification

---

## 🔍 Research Findings

### **Clay.com API Capabilities**

Based on web research, Clay.com offers several API/automation options:

**1. Webhook-Based API (Table as API)**
- Create a Clay table with enrichment columns
- Send data via webhook (HTTP POST)
- Clay processes enrichment in background
- Returns results via webhook callback
- **Use case:** Send name + location → Get LinkedIn URL

**2. Enterprise API (Limited Access)**
- Direct REST API for lookups
- Requires Enterprise plan
- Fast responses for basic enrichment
- Contact Clay GTM engineers for access

**3. HTTP API Integration**
- Clay can call external APIs
- Can be used to trigger Clay tables
- Supports pagination and complex workflows

---

## 🎯 Recommended Approach: Webhook-Based Enrichment

### **How It Works:**

**Step 1: Create Clay Table**
1. Create table with columns:
   - Input: Name, Location, GitHub Username
   - Enrichment: LinkedIn URL (using Clay's LinkedIn enrichment)
   - Output: Enriched LinkedIn URL

**Step 2: Set Up Webhook**
1. Clay generates webhook URL for the table
2. Configure webhook to accept JSON data
3. Set up callback webhook for results

**Step 3: Python Integration**
```python
import requests

def enrich_linkedin_via_clay(name, location, github_username):
    # Send to Clay webhook
    webhook_url = "https://clay.com/webhook/your-table-id"
    
    payload = {
        "name": name,
        "location": location,
        "github_username": github_username
    }
    
    response = requests.post(webhook_url, json=payload)
    
    # Clay processes in background
    # Results returned via callback webhook
    return response.json()
```

**Step 4: Receive Results**
- Clay calls your callback webhook with enriched data
- Extract LinkedIn URL from response
- Update candidate record

---

## 📊 Expected Performance

**Success Rate:**
- Clay uses multiple data sources (Apollo, Clearbit, PDL, etc.)
- Expected: 40-60% LinkedIn URL discovery
- Better than Google API (deprecated)
- Similar to what you're getting manually

**Speed:**
- Webhook response: Immediate acknowledgment
- Enrichment time: 30 seconds - 2 minutes per record
- Batch processing: Can send all 2,629 candidates at once
- Total time: 1-2 hours for full batch

**Cost:**
- Uses your existing Clay.com credits
- No additional API fees
- Cost depends on your Clay plan and credit usage

---

## 🔧 Implementation Plan

### **Phase 1: Clay Table Setup (30 minutes)**

1. **Create Clay Table:**
   - Log into Clay.com
   - Create new table: "GitHub Candidate LinkedIn Enrichment"
   - Add columns:
     - Name (text input)
     - Location (text input)
     - GitHub Username (text input)
     - LinkedIn URL (enrichment - use "Find LinkedIn URL" integration)

2. **Configure Webhook:**
   - Go to table settings
   - Enable "Webhook" or "API Access"
   - Copy webhook URL
   - Set up callback webhook URL (we'll create endpoint)

3. **Test Enrichment:**
   - Manually add 1-2 test rows
   - Verify LinkedIn enrichment works
   - Check success rate and data quality

---

### **Phase 2: Python Integration (2 hours)**

**Create Clay API Client:**

```python
# clay_enrichment.py

import requests
import time
from typing import Optional, List, Dict

class ClayEnrichmentClient:
    def __init__(self, webhook_url: str, api_key: Optional[str] = None):
        self.webhook_url = webhook_url
        self.api_key = api_key
        
    def enrich_candidate(self, name: str, location: str, github_username: str) -> Dict:
        """
        Send candidate to Clay for LinkedIn enrichment.
        """
        payload = {
            "name": name,
            "location": location,
            "github_username": github_username
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers=headers
        )
        
        return response.json()
    
    def batch_enrich(self, candidates: List[Dict], delay: float = 0.5) -> List[Dict]:
        """
        Batch enrich multiple candidates.
        """
        results = []
        
        for i, candidate in enumerate(candidates):
            result = self.enrich_candidate(
                name=candidate.get('name'),
                location=candidate.get('location'),
                github_username=candidate.get('github_username')
            )
            results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"Sent {i + 1}/{len(candidates)} to Clay for enrichment")
            
            time.sleep(delay)
        
        return results
```

**Integrate with Scorer:**

```python
# In deep_scorer_v3.py

from clay_enrichment import ClayEnrichmentClient

# After scoring, send to Clay for LinkedIn enrichment
clay_client = ClayEnrichmentClient(
    webhook_url=os.getenv("CLAY_WEBHOOK_URL"),
    api_key=os.getenv("CLAY_API_KEY")
)

# Batch send all candidates
candidates_for_enrichment = [
    {
        "name": result["name"],
        "location": result["location"],
        "github_username": result["username"]
    }
    for result in scored_candidates
]

clay_client.batch_enrich(candidates_for_enrichment)
```

---

### **Phase 3: Callback Handler (1 hour)**

**Create Flask endpoint to receive Clay results:**

```python
# clay_callback_handler.py

from flask import Flask, request, jsonify
import csv

app = Flask(__name__)

@app.route('/clay-callback', methods=['POST'])
def handle_clay_callback():
    """
    Receive enriched data from Clay webhook.
    """
    data = request.json
    
    # Extract LinkedIn URL
    github_username = data.get('github_username')
    linkedin_url = data.get('linkedin_url')
    
    # Update CSV with LinkedIn URL
    update_candidate_linkedin(github_username, linkedin_url)
    
    return jsonify({"status": "success"}), 200

def update_candidate_linkedin(github_username: str, linkedin_url: str):
    """
    Update candidate CSV with LinkedIn URL from Clay.
    """
    # Read CSV
    # Find candidate by github_username
    # Update linkedin_url field
    # Write back to CSV
    pass

if __name__ == '__main__':
    app.run(port=5001)
```

---

## 🚀 End-to-End Automated Workflow

**Step 1: Run Scorer (25-30 minutes)**
```bash
python deep_scorer_v3.py "path/to/sharded_users.csv"
```
- Scores all candidates
- Extracts LinkedIn from GitHub profiles (20-30%)

**Step 2: Send to Clay for Enrichment (5 minutes)**
```bash
python enrich_with_clay.py
```
- Reads scored candidates
- Sends candidates without LinkedIn to Clay webhook
- Clay enriches in background (1-2 hours)

**Step 3: Receive Results (Automatic)**
- Clay calls callback webhook with enriched data
- LinkedIn URLs automatically added to CSV
- No manual intervention needed

**Step 4: Final Output**
- CSV with all candidates
- LinkedIn URLs from GitHub (20-30%)
- LinkedIn URLs from Clay (40-60% of remaining)
- Total coverage: 55-75%

---

## 💰 Cost Analysis

**Clay.com Credits:**
- Depends on your plan
- Typical: 1-5 credits per enrichment
- For 2,000 candidates: 2,000-10,000 credits
- Check your Clay plan for credit costs

**Comparison:**
- Manual work: Free but time-consuming (40+ hours)
- Clay API: Uses existing credits, fully automated
- Proxycurl: $26-79 for 2,629 candidates
- Apollo.io: $49-99/month

---

## ✅ Next Steps

**Immediate:**
1. Check if you have webhook/API access in your Clay plan
2. Create test Clay table with LinkedIn enrichment
3. Get webhook URL from Clay
4. Test with 5-10 candidates manually

**If Webhook Access Available:**
1. I'll build the Clay API integration (2-3 hours)
2. Create callback handler
3. Integrate with scorer
4. Test end-to-end automation

**If No Webhook Access:**
- Check if you can upgrade Clay plan
- Or consider Proxycurl/Apollo.io as alternatives
- Or use CSV upload to Clay (semi-automated)

---

## 🎯 Questions for You

1. **What Clay.com plan do you have?** (Starter, Explorer, Pro, Enterprise?)
2. **Do you have API/webhook access in Clay?** (Check table settings)
3. **How many Clay credits do you have available?**
4. **Can you create a test table and share the webhook URL?**

**Once I know your Clay plan capabilities, I can build the automated integration.**
