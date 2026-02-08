"""Multi-exam study plan generator (Phase 8)."""
from pathlib import Path
from datetime import date, datetime, timedelta
import re
import json
from typing import Literal

from app.models.enriched_coverage import EnrichedCoverage, EnrichedTopic
from app.models.plan import StudyPlan, StudyDay, StudyBlock, ExamInfo
from app.tools.question_generator import generate_study_question


def estimate_time_minutes(
    topic: EnrichedTopic,
    chapter: int
) -> int:
    """
    Estimate time needed for a topic.
    
    Rules:
    - Base: 30 minutes
    - +20 if practice problems exist (>2)
    - +15 if foundational chapters (1-3)
    - +10 if low confidence (<0.7)
    
    Args:
        topic: Enriched topic with metadata
        chapter: Chapter number
        
    Returns:
        Estimated minutes
    """
    minutes = 30  # Base
    
    # Practice problems add time
    if len(topic.practice_problems) > 2:
        minutes += 20
    elif len(topic.practice_problems) > 0:
        minutes += 10
    
    # Foundational chapters need more time
    if chapter <= 3:
        minutes += 15
    
    # Low confidence needs more exploration time
    if topic.confidence_score < 0.7:
        minutes += 10
    
    return minutes


def format_reading_pages(topic: EnrichedTopic) -> str:
    """
    Format reading pages as human-readable string.
    
    Args:
        topic: Enriched topic with reading pages
        
    Returns:
        e.g., "Triola, pp. 21-27, 31-32, p. 38"
    """
    if not topic.reading_pages.page_ranges:
        return ""
    
    # Get filename (short version)
    filename = topic.reading_pages.filename
    # Extract author or first part of filename
    if " - " in filename:
        short_name = filename.split(" - ")[0].strip()
    else:
        short_name = filename.split(".")[0][:20]
    
    # Format ranges
    ranges = []
    for start, end in topic.reading_pages.page_ranges:
        if start == end:
            ranges.append(f"p. {start}")
        else:
            ranges.append(f"pp. {start}-{end}")
    
    return f"{short_name}, {', '.join(ranges)}"


def format_practice_problems(topic: EnrichedTopic) -> list:
    """
    Format practice problems as list of problem references.
    
    Args:
        topic: Enriched topic with practice problems
        
    Returns:
        List of {text, page} dicts
    """
    from app.models.plan import PracticeProblemRef
    
    if not topic.practice_problems:
        return []
    
    formatted = []
    for prob in topic.practice_problems[:5]:  # Max 5 problems
        # Use full snippet, just clean it up
        text = prob.snippet.strip()
        formatted.append(PracticeProblemRef(text=text, page=prob.page))
    
    return formatted


def create_study_block(
    topic: EnrichedTopic,
    exam_info: ExamInfo,
    generate_questions: bool = True
) -> StudyBlock:
    """
    Create a study block from an enriched topic.
    
    Args:
        topic: Enriched topic
        exam_info: Exam information
        generate_questions: Whether to generate Socratic questions
        
    Returns:
        StudyBlock with all fields populated
    """
    # Estimate time
    time_minutes = estimate_time_minutes(topic, topic.chapter)
    
    # Format resources
    reading = format_reading_pages(topic)
    problems = format_practice_problems(topic)
    
    # Generate study question from RAG chunks
    study_question = ""
    if generate_questions and topic.top_chunks:
        study_question = generate_study_question(
            objective=topic.bullet,
            chunk_excerpts=topic.top_chunks,
            chapter_title=topic.chapter_title
        )
    
    # Add warning if low confidence
    notes = topic.notes
    if topic.confidence_score < 0.6 and not notes:
        notes = "⚠️ Low confidence match - verify coverage in textbook"
    
    return StudyBlock(
        exam_id=exam_info.exam_id,
        exam_name=exam_info.exam_name,
        course=exam_info.course,
        chapter=topic.chapter,
        chapter_title=topic.chapter_title,
        topic=f"Ch {topic.chapter}: {topic.chapter_title}",
        objective=topic.bullet,
        reading_pages=reading,
        practice_problems=problems,
        key_terms=topic.key_terms,
        study_question=study_question,
        time_estimate_minutes=time_minutes,
        confidence_score=topic.confidence_score,
        notes=notes
    )


def generate_multi_exam_plan(
    enriched_coverage_paths: list[Path],
    start_date: date,
    end_date: date,
    minutes_per_day: int = 90,
    strategy: Literal["round_robin", "priority_first", "balanced"] = "balanced",
    generate_questions: bool = True
) -> StudyPlan:
    """
    Generate a multi-exam interleaved study plan.
    
    Args:
        enriched_coverage_paths: Paths to enriched coverage JSON files
        start_date: Start date for studying
        end_date: End date (or earliest exam date - buffer)
        minutes_per_day: Target study minutes per day
        strategy: Scheduling strategy
        generate_questions: Whether to generate Socratic questions (slower)
        
    Returns:
        Complete StudyPlan
    """
    print(f"\n📅 Generating Multi-Exam Study Plan")
    print(f"   Strategy: {strategy}")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Minutes/day: {minutes_per_day}")
    print()
    
    # Load enriched coverages
    print("[1/5] Loading enriched coverages...", flush=True)
    coverages = []
    for path in enriched_coverage_paths:
        with open(path) as f:
            data = json.load(f)
        coverage = EnrichedCoverage(**data)
        coverages.append(coverage)
        print(f"  ✓ {coverage.exam_name}: {len(coverage.topics)} topics")
    
    # Create exam info
    exams = []
    
    for coverage in coverages:
        # Extract course code from exam_name (e.g., "HLTH 204 - Midterm Examination 1")
        course_pattern = r'([A-Z]{3,5}\s+\d{3})'
        exam_name = coverage.exam_name
        
        # Try to extract course code from exam_name
        match = re.search(course_pattern, exam_name)
        if match:
            course = match.group(1)
        else:
            # Fallback: use the first part before " - " or the full name
            course = exam_name.split(" - ")[0].strip() if " - " in exam_name else exam_name
        
        exam_info = ExamInfo(
            exam_id=coverage.exam_id,
            exam_name=exam_name,
            exam_date=coverage.exam_date,
            course=course,
            source_file_id=coverage.source_file_id
        )
        exams.append(exam_info)
    
    # Create work queue with all topics
    print(f"\n[2/5] Building work queue...", flush=True)
    work_items = []
    for i, (coverage, exam_info) in enumerate(zip(coverages, exams)):
        for topic in coverage.topics:
            work_items.append({
                "topic": topic,
                "exam_info": exam_info,
                "exam_index": i,  # Used for round-robin
                "minutes": estimate_time_minutes(topic, topic.chapter)
            })
    
    total_topics = len(work_items)
    total_minutes = sum(item["minutes"] for item in work_items)
    print(f"  ✓ Total topics: {total_topics}")
    print(f"  ✓ Total estimated time: {total_minutes // 60}h {total_minutes % 60}m")
    
    # Apply scheduling strategy
    print(f"\n[3/5] Scheduling with '{strategy}' strategy...", flush=True)
    
    if strategy == "round_robin":
        # Cycle through exams evenly
        work_items.sort(key=lambda x: (x["exam_index"], x["topic"].chapter))
        scheduled_items = []
        exam_queues = {exam.exam_id: [] for exam in exams}
        
        for item in work_items:
            exam_queues[item["exam_info"].exam_id].append(item)
        
        # Round-robin scheduling
        while any(exam_queues.values()):
            for exam_id in exam_queues:
                if exam_queues[exam_id]:
                    scheduled_items.append(exam_queues[exam_id].pop(0))
    
    elif strategy == "priority_first":
        # Process exams in order (first exam first, then second exam)
        work_items.sort(key=lambda x: (x["exam_index"], x["topic"].chapter))
        scheduled_items = work_items
    
    else:  # balanced
        # Aim for equal total minutes per exam
        exam_minutes = {exam.exam_id: 0 for exam in exams}
        scheduled_items = []
        
        while work_items:
            # Find exam with least total minutes
            min_exam = min(exam_minutes.items(), key=lambda x: x[1])[0]
            
            # Find next item for that exam
            for item in work_items:
                if item["exam_info"].exam_id == min_exam:
                    scheduled_items.append(item)
                    exam_minutes[min_exam] += item["minutes"]
                    work_items.remove(item)
                    break
    
    print(f"  ✓ Scheduled {len(scheduled_items)} topics")
    
    # Allocate to days
    print(f"\n[4/5] Allocating topics to days...", flush=True)
    days = []
    current_date = start_date
    current_day = None
    
    for item in scheduled_items:
        # Check if we need a new day
        if current_day is None or current_day.total_minutes + item["minutes"] > minutes_per_day:
            if current_day is not None:
                days.append(current_day)
                current_date += timedelta(days=1)
            
            # Skip weekends (optional - remove if you want 7-day weeks)
            while current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
            
            if current_date > end_date:
                print(f"  ⚠️ Warning: Ran past end date, added extra days")
            
            current_day = StudyDay(
                date=current_date.isoformat(),
                day_name=current_date.strftime("%A")
            )
        
        # Create block (without questions for now - we'll batch generate)
        block = create_study_block(
            topic=item["topic"],
            exam_info=item["exam_info"],
            generate_questions=False  # Batch later
        )
        current_day.add_block(block)
    
    # Add final day
    if current_day:
        days.append(current_day)
    
    print(f"  ✓ Created {len(days)} study days")
    
    # Generate study questions in batch
    if generate_questions:
        print(f"\n[5/5] Generating study questions from textbook...", flush=True)
        all_blocks = [block for day in days for block in day.blocks]
        
        # Need to map blocks back to their enriched topics to get chunk excerpts
        topic_map = {}
        for coverage in coverages:
            for topic in coverage.topics:
                # Create a key from chapter + bullet (should be unique)
                key = f"{topic.chapter}|{topic.bullet}"
                topic_map[key] = topic
        
        total_blocks = len(all_blocks)
        questions_generated = 0
        
        for i, block in enumerate(all_blocks, 1):
            if i % 10 == 0 or i == total_blocks:
                print(f"  Progress: {i}/{total_blocks}", flush=True)
            
            # Find corresponding enriched topic to get chunks
            key = f"{block.chapter}|{block.objective}"
            enriched_topic = topic_map.get(key)
            
            if enriched_topic and enriched_topic.top_chunks:
                block.study_question = generate_study_question(
                    objective=block.objective,
                    chunk_excerpts=enriched_topic.top_chunks,
                    chapter_title=block.chapter_title
                )
                if block.study_question:
                    questions_generated += 1
        
        print(f"  ✓ Generated {questions_generated}/{total_blocks} study questions")
    else:
        print(f"\n[5/5] Skipping question generation (can add later)")
    
    # Create plan
    plan = StudyPlan(
        exams=exams,
        days=days,
        strategy=strategy,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        minutes_per_day=minutes_per_day
    )
    
    plan.calculate_totals()
    
    return plan
