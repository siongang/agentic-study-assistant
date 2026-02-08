"""LLM-powered intelligent study planning (Priority analysis)."""
from pathlib import Path
from datetime import date
import json
from typing import Optional

from app.models.enriched_coverage import EnrichedCoverage, EnrichedTopic
from app.models.plan import Priority
from app.tools.llm_utils import call_gemini


def analyze_study_load(
    enriched_coverage_paths: list[Path],
    start_date: date,
    end_date: date,
    minutes_per_day: int = 90
) -> dict:
    """
    Analyze study workload and feasibility (pure calculation, no LLM).
    
    Args:
        enriched_coverage_paths: Paths to enriched coverage JSON files
        start_date: Study start date
        end_date: Study end date (or exam date)
        minutes_per_day: Target study time per day
        
    Returns:
        dict with:
        - total_topics: Number of topics to cover
        - total_time_needed: Estimated hours needed
        - time_available: Hours available
        - feasibility: "comfortable" | "realistic" | "tight" | "impossible"
        - days_available: Study days available
        - coverage_percentage: What % of material fits in time
        - recommendation: Strategy recommendation
    """
    # Load coverages
    coverages = []
    for path in enriched_coverage_paths:
        with open(path) as f:
            data = json.load(f)
        coverages.append(EnrichedCoverage(**data))
    
    # Count topics and estimate time
    total_topics = sum(len(c.topics) for c in coverages)
    
    # Simple time estimate: 30-60 min per topic
    # We'll use 45 min average as baseline before LLM refinement
    avg_minutes_per_topic = 45
    total_minutes_needed = total_topics * avg_minutes_per_topic
    total_hours_needed = total_minutes_needed / 60
    
    # Calculate available time
    days_available = (end_date - start_date).days + 1
    # Skip weekends (rough estimate - 5/7 of days)
    weekdays_available = int(days_available * 5/7)
    total_minutes_available = weekdays_available * minutes_per_day
    total_hours_available = total_minutes_available / 60
    
    # Calculate feasibility
    coverage_percentage = min(100, (total_hours_available / total_hours_needed) * 100) if total_hours_needed > 0 else 100
    ratio = total_hours_available / total_hours_needed if total_hours_needed > 0 else 1.0
    
    if ratio >= 1.5:
        feasibility = "comfortable"
        recommendation = "comprehensive"
    elif ratio >= 0.9:
        feasibility = "realistic"
        recommendation = "balanced"
    elif ratio >= 0.5:
        feasibility = "tight"
        recommendation = "prioritized"
    else:
        feasibility = "impossible"
        recommendation = "cramming"
    
    return {
        "total_topics": total_topics,
        "total_time_needed_hours": round(total_hours_needed, 1),
        "time_available_hours": round(total_hours_available, 1),
        "feasibility": feasibility,
        "days_available": weekdays_available,
        "coverage_percentage": round(coverage_percentage, 1),
        "recommendation": recommendation,
        "exams": [
            {
                "exam_name": c.exam_name,
                "topics": len(c.topics),
                "exam_date": c.exam_date
            }
            for c in coverages
        ]
    }


def prioritize_topics(
    enriched_coverage_paths: list[Path],
    strategy: str = "balanced"
) -> dict:
    """
    Use LLM to analyze and prioritize topics by importance.
    
    Args:
        enriched_coverage_paths: Paths to enriched coverage JSON files
        strategy: "comprehensive", "balanced", "prioritized", or "cramming"
        
    Returns:
        dict with:
        - topics: List of {topic_data, priority, reason, time_estimate}
        - time_breakdown: Minutes per priority level
        - strategy_used: Strategy applied
    """
    # Load coverages
    coverages = []
    for path in enriched_coverage_paths:
        with open(path) as f:
            data = json.load(f)
        coverages.append(EnrichedCoverage(**data))
    
    # Prepare topic summaries for LLM
    topic_summaries = []
    for coverage in coverages:
        for topic in coverage.topics:
            # Create concise summary
            summary = {
                "exam": coverage.exam_name,
                "chapter": topic.chapter,
                "chapter_title": topic.chapter_title,
                "objective": topic.bullet,
                "has_practice_problems": len(topic.practice_problems) > 0,
                "evidence_quality": topic.confidence_score,
                "key_terms_count": len(topic.key_terms)
            }
            topic_summaries.append(summary)
    
    # Build LLM prompt
    prompt = f"""You are an expert study planner analyzing exam coverage. 

Strategy: {strategy}
- "comprehensive": Study everything thoroughly
- "balanced": Mix of depth and breadth  
- "prioritized": Focus on high-value topics
- "cramming": Only critical must-know topics

Exam Coverage:
{json.dumps(topic_summaries, indent=2)}

Task: Analyze each topic and assign a priority level based on:
1. **Foundational importance**: Is this a prerequisite for other topics?
2. **Exam emphasis**: Early chapters and topics with practice problems are usually more important
3. **Complexity**: Adjust time estimates based on topic depth
4. **Strategy fit**: Align with the user's time constraints

Priority Levels:
- "critical": Foundational concepts, definitely on exam, must study
- "high": Very important, likely to be tested
- "medium": Should know, might be tested
- "low": Good to know, less likely to be tested heavily
- "optional": Extra depth, review if time permits

Time Estimates:
- Simple concepts: 20-30 min
- Standard topics: 30-45 min  
- Complex topics with problems: 45-75 min
- Deep/advanced topics: 60-90 min

Return JSON array (one object per topic):
[
  {{
    "chapter": <int>,
    "objective": "<string>",
    "priority": "critical|high|medium|low|optional",
    "reason": "<brief explanation>",
    "time_estimate_minutes": <int>
  }},
  ...
]

Be concise but clear in reasons. Focus on why the priority matters."""

    # Call LLM
    try:
        response = call_gemini(
            prompt=prompt,
            model="gemini-2.0-flash-exp",
            temperature=0.3  # Low temperature for consistent analysis
        )
        
        # Parse response
        # Clean markdown code blocks if present
        content = response.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        priorities = json.loads(content)
        
        # Match priorities back to topics
        result_topics = []
        for coverage in coverages:
            for topic in coverage.topics:
                # Find matching priority assignment
                priority_data = next(
                    (p for p in priorities 
                     if p["chapter"] == topic.chapter and p["objective"] == topic.bullet),
                    None
                )
                
                if priority_data:
                    result_topics.append({
                        "coverage": coverage,
                        "topic": topic,
                        "priority": priority_data["priority"],
                        "reason": priority_data["reason"],
                        "time_estimate": priority_data["time_estimate_minutes"]
                    })
                else:
                    # Fallback if LLM didn't return this topic
                    result_topics.append({
                        "coverage": coverage,
                        "topic": topic,
                        "priority": "medium",
                        "reason": "Default priority",
                        "time_estimate": 45
                    })
        
        # Calculate time breakdown
        time_breakdown = {
            "critical": sum(t["time_estimate"] for t in result_topics if t["priority"] == "critical"),
            "high": sum(t["time_estimate"] for t in result_topics if t["priority"] == "high"),
            "medium": sum(t["time_estimate"] for t in result_topics if t["priority"] == "medium"),
            "low": sum(t["time_estimate"] for t in result_topics if t["priority"] == "low"),
            "optional": sum(t["time_estimate"] for t in result_topics if t["priority"] == "optional")
        }
        
        return {
            "topics": result_topics,
            "time_breakdown": time_breakdown,
            "strategy_used": strategy,
            "total_topics": len(result_topics)
        }
        
    except Exception as e:
        print(f"Error in LLM prioritization: {e}")
        print("Falling back to default priorities...")
        
        # Fallback: Use simple heuristics
        result_topics = []
        for coverage in coverages:
            for topic in coverage.topics:
                # Simple heuristic: early chapters = higher priority
                if topic.chapter <= 2:
                    priority = "critical"
                    time_est = 50
                elif topic.chapter <= 5:
                    priority = "high"
                    time_est = 45
                else:
                    priority = "medium"
                    time_est = 40
                
                result_topics.append({
                    "coverage": coverage,
                    "topic": topic,
                    "priority": priority,
                    "reason": "Heuristic-based (LLM unavailable)",
                    "time_estimate": time_est
                })
        
        time_breakdown = {
            "critical": sum(t["time_estimate"] for t in result_topics if t["priority"] == "critical"),
            "high": sum(t["time_estimate"] for t in result_topics if t["priority"] == "high"),
            "medium": sum(t["time_estimate"] for t in result_topics if t["priority"] == "medium"),
            "low": 0,
            "optional": 0
        }
        
        return {
            "topics": result_topics,
            "time_breakdown": time_breakdown,
            "strategy_used": strategy,
            "total_topics": len(result_topics)
        }
