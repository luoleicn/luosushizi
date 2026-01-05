# Development Plan & Log

## Project Overview
A web-based Chinese character flashcard tool for children. Users log in with preconfigured accounts, input characters only, and learn via an adaptive spaced-repetition algorithm. The system auto-fetches pinyin and definitions from an online API, caches results, and syncs progress across devices.

## Requirements (Confirmed)
- Web app, responsive for mobile/iPad/PC
- Login required; accounts are configured server-side (no registration UI)
- Users input only Chinese characters
- Offline pinyin and common word suggestions (no network dependency)
- Learning flow: show character -> known/unknown -> if unknown show pinyin+definition+hint -> next
- Intelligent spaced repetition (SM-2 or improved)
- Track study time and use it in scheduling
- Cross-device sync per account

## Milestones
1) Product & UX design
2) Backend API & data model
3) Frontend implementation
4) Algorithm & scheduling
5) QA & polish

## Detailed Plan
### 1) Product & UX
- Define main screens: Login, Character Input, Study Session, Review Queue, Progress/Stats (lightweight)
- Determine mobile-first layout, large touch targets, high readability
- Decide minimal flows to reduce cognitive load for children

### 2) Backend API & Data Model
- Python FastAPI
- Auth: config-based accounts, JWT tokens
- DB: SQLite (dev) + migration path for Postgres
- Offline dictionary: pypinyin for pinyin, THUOCL word list for common word suggestions
- Use THUOCL full collection; show top 3 highest-frequency words per character
- Models:
  - User
  - Character (hanzi, pinyin, source, cached_at)
  - CommonWord (word, frequency, source)
  - CharacterWordIndex (hanzi, word_id)
  - StudyRecord (user_id, character_id, ease_factor, interval, repetitions, last_reviewed_at, next_review_at, last_rating)
  - StudySession (user_id, started_at, ended_at, total_cards, known_count, unknown_count)
- Endpoints:
  - POST /auth/login
  - POST /characters/import
  - GET /characters/list
  - GET /study/queue
  - POST /study/review
  - GET /characters/{hanzi}/info
  - GET /stats/summary

#### THUOCL Import & Index Build
- Download THUOCL full collection text files
- Parse each line into word + frequency
- Persist CommonWord with frequency
- Build CharacterWordIndex by splitting each word into characters
- Query path: given hanzi, join CharacterWordIndex -> CommonWord, order by frequency desc, limit 3

#### Character Info Response (Offline)
- hanzi
- pinyin (from pypinyin)
- common_words: array of {word, frequency}

#### API Sketch (Request/Response)
- POST /auth/login
  - Request: {username, password}
  - Response: {access_token, token_type, user}
- POST /characters/import
  - Request: {items: [hanzi]}
  - Response: {imported, skipped}
- GET /characters/list
  - Response: {items: [{hanzi, pinyin}]}
- GET /characters/{hanzi}/info
  - Response: {hanzi, pinyin, common_words}
- GET /study/queue
  - Response: {items: [{hanzi, pinyin, due_at, is_new}]}
- POST /study/review
  - Request: {hanzi, rating, reviewed_at}
  - Response: {next_review_at, interval, ease_factor}
- GET /stats/summary
  - Response: {total, known, unknown, due_today, study_time_total}

### 3) Frontend
- Responsive layout (CSS Grid/Flex + media queries)
- Pages:
  - Login
  - Character Input (paste/import)
  - Study (card display + actions)
  - Simple stats
- UX rules:
  - Big type, minimal UI
  - One primary action per step
  - Clear feedback on progress

#### Study Interaction (Unknown)
- Show hanzi by default
- If user taps "Unknown": reveal pinyin + top 3 common words
- Provide "Next" button to continue

### Project Structure (Proposed)
- /backend
  - app/main.py
  - app/api/
  - app/models/
  - app/services/dictionary/
  - app/services/scheduler/
  - app/core/config.yaml
  - data/thuocl/
- /frontend
  - src/pages/
  - src/components/
  - src/api/

### 4) Algorithm
- Use SM-2 with adjustments for unknown answers
- Ratings mapping:
  - Known = 4 or 5
  - Unknown = 2 or 1
- Update schedule on each review
- Include same-day re-queue for unknowns

### 5) QA & Polish
- Ensure API errors handled gracefully
- Verify mobile layout on small screens
- Add basic logging and audit trail

## Progress Log
- 2025-xx-xx: Initialized development plan and requirements.

## Open Decisions
- Confirm THUOCL word list variant (e.g., THUOCL词表合集 or high-frequency subset)
- Finalize auth config format (YAML)
- Confirm frontend framework (Vue 3)
