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

## Project Knowledge (Current State)
### Product Scope
- Web-based Chinese character flashcards for children with responsive UI (mobile/iPad/PC).
- Users log in with preconfigured accounts (no UI registration).
- Users input characters only; pinyin is generated offline and common-word hints come from THUOCL.
- Learning uses spaced repetition (SM-2) and tracks study time.
- Multi-dictionary model: each user owns dictionaries; dictionaries can be public/private.
  - Public dictionaries are read-only for non-owners.

### Backend
- Framework: FastAPI (Python 3.6.9 compatible).
- Config: `backend/app/core/config.yaml`, loaded by `backend/app/core/config.py`.
- Auth: JWT + bcrypt; login at `/auth/login`.
- CORS: currently allow all origins for dev.
- SQLite schema: `dictionaries`, `characters`, `study_records`, `study_sessions`.
- Migration script: `backend/app/core/migrate_to_dictionaries.py`
  - Creates default private dictionary “我的字库” per user.
  - `--mode all` copies full legacy characters; `--mode studied` copies only studied.

### Backend API (Dictionary-scoped)
- `GET /dictionaries` list visible dictionaries (owner + public).
- `POST /dictionaries` create dictionary.
- `PATCH /dictionaries/{id}` update dictionary (owner only).
- `DELETE /dictionaries/{id}` delete dictionary (owner only).
- `POST /dictionaries/{id}/characters/import` import characters (owner only).
- `GET /dictionaries/{id}/characters/list` list characters (read allowed).
- `GET /dictionaries/{id}/characters/{hanzi}/info` info with pinyin + common words.
- `GET /dictionaries/{id}/study/queue` get queue.
- `POST /dictionaries/{id}/study/review` submit review.
- `POST /dictionaries/{id}/study/session/start|end` session tracking.
- `GET /dictionaries/{id}/stats/summary` stats.

### Frontend
- Framework: Vue 3 + Vite.
- Auth state: `frontend/src/store/auth.js` (localStorage token).
- Dictionary state: `frontend/src/store/dictionary.js` (current dictionary + list).
- API client: `frontend/src/api/client.js` uses `VITE_API_BASE`.
- Pages:
  - Login: `frontend/src/pages/LoginPage.vue` (eye icon toggle).
  - Study: `frontend/src/pages/StudyPage.vue` (card, SM-2 review, audio toggles, dictionary card).
  - Input: `frontend/src/pages/InputPage.vue` (dictionary select + create, grouped preview, read-only warnings).
  - Stats: `frontend/src/pages/StatsPage.vue` (summary + progress bars + weekly placeholder).
  - Dictionaries: `frontend/src/pages/DictionariesPage.vue` (create/edit/delete, public/private).
- Navigation: top + bottom nav in `frontend/src/App.vue`.

### Deployment Notes
- Dev: set `VITE_API_BASE=http://127.0.0.1:8000` before `npm run dev`.
- Apache production: build with `VITE_API_BASE=/api`, deploy `dist/` to `/var/www/hanzi-cards`, proxy `/api` to backend.
- systemd service example in `README.md`.

## Open Decisions
- Confirm THUOCL word list variant (e.g., THUOCL词表合集 or high-frequency subset)
- Finalize auth config format (YAML)
- Confirm frontend framework (Vue 3)
