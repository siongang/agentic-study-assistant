"""Export study plans to readable formats (Phase 9)."""
from pathlib import Path
import csv
from datetime import datetime
from collections import defaultdict

from app.models.plan import StudyPlan, Priority


def export_to_markdown(plan: StudyPlan, output_path: Path) -> None:
    """
    Export study plan to Markdown format.
    
    Args:
        plan: StudyPlan to export
        output_path: Path to save markdown file
    """
    lines = []
    
    # Title
    exam_names = ", ".join(exam.exam_name for exam in plan.exams)
    lines.append(f"# Study Plan: {exam_names}\n")
    
    # Metadata table
    lines.append("## Plan Overview\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Plan ID | `{plan.plan_id}` |")
    lines.append(f"| Created | {plan.created_at.strftime('%Y-%m-%d %H:%M')} |")
    lines.append(f"| Date Range | {plan.start_date} to {plan.end_date} |")
    lines.append(f"| Total Days | {plan.total_days} |")
    lines.append(f"| Total Hours | {plan.total_study_hours:.1f}h |")
    lines.append(f"| Total Topics | {plan.total_topics} |")
    lines.append(f"| Strategy | {plan.strategy} |")
    lines.append(f"| Minutes/Day | {plan.minutes_per_day} |\n")
    
    # Per-exam breakdown
    lines.append("## Exam Breakdown\n")
    stats = plan.get_exam_stats()
    for exam_id, exam_stats in stats.items():
        hours = exam_stats['total_minutes'] / 60
        lines.append(f"### {exam_stats['exam_name']}")
        lines.append(f"- Topics: {exam_stats['topics']}")
        lines.append(f"- Time: {hours:.1f}h ({exam_stats['total_minutes']} minutes)")
        lines.append(f"- Avg Confidence: {exam_stats['avg_confidence']:.2f}\n")
    
    # Priority breakdown (if priorities are used)
    priority_counts = defaultdict(int)
    has_priorities = False
    for day in plan.days:
        for block in day.blocks:
            if hasattr(block, 'priority') and block.priority != Priority.MEDIUM:
                has_priorities = True
            if hasattr(block, 'priority'):
                priority_counts[block.priority] += 1
    
    if has_priorities:
        lines.append("## Priority Breakdown\n")
        priority_emoji = {
            Priority.CRITICAL: "🔴",
            Priority.HIGH: "🟠",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢",
            Priority.OPTIONAL: "⚪"
        }
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW, Priority.OPTIONAL]:
            if priority in priority_counts:
                emoji = priority_emoji.get(priority, "")
                lines.append(f"- {emoji} **{priority.value.title()}:** {priority_counts[priority]} topics")
        lines.append("")
    
    # Daily schedule
    lines.append("---\n")
    lines.append("## Daily Schedule\n")
    
    for day in plan.days:
        # Day header
        lines.append(f"### {day.day_name}, {day.date}")
        lines.append(f"**Total:** {day.total_minutes} minutes, {len(day.blocks)} topics\n")
        
        # Group blocks by priority for better organization
        priority_groups = defaultdict(list)
        for block in day.blocks:
            priority = getattr(block, 'priority', Priority.MEDIUM)
            priority_groups[priority].append(block)
        
        # Display in priority order
        priority_order = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW, Priority.OPTIONAL]
        priority_emoji = {
            Priority.CRITICAL: "🔴",
            Priority.HIGH: "🟠",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢",
            Priority.OPTIONAL: "⚪"
        }
        priority_labels = {
            Priority.CRITICAL: "CRITICAL - Must Study",
            Priority.HIGH: "HIGH PRIORITY",
            Priority.MEDIUM: "MEDIUM PRIORITY",
            Priority.LOW: "LOW PRIORITY - Optional",
            Priority.OPTIONAL: "OPTIONAL - If Time Permits"
        }
        
        block_counter = 1
        for priority in priority_order:
            if priority in priority_groups and priority_groups[priority]:
                # Only show priority header if we have multiple priorities
                if len(priority_groups) > 1 or (len(priority_groups) == 1 and priority != Priority.MEDIUM):
                    emoji = priority_emoji.get(priority, "")
                    label = priority_labels.get(priority, priority.value.upper())
                    lines.append(f"\n**{emoji} {label}**\n")
                
                for block in priority_groups[priority]:
                    lines.append(f"#### {block_counter}. {block.course or block.exam_name} - {block.topic}")
                    lines.append(f"**Objective:** {block.objective}\n")
            
                    if block.reading_pages:
                        lines.append(f"📖 **Reading:** {block.reading_pages}\n")
                    
                    if block.practice_problems:
                        problems_list = [f"{p.text} (p. {p.page})" for p in block.practice_problems]
                        problems_str = "\n  - ".join(problems_list)
                        lines.append(f"📝 **Practice:**\n  - {problems_str}\n")
                    
                    if block.key_terms:
                        terms_str = ", ".join(block.key_terms)
                        lines.append(f"💡 **Key Terms:** {terms_str}\n")
                    
                    if block.study_question:
                        lines.append(f"❓ **Question:** {block.study_question}\n")
                    
                    # Show priority reason if available
                    if hasattr(block, 'priority_reason') and block.priority_reason:
                        lines.append(f"🎯 **Why this priority:** {block.priority_reason}\n")
                    
                    lines.append(f"⏱️ **Time:** {block.time_estimate_minutes} minutes")
                    lines.append(f" | 📊 **Evidence:** {block.confidence_score:.2f}\n")
                    
                    if block.notes:
                        lines.append(f"📌 **Note:** {block.notes}\n")
                    
                    lines.append("")  # Blank line between blocks
                    block_counter += 1
        
        lines.append("---\n")
    
    # Footer
    lines.append(f"\n*Generated by Study Agent on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    # Write to file
    output_path.write_text("\n".join(lines))


def export_to_csv(plan: StudyPlan, output_path: Path) -> None:
    """
    Export study plan to CSV format.
    
    Args:
        plan: StudyPlan to export
        output_path: Path to save CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Date",
            "Day",
            "Exam/Course",
            "Chapter",
            "Topic",
            "Learning Objective",
            "Priority",
            "Reading Pages",
            "Practice Problems",
            "Key Terms",
            "Study Question",
            "Time (min)",
            "Evidence Score"
        ])
        
        # Data rows
        for day in plan.days:
            for block in day.blocks:
                # Format practice problems for CSV
                problems_str = "; ".join([f"{p.text} (p. {p.page})" for p in block.practice_problems])
                
                # Get priority
                priority_str = getattr(block, 'priority', Priority.MEDIUM).value.upper()
                
                writer.writerow([
                    day.date,
                    day.day_name,
                    block.course or block.exam_name,
                    f"Ch {block.chapter}: {block.chapter_title}",
                    block.topic,
                    block.objective,
                    priority_str,
                    block.reading_pages,
                    problems_str,
                    ", ".join(block.key_terms),
                    block.study_question,
                    block.time_estimate_minutes,
                    f"{block.confidence_score:.2f}"
                ])


def export_to_json(plan: StudyPlan, output_path: Path) -> None:
    """
    Export study plan to pretty-printed JSON.
    
    Args:
        plan: StudyPlan to export
        output_path: Path to save JSON file
    """
    import json
    
    with open(output_path, 'w') as f:
        json.dump(plan.model_dump(mode='json'), f, indent=2, default=str)
