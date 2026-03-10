# Feedback Collection System (T080)

## Purpose

Collect user feedback on memory system effectiveness to continuously improve:
- Entry quality and relevance
- Threshold tuning
- Search accuracy
- Overall usefulness

## Feedback Channels

### 1. Implicit Feedback (Automatic)

#### Positive Signals
- User searches for and reads an entry
- Entry is referenced in multiple projects
- Similar patterns emerge across projects

#### Negative Signals
- Entry is never accessed
- Entry is deleted/edited shortly after creation
- User creates similar entry (original was unclear)

### 2. Explicit Feedback (Optional)

#### After Deep Read
```
Was this memory entry helpful?
[1] Very helpful - saved me time
[2] Somewhat helpful - had useful info
[3] Not helpful - wrong or outdated
[4] Skip - don't ask again
```

#### Weekly Summary
```
Memory System Weekly Report:
- 5 new entries added
- 12 entries accessed
- Top entry: "JWT token expiration fix"

Rate this week's memory value: [1-5]
What would make it more useful? [optional text]
```

### 3. Feedback Commands

```bash
# Mark entry as helpful
spec-kit memory helpful --entry "JWT token expiration"

# Mark entry as not helpful
spec-kit memory unhelpful --entry "JWT token expiration"

# Suggest improvement
spec-kit memory improve --entry "JWT token expiration" \
  --note "Add code example"

# Request threshold review
spec-kit memory review-thresholds
```

## Feedback Storage

### File Structure
```
~/.claude/memory/
├── feedback/
│   ├── entry_feedback.json    # Per-entry ratings
│   ├── weekly_reports.json     # Weekly summaries
│   └── threshold_suggestions.md # Suggested changes
```

### Feedback Entry Format
```json
{
  "entry_id": "jwt-token-expiration-2024-03-10",
  "project_id": "spec-kit",
  "timestamp": "2024-03-10T12:00:00Z",
  "rating": 5,
  "helpful": true,
  "access_count": 15,
  "last_accessed": "2024-03-15T10:30:00Z",
  "notes": ["Saved 2 hours of debugging", "Needs code example"]
}
```

## Using Feedback for Improvements

### 1. Quality Scoring
```python
def calculate_entry_score(entry_feedback):
    """Calculate composite quality score."""
    return (
        entry_feedback.rating * 0.4 +           # User rating
        min(entry_feedback.access_count, 10) * 0.05 +  # Access frequency
        (1 if entry_feedback.helpful else 0) * 0.3 +   # Helpful flag
        days_since_creation * -0.01              # Decay
    )
```

### 2. Threshold Adjustment
```python
def adjust_thresholds(feedback_data):
    """Suggest threshold adjustments based on feedback."""
    architecture_ratings = [f for f in feedback_data
                           if f.destination == 'architecture']
    avg_rating = sum(f.rating for f in architecture_ratings) / len(architecture_ratings)

    if avg_rating < 3.5:
        return "Consider raising HIGH_IMPORTANCE threshold"
    elif avg_rating > 4.5:
        return "Consider lowering HIGH_IMPORTANCE threshold"
    return "Thresholds well-calibrated"
```

### 3. Entry Cleanup
```python
def suggest_cleanup(feedback_data):
    """Suggest entries to archive or delete."""
    suggestions = []
    for entry in feedback_data:
        if entry.days_since_access > 90 and entry.score < 2.0:
            suggestions.append({
                "action": "archive",
                "entry": entry.title,
                "reason": "Low score, not accessed in 90 days"
            })
    return suggestions
```

## Implementation Status

- [ ] Create feedback storage structure
- [ ] Implement implicit feedback tracking
- [ ] Add explicit feedback prompts (optional)
- [ ] Build feedback analysis tools
- [ ] Generate weekly reports
- [ ] Implement threshold adjustment suggestions

## Privacy Considerations

1. Feedback is stored locally (no cloud upload)
2. Users can disable feedback collection
3. No code snippets in feedback (only metadata)
4. Anonymous aggregate reporting optional
