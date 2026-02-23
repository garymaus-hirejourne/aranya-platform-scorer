# Self-Learning Multi-LLM Recruiting System
## Design Document

---

## Vision

A recruiting AI that **automatically improves** by:
1. **Learning from every hire** (success/failure patterns)
2. **Using multiple AI models** (OpenAI + Gemini) for better decisions
3. **Self-correcting** when performance drops
4. **Getting smarter over time** without manual intervention

---

## Architecture

### **1. Multi-LLM Ensemble**

```
┌─────────────────────────────────────────────────────────┐
│                  DECISION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   OpenAI     │  │   Gemini     │  │   Ensemble   │  │
│  │   GPT-4      │  │   Pro        │  │   Voting     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│              LEARNING FEEDBACK LOOP                     │
│  • Track hiring outcomes                               │
│  • Measure model accuracy                              │
│  • Auto-adjust weights                                 │
└─────────────────────────────────────────────────────────┘
```

### **Why Multiple LLMs?**

**OpenAI GPT-4:**
- Excellent at pattern recognition
- Strong reasoning capabilities
- Good for rubric generation

**Gemini Pro:**
- Different training data = different perspectives
- Strong at technical analysis
- Good for code evaluation

**Ensemble Voting:**
- Combine both models' insights
- Reduce individual model bias
- Higher accuracy through consensus

---

## Components

### **1. Multi-LLM Learning Engine** (`multi_llm_engine.py`)

```python
class MultiLLMEngine:
    """
    Uses OpenAI + Gemini to analyze candidates and learn from outcomes.
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.gemini_client = genai.GenerativeModel('gemini-pro')
        self.tracker = FeedbackTracker()
        self.performance_metrics = PerformanceTracker()
    
    def analyze_candidate(self, username, profile_data):
        """
        Get insights from both LLMs and combine them.
        """
        # OpenAI analysis
        openai_score = self._openai_analyze(username, profile_data)
        
        # Gemini analysis
        gemini_score = self._gemini_analyze(username, profile_data)
        
        # Ensemble decision
        final_score = self._ensemble_vote(openai_score, gemini_score)
        
        return {
            'final_score': final_score,
            'openai_score': openai_score,
            'gemini_score': gemini_score,
            'confidence': self._calculate_confidence(openai_score, gemini_score)
        }
    
    def learn_from_outcomes(self):
        """
        Analyze which model was more accurate and adjust weights.
        """
        outcomes = self.tracker.get_all_feedback()
        
        openai_accuracy = self._measure_accuracy('openai', outcomes)
        gemini_accuracy = self._measure_accuracy('gemini', outcomes)
        
        # Auto-adjust ensemble weights
        self._update_ensemble_weights(openai_accuracy, gemini_accuracy)
        
        # Generate improvement insights
        improvements = self._generate_improvements(outcomes)
        
        return improvements
```

### **2. Automated Feedback Collector** (`auto_feedback.py`)

```python
class AutoFeedbackCollector:
    """
    Automatically tracks candidate outcomes from various sources.
    """
    
    def __init__(self):
        self.tracker = FeedbackTracker()
        self.sources = {
            'email': EmailMonitor(),      # Parse hiring emails
            'calendar': CalendarMonitor(), # Track interview schedules
            'ats': ATSIntegration(),       # Connect to ATS system
            'manual': ManualEntry()        # Fallback to manual
        }
    
    def collect_feedback(self):
        """
        Automatically collect feedback from all sources.
        """
        for source_name, source in self.sources.items():
            try:
                new_feedback = source.get_recent_outcomes()
                for feedback in new_feedback:
                    self.tracker.add_feedback(
                        username=feedback['username'],
                        outcome=feedback['outcome'],
                        source=source_name,
                        timestamp=feedback['timestamp']
                    )
            except Exception as e:
                print(f"Error collecting from {source_name}: {e}")
```

### **3. Continuous Learning Loop** (`continuous_learner.py`)

```python
class ContinuousLearner:
    """
    Runs periodic learning cycles to improve the system.
    """
    
    def __init__(self):
        self.engine = MultiLLMEngine()
        self.schedule = {
            'daily': self.daily_learning,
            'weekly': self.weekly_deep_learning,
            'monthly': self.monthly_strategy_review
        }
    
    def daily_learning(self):
        """
        Quick daily adjustments based on recent feedback.
        """
        # Collect yesterday's feedback
        feedback = self.engine.tracker.get_recent_feedback(days=1)
        
        if len(feedback) > 0:
            # Quick pattern check
            insights = self.engine.learn_from_outcomes()
            
            # Minor rubric adjustments
            if insights['needs_adjustment']:
                self._apply_minor_adjustments(insights)
    
    def weekly_deep_learning(self):
        """
        Deep analysis of patterns and major improvements.
        """
        # Analyze last week's data
        feedback = self.engine.tracker.get_recent_feedback(days=7)
        
        # Run both LLMs for deep analysis
        openai_insights = self.engine._openai_deep_analysis(feedback)
        gemini_insights = self.engine._gemini_deep_analysis(feedback)
        
        # Combine insights
        combined = self.engine._merge_insights(openai_insights, gemini_insights)
        
        # Apply improvements
        self._apply_improvements(combined)
        
        # A/B test new rubric
        self._setup_ab_test(combined['suggested_rubric'])
    
    def monthly_strategy_review(self):
        """
        High-level strategy review and major pivots.
        """
        # Performance metrics
        metrics = self.engine.performance_metrics.get_monthly_stats()
        
        # Are we improving?
        if metrics['trend'] == 'declining':
            # Major strategy shift needed
            self._trigger_strategy_review()
```

### **4. Performance Tracker** (`performance_tracker.py`)

```python
class PerformanceTracker:
    """
    Tracks system effectiveness over time.
    """
    
    def __init__(self):
        self.metrics_file = "data/performance_metrics.jsonl"
    
    def track_prediction(self, username, predicted_score, actual_outcome):
        """
        Track how accurate our predictions are.
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'predicted_score': predicted_score,
            'actual_outcome': actual_outcome,
            'error': self._calculate_error(predicted_score, actual_outcome)
        }
        
        self._append_metric(metric)
    
    def get_accuracy_trend(self, days=30):
        """
        Calculate accuracy trend over time.
        """
        metrics = self._load_recent_metrics(days)
        
        # Calculate precision, recall, F1
        precision = self._calculate_precision(metrics)
        recall = self._calculate_recall(metrics)
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'trend': self._calculate_trend(metrics)
        }
```

### **5. Self-Correction System** (`self_corrector.py`)

```python
class SelfCorrector:
    """
    Automatically detects and fixes performance issues.
    """
    
    def __init__(self):
        self.performance = PerformanceTracker()
        self.engine = MultiLLMEngine()
        self.thresholds = {
            'precision_min': 0.7,
            'recall_min': 0.6,
            'f1_min': 0.65
        }
    
    def check_and_correct(self):
        """
        Check performance and auto-correct if needed.
        """
        metrics = self.performance.get_accuracy_trend(days=7)
        
        issues = []
        
        # Check precision (too many false positives?)
        if metrics['precision'] < self.thresholds['precision_min']:
            issues.append('low_precision')
            self._tighten_criteria()
        
        # Check recall (missing good candidates?)
        if metrics['recall'] < self.thresholds['recall_min']:
            issues.append('low_recall')
            self._broaden_search()
        
        # Check overall performance
        if metrics['f1_score'] < self.thresholds['f1_min']:
            issues.append('overall_poor')
            self._trigger_deep_review()
        
        return {
            'issues_found': issues,
            'corrections_applied': len(issues) > 0,
            'new_metrics': self.performance.get_accuracy_trend(days=1)
        }
    
    def _tighten_criteria(self):
        """
        Increase score thresholds to reduce false positives.
        """
        # Increase minimum score threshold
        # Increase weight on proven success factors
        pass
    
    def _broaden_search(self):
        """
        Expand search criteria to catch more candidates.
        """
        # Add more search queries
        # Reduce minimum score threshold
        # Explore adjacent skill sets
        pass
```

---

## Implementation Phases

### **Phase 1: Multi-LLM Foundation** (Week 1)
- [ ] Add Gemini API integration
- [ ] Create `multi_llm_engine.py`
- [ ] Implement ensemble voting
- [ ] Test both models on sample candidates

### **Phase 2: Automated Feedback** (Week 2)
- [ ] Build `auto_feedback.py`
- [ ] Integrate with email/calendar (if available)
- [ ] Create manual feedback UI
- [ ] Start collecting outcome data

### **Phase 3: Continuous Learning** (Week 3)
- [ ] Create `continuous_learner.py`
- [ ] Set up daily/weekly/monthly schedules
- [ ] Implement A/B testing framework
- [ ] Build performance dashboard

### **Phase 4: Self-Correction** (Week 4)
- [ ] Build `performance_tracker.py`
- [ ] Create `self_corrector.py`
- [ ] Set up automated alerts
- [ ] Implement auto-adjustment logic

---

## Key Metrics to Track

### **Model Performance**
- **Precision**: % of high-scored candidates who succeed
- **Recall**: % of successful candidates we identified
- **F1 Score**: Harmonic mean of precision and recall
- **Model Agreement**: How often OpenAI and Gemini agree

### **Business Impact**
- **Time-to-Hire**: Days from search to hire
- **Cost-per-Hire**: Total cost / successful hires
- **Quality-of-Hire**: Performance ratings after 90 days
- **Retention Rate**: % still employed after 1 year

### **Learning Effectiveness**
- **Accuracy Trend**: Is the system improving over time?
- **Feedback Volume**: How much data are we collecting?
- **Adjustment Frequency**: How often do we need corrections?
- **ROI**: Value gained vs. cost of running the system

---

## Example Learning Cycle

```
Week 1:
  - Score 50 candidates
  - 10 get interviewed
  - 2 get hired

Week 2:
  - Collect feedback on Week 1 candidates
  - OpenAI: "Hired candidates had strong K8s operator experience"
  - Gemini: "Hired candidates contributed to CNCF projects"
  - System: Increase weight on K8s operators + CNCF contributions

Week 3:
  - Apply new rubric
  - Score 50 new candidates
  - 15 get interviewed (↑ from 10)
  - 4 get hired (↑ from 2)

Week 4:
  - Measure improvement
  - Precision: 26% → 27% (slight improvement)
  - Recall: Unknown → tracking now
  - Continue learning...

Month 2:
  - System has learned from 200+ candidates
  - Precision: 35%
  - Recall: 80%
  - Time-to-hire: 45 days → 30 days
  - Cost-per-hire: $5000 → $3000
```

---

## Benefits of Multi-LLM Approach

### **1. Reduced Bias**
- Different models = different perspectives
- Ensemble voting reduces individual model weaknesses

### **2. Higher Accuracy**
- Two models catch more patterns than one
- Disagreement signals uncertainty (investigate further)

### **3. Continuous Improvement**
- Track which model is more accurate
- Auto-adjust weights based on performance
- Learn from both models' strengths

### **4. Robustness**
- If one API is down, use the other
- If one model fails, fallback available
- Reduced single-point-of-failure risk

---

## Next Steps

1. **Add Gemini API** to `.env`
2. **Build `multi_llm_engine.py`** with ensemble voting
3. **Test both models** on existing candidates
4. **Compare results** to see which is more accurate
5. **Implement automated feedback** collection
6. **Set up continuous learning** loop
7. **Deploy and monitor** performance

---

## Questions to Answer

1. **Which model is better at what?**
   - Technical skills: OpenAI vs Gemini?
   - Pattern recognition: Which is more accurate?
   - Cost efficiency: Which gives better ROI?

2. **How should we weight the ensemble?**
   - 50/50 split?
   - Weight by historical accuracy?
   - Dynamic weighting based on candidate type?

3. **What triggers a learning cycle?**
   - Every N candidates?
   - Every N days?
   - When performance drops?

4. **How do we measure success?**
   - Hiring manager satisfaction?
   - Time-to-hire reduction?
   - Quality-of-hire scores?

---

**This system will truly learn and improve over time, using the best of both OpenAI and Gemini to make smarter hiring decisions.**
