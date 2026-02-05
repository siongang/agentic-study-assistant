# Usage Guide

How to use the Agentic Study Planner in practice.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Terminal Chat Interface](#terminal-chat-interface)
3. [Core Workflows](#core-workflows)
4. [Example Sessions](#example-sessions)
5. [Commands Reference](#commands-reference)
6. [Best Practices](#best-practices)
7. [Advanced Usage](#advanced-usage)

---

## Quick Start

### 1. Add your textbooks

Place PDF files in the `data/uploads/` directory:

```bash
cp ~/Downloads/physics_textbook.pdf data/uploads/physics.pdf
cp ~/Downloads/biology_textbook.pdf data/uploads/biology.pdf
```

**Naming convention**: Use descriptive names like `physics.pdf`, `biology.pdf`, `chemistry.pdf`.

### 2. Start the chat interface

```bash
source .venv/bin/activate  # Activate virtual environment
python -m app.main
```

You should see:

```
╔═══════════════════════════════════════════════════╗
║      Agentic Study Planner - Terminal Chat        ║
║                                                   ║
║  Type your message below.                         ║
║  Commands: help, status, clear, quit              ║
╚═══════════════════════════════════════════════════╝

>
```

### 3. Tell the agent what you need

```
> I added physics and biology textbooks.
> My physics exam is February 21.
> My biology exam is February 25.
> Make me a day-by-day study plan.
```

The agent will:
1. Detect new textbooks
2. Ingest them (extract topics, create embeddings)
3. Generate a study plan
4. Show you the results

---

## Terminal Chat Interface

### How it works

The chat interface is a **conversational loop**:

```
You → RootAgent → [specialized agents] → Tools → Response
```

The **RootAgent** decides which agent to call based on your message.

### Available commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `status` | Show system status (materials, plan, coverage) |
| `clear` | Clear conversation history |
| `quit` | Exit the chat |

### Example interaction

```
> status

📚 Materials Registry:
  - Physics (physics.pdf)
    ✓ Ingested, 18 topics
  - Biology (biology.pdf)
    ✓ Ingested, 24 topics

📅 Current Plan:
  ✓ Valid
  - Start: Feb 5
  - End: Feb 25
  - Days: 20
  - Topics: 42/42 (100%)

> help

Available Commands:
  status   - Show materials, plan, and coverage
  clear    - Clear conversation history
  quit     - Exit the chat

Natural language commands:
  "Explain [topic]"           - Get explanation from textbooks
  "Make me a plan"            - Generate study schedule
  "Show coverage"             - Display topic coverage
  "I added [course] textbook" - Trigger ingestion

> quit

Goodbye! Your study plan is saved in data/plans/study_plan.md
```

---

## Core Workflows

### Workflow 1: Initial Setup (First Time)

**Goal**: Set up your first study plan.

**Steps**:

1. **Add textbooks**:
   ```bash
   cp ~/Downloads/*.pdf data/uploads/
   ```

2. **Start the chat**:
   ```bash
   python -m app.main
   ```

3. **Provide information**:
   ```
   > I have three textbooks: physics, biology, and chemistry.
   > My exams are:
   > - Physics: February 21
   > - Biology: February 25
   > - Chemistry: March 5
   > I can study 3 hours per day.
   > Please make me a study plan.
   ```

4. **Wait for ingestion**:
   ```
   [Ingesting physics.pdf...]
   ✓ Extracted 18 topics
   ✓ Created 234 chunks
   ✓ Generated embeddings
   
   [Ingesting biology.pdf...]
   ✓ Extracted 24 topics
   ...
   ```

5. **Review plan**:
   ```
   ✓ Study plan generated!
   
   Coverage:
   - Physics: 18/18 topics ✓
   - Biology: 24/24 topics ✓
   - Chemistry: 32/32 topics ✓
   
   Plan saved to: data/plans/study_plan.md
   ```

6. **Check the plan**:
   ```bash
   cat data/plans/study_plan.md
   ```

---

### Workflow 2: Adding a New Textbook

**Goal**: Add a new course mid-way through your study period.

**Steps**:

1. **Add the PDF**:
   ```bash
   cp ~/Downloads/calculus.pdf data/uploads/
   ```

2. **Tell the agent**:
   ```
   > I added a calculus textbook. My calculus exam is March 10.
   ```

3. **Agent response**:
   ```
   [Detected new material: calculus.pdf]
   [Ingesting...]
   ✓ Extracted 28 topics
   
   ⚠️ Your current study plan does not include calculus topics.
   Would you like me to regenerate the plan?
   ```

4. **Confirm**:
   ```
   > Yes, regenerate the plan.
   ```

5. **New plan generated**:
   ```
   ✓ Updated plan includes all 4 courses.
   Coverage: 102/102 topics ✓
   ```

---

### Workflow 3: Replacing a Textbook

**Goal**: Swap an old edition for a new edition.

**Steps**:

1. **Replace the file**:
   ```bash
   # Remove old version
   rm data/uploads/physics.pdf
   
   # Add new version
   cp ~/Downloads/physics_new_edition.pdf data/uploads/physics.pdf
   ```

2. **Tell the agent**:
   ```
   > I replaced my physics textbook with a new edition.
   ```

3. **Agent detects change**:
   ```
   [File hash changed for physics.pdf]
   [Invalidating old artifacts...]
   [Re-ingesting...]
   
   ✓ Re-ingested physics textbook
   - Old: 18 topics
   - New: 20 topics (added 2 new chapters)
   
   ⚠️ Your study plan is now invalid.
   Would you like me to regenerate it?
   ```

4. **Regenerate**:
   ```
   > Yes, please.
   
   ✓ New plan generated with updated physics topics.
   ```

---

### Workflow 4: Tutoring (RAG-based Q&A)

**Goal**: Get explanations and help from your textbooks.

**Steps**:

1. **Ask a question**:
   ```
   > Explain the difference between velocity and acceleration.
   ```

2. **Agent retrieves and explains**:
   ```
   Based on your physics textbook:
   
   **Velocity** is the rate of change of displacement with respect to time.
   It's a vector quantity (has magnitude and direction).
   (Physics textbook, pp. 7-9)
   
   **Acceleration** is the rate of change of velocity with respect to time.
   It indicates how quickly velocity is changing.
   (Physics textbook, pp. 12-15)
   
   Key difference: Velocity measures how position changes; acceleration 
   measures how velocity itself changes.
   
   **Example**: A car moving at constant 60 mph has velocity but zero 
   acceleration. When the car speeds up to 70 mph, it has positive acceleration.
   
   Would you like a practice problem?
   ```

3. **Request practice**:
   ```
   > Yes, give me a practice problem.
   
   **Problem**: A car travels at 20 m/s. After 5 seconds, its velocity 
   is 35 m/s. What is its average acceleration?
   
   (Hint: a = Δv / Δt)
   ```

4. **Check answer**:
   ```
   > The answer is 3 m/s².
   
   ✓ Correct! 
   
   Calculation: a = (35 - 20) / 5 = 15 / 5 = 3 m/s²
   ```

---

### Workflow 5: Checking Coverage

**Goal**: Verify all topics are scheduled before exams.

**Steps**:

1. **Ask for coverage**:
   ```
   > Show me topic coverage for physics.
   ```

2. **Agent response**:
   ```
   Physics Topic Coverage:
   
   ✓ Kinematics (scheduled: Feb 5, 8)
   ✓ Dynamics (scheduled: Feb 6, 10)
   ✓ Energy (scheduled: Feb 12, 15)
   ✓ Momentum (scheduled: Feb 14, 18)
   ...
   ✓ Waves (scheduled: Feb 19, 20)
   
   Coverage: 18/18 topics (100%)
   Exam date: Feb 21 ✓
   ```

3. **Check all courses**:
   ```
   > Show overall coverage.
   
   Overall Coverage:
   
   Physics:    18/18 (100%) ✓
   Biology:    24/24 (100%) ✓
   Chemistry:  32/32 (100%) ✓
   
   Total: 74/74 topics scheduled ✓
   ```

---

## Example Sessions

### Session 1: Complete First-Time Setup

```
$ python -m app.main

╔═══════════════════════════════════════════════════╗
║      Agentic Study Planner - Terminal Chat        ║
╚═══════════════════════════════════════════════════╝

> I'm preparing for two exams. I have physics and biology textbooks 
> in data/uploads/. Physics exam is Feb 21, biology is Feb 25. 
> I want to study 3 hours per day. Make me a plan.

[Scanning data/uploads/...]
[Found: physics.pdf, biology.pdf]

[Ingesting physics.pdf...]
✓ Parsed 456 pages
✓ Extracted 18 topics
✓ Created 234 chunks
✓ Generated embeddings

[Ingesting biology.pdf...]
✓ Parsed 523 pages
✓ Extracted 24 topics
✓ Created 298 chunks
✓ Generated embeddings

[Generating study plan...]
✓ Allocated 42 topics across 20 days
✓ Average workload: 2.8 hrs/day

[Verifying plan...]
✓ Physics: 18/18 topics covered
✓ Biology: 24/24 topics covered
✓ No deadline violations
✓ Workload within limits

📅 Study Plan Summary:

Period: Feb 5 - Feb 25 (20 days)

Physics (18 topics, exam Feb 21):
  - Scheduled over 16 days
  - Avg 2.5 hrs/day

Biology (24 topics, exam Feb 25):
  - Scheduled over 20 days
  - Avg 3.2 hrs/day

Detailed plan saved to: data/plans/study_plan.md

> status

📚 Materials Registry:
  ✓ Physics (physics.pdf) - 18 topics
  ✓ Biology (biology.pdf) - 24 topics

📅 Current Plan:
  ✓ Valid
  - Coverage: 42/42 (100%)
  - Start: Feb 5
  - End: Feb 25

> quit
```

---

### Session 2: Tutoring Session

```
> Explain Newton's first law.

Based on your physics textbook:

**Newton's First Law** (Law of Inertia):
"An object at rest stays at rest, and an object in motion stays in 
motion with constant velocity, unless acted upon by a net external force."

(Physics textbook, pp. 67-70)

**Key Points**:
1. **Inertia**: The tendency of objects to resist changes in motion
2. **Net force = 0**: No acceleration occurs
3. **Constant velocity**: Speed AND direction remain unchanged

**Examples**:
- A book on a table stays at rest (no net force)
- A hockey puck on ice slides with constant velocity (negligible friction)
- You lurch forward when a car brakes suddenly (your body wants to 
  maintain its forward motion)

Would you like to see how this relates to Newton's second law?

> Yes.

Newton's Second Law extends the first law:

**F = ma** (Force equals mass times acceleration)

Connection to First Law:
- When F = 0 (no net force), then a = 0 (no acceleration)
- This is Newton's First Law as a special case!

(Physics textbook, pp. 71-74)

The first law tells us WHAT happens with zero net force.
The second law tells us WHAT HAPPENS with non-zero net force.

> Give me a practice problem.

**Problem**:

A 5 kg object is at rest. Two forces act on it:
- Force 1: 20 N to the right
- Force 2: 15 N to the left

What is the object's acceleration?

(Hint: Find net force first, then use F = ma)

> Net force is 5N right, so a = 5/5 = 1 m/s² to the right.

✓ Exactly right!

Step-by-step:
1. Net force = 20N - 15N = 5N (to the right)
2. F = ma → a = F/m = 5N / 5kg = 1 m/s²

Great work! This demonstrates how multiple forces combine to 
produce acceleration.
```

---

### Session 3: Handling Changes

```
> I just got a new physics textbook (updated edition). I replaced 
> the old one in data/uploads/.

[Checking materials...]
[Hash mismatch for physics.pdf - file was changed]

[Invalidating old artifacts...]
✓ Removed old topic inventory
✓ Removed old chunks
✓ Removed old vector index

[Re-ingesting physics.pdf...]
✓ Parsed 492 pages (36 more than before)
✓ Extracted 20 topics (2 new chapters)
✓ Created 267 chunks
✓ Generated embeddings

New topics added:
- Chapter 19: Relativity (pp. 450-475)
- Chapter 20: Quantum Mechanics Intro (pp. 476-492)

⚠️ Your current study plan is now INVALID because:
- Physics topic count changed (18 → 20)
- New chapters need to be scheduled

Would you like me to generate a new plan?

> Yes, but I want to prioritize the new chapters since they might 
> be harder.

[Generating new plan with prioritization...]

✓ New chapters scheduled earlier:
  - Relativity: Feb 6, 11, 16 (3 sessions)
  - Quantum Mechanics: Feb 9, 13, 17 (3 sessions)

✓ Total coverage: 44 topics (20 physics + 24 biology)

Updated plan saved to: data/plans/study_plan.md

> Thanks!

You're welcome! Good luck with the new material.
```

---

## Commands Reference

### Status Commands

| Command | Description | Example Output |
|---------|-------------|----------------|
| `status` | Show system state | Materials, plan validity, coverage |
| `materials` | List textbooks | Files, topics, ingestion status |
| `plan` | Show plan summary | Date range, coverage, workload |
| `coverage [course]` | Show topic coverage | Scheduled vs. required topics |

### Action Commands

| Command | Description | Example |
|---------|-------------|---------|
| `ingest [course]` | Manually trigger ingestion | `ingest physics` |
| `replan` | Regenerate study plan | `replan` |
| `export [format]` | Export plan to format | `export markdown` |

### Utility Commands

| Command | Description |
|---------|-------------|
| `help` | Show command list |
| `clear` | Clear conversation history |
| `quit` | Exit chat |

---

## Best Practices

### 1. Textbook Naming

Use descriptive, course-based names:

✅ **Good**:
- `physics.pdf`
- `biology_campbell.pdf`
- `chemistry_organic.pdf`

❌ **Bad**:
- `book1.pdf`
- `textbook_final_v3_ACTUAL.pdf`
- `Download (2).pdf`

### 2. When to Regenerate Plans

Regenerate when:
- ✅ You add/remove/replace a textbook
- ✅ Exam dates change
- ✅ Your available study time changes
- ✅ You want to reprioritize topics

Don't regenerate when:
- ❌ You just want to see a topic explanation
- ❌ You're checking coverage (use `status` instead)
- ❌ You're marking progress (future feature)

### 3. Effective Questions for Tutoring

**Good questions** (specific, grounded):
- "Explain the difference between X and Y"
- "What is the formula for Z?"
- "Give me an example of concept W"
- "How does A relate to B?"

**Less effective** (too broad):
- "Tell me about chapter 3"
- "What should I know for the exam?"
- "Summarize everything"

### 4. File Organization

Keep your workspace clean:

```
data/uploads/          # Only current textbooks
data/uploads/archive/  # Old versions (optional)
```

Don't mix:
- ❌ Lecture slides
- ❌ Practice problems
- ❌ Notes

(These might be supported in future versions)

### 5. Review Generated Plans

After generation, always review `data/plans/study_plan.md`:

- ✅ Check daily workload is reasonable
- ✅ Verify difficult topics have enough time
- ✅ Make sure buffer exists before exams

---

## Advanced Usage

### Custom Constraints

Provide detailed constraints for better plans:

```
> Make me a plan with these rules:
> - No studying on Saturdays
> - Physics topics should be spaced at least 2 days apart
> - Prioritize biology topics related to genetics
> - Reserve last 2 days before each exam for review only
```

### Multi-Session Studying

For long-term planning:

```
> I want to study each topic twice: once for learning, once for review.
> Learning sessions should happen first, then review sessions 5-7 days later.
```

### Integrating External Deadlines

```
> I have a midterm on March 1 that covers topics 1-10 in physics.
> Make sure those are scheduled before March 1, with review time.
```

### Exporting Plans

```
> Export my plan to Google Calendar format.

[Generates ICS file]
✓ Saved to: data/plans/study_plan.ics

Import this file into Google Calendar to sync events.
```

---

## Troubleshooting

### Issue: "No textbooks found"

**Cause**: PDFs not in `data/uploads/`

**Fix**:
```bash
ls data/uploads/  # Check what's there
cp ~/path/to/textbook.pdf data/uploads/
```

### Issue: "Ingestion failed"

**Possible causes**:
1. PDF is encrypted
2. PDF is corrupted
3. File is not a valid PDF

**Fix**:
```bash
# Test PDF manually
python -c "import fitz; doc = fitz.open('data/uploads/file.pdf'); print(len(doc))"
```

### Issue: "Coverage is 0%"

**Cause**: Plan hasn't been generated yet

**Fix**:
```
> Make me a study plan.
```

### Issue: Plan seems unrealistic

**Cause**: Constraints are too tight or topics are imbalanced

**Fix**:
```
> My plan looks too packed. Can you spread it out more? I can study until March 10 instead.
```

---

## Tips for Success

1. **Ingest early**: Add textbooks as soon as possible (ingestion takes time)
2. **Review daily**: Check your plan each morning
3. **Ask questions**: Use the tutor agent frequently
4. **Update proactively**: If exams change, update immediately
5. **Trust the coverage**: The system guarantees 100% topic coverage

---

**Next**: [Architecture Documentation →](ARCHITECTURE.md)
