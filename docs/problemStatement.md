## MeetIQ — Problem Statement

Modern teams spend a significant amount of time in meetings discussing project updates, decisions, blockers, and next steps. After a meeting ends, critical information often becomes **lost, delayed, or fragmented** across personal notes, chat messages, and follow-up emails.

### What goes wrong today

Teams commonly struggle with:

- **Forgetting decisions** made during the meeting
- **Missing context** when someone can’t attend live
- **Unclear ownership** of action items
- **Poor tracking** of next steps and deadlines
- **Extra manual work** to write notes, summaries, and follow-ups

These gaps reduce productivity and create a disconnect between **discussion** and **execution**.

### Proposed solution

Build **MeetIQ** — a platform that converts meeting recordings into a structured, shareable set of outputs:

- **Executive summary**
- **Key discussion points**
- **Decisions made**
- **Action items**
- **Owners** (when identifiable)
- **Deadlines** (when mentioned)

### Objective

Reduce post-meeting manual effort while improving **alignment**, **accountability**, and **access to meeting outcomes**.

---

## MVP Scope

### Inputs

- **Audio recordings**: `.mp3`, `.wav`, `.m4a`
- **Video recordings**: optional

### Outputs

- **Executive summary**
- **Key discussion points**
- **Decisions made**
- **Action items**
- **Owners** (if identified)
- **Deadlines** (if mentioned)

---

## Target users

### Primary users

- **Product Managers**
- **Startup founders**
- **Engineering managers**
- **Remote teams**
- **Students working on group projects**

### User goal

> “I want to quickly understand what happened in a meeting and know exactly what actions need to be taken next.”

---

## APIs and datasets

### 1) Speech-to-text (STT)

- **Tool**: Whisper (open source)
- **Repository**: `https://github.com/openai/whisper`
- **Purpose**: Convert meeting recordings into a transcript
- **Input**: Audio recording
- **Output**: Timestamped transcript
- **Cost**: Free (run locally)

### 2) LLM for meeting analysis

- **Tool**: Groq API
- **Console**: `https://console.groq.com/`
- **Purpose**:
  - Meeting summarization
  - Decision extraction
  - Action item extraction
  - Deadline identification
- **Cost**: Free tier available

### 3) Test dataset — meeting recordings

- **Dataset**: AMI Meeting Corpus
- **Homepage**: `http://groups.inf.ed.ac.uk/ami/corpus/`
- **Contains**:
  - Real meeting recordings
  - Audio files
  - Human-generated annotations
  - Meeting transcripts
- **Use**:
  - Testing transcript quality
  - Benchmarking summaries
- **Cost**: Free

### 4) Additional dataset

- **Dataset**: ICSI Meeting Corpus
- **Homepage**: `https://www1.icsi.berkeley.edu/Speech/mr/`
- **Contains**:
  - Multi-speaker meetings
  - Meeting transcripts
  - Discussion recordings
- **Use**:
  - Speaker interaction testing
  - Multi-person meeting analysis
- **Cost**: Free

### 5) Summarization benchmark dataset

- **Dataset**: QMSum
- **Repository**: `https://github.com/Yale-LILY/QMSum`
- **Contains**:
  - Meeting transcripts
  - Human-written summaries
- **Use**: Evaluating summary quality
- **Cost**: Free