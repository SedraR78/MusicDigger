# Manual API tests

Every endpoint in MusicDigger was validated by hand with `curl`, including its
error cases. This file documents each test, what it checks, and what the server
is expected to return.

There is no automated test suite yet — that is the project's main technical
debt, and it is listed in the README. A runnable version of these checks lives
in `test_api.sh`.

**Setup used throughout:**

```bash
BASE="http://127.0.0.1:5006"

TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@musicdigger.test","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

## 1. Authentication

### Register a new account

```bash
curl -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"newdigger","email":"new@test.com","password":"password123"}'
```

**Expected: 201** — returns the user, an access token and a refresh token.

---

### Register with an email already taken

```bash
curl -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"whoever","email":"alex@musicdigger.test","password":"password123"}'
```

**Expected: 409 Conflict**

```json
{"error": "Email already registered", "code": 409}
```

*Why 409 and not 400: the request is well formed. It is the state of the server
that prevents it from succeeding.*

---

### Register with a password that is too short

```bash
curl -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"shorty","email":"short@test.com","password":"abc"}'
```

**Expected: 400** — `Password must be at least 8 characters`

---

### Register with a missing field

```bash
curl -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"nomail"}'
```

**Expected: 400** — the server never assumes a field is present.

---

### Log in with valid credentials

```bash
curl -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@musicdigger.test","password":"password123"}'
```

**Expected: 200** — returns both tokens.

---

### Log in with a wrong password

```bash
curl -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@musicdigger.test","password":"wrongpassword"}'
```

**Expected: 401** — `Invalid email or password`

---

### Log in with an email that does not exist

```bash
curl -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@nowhere.test","password":"password123"}'
```

**Expected: 401** — `Invalid email or password`

*The message is deliberately identical to the previous test. A different one
would let an attacker work out which emails have an account.*

*Known limitation: response time still differs slightly, since no hash is
computed when the user does not exist. That is a timing attack, identified but
not addressed.*

---

### Access a protected route without a token

```bash
curl "$BASE/api/auth/me"
```

**Expected: 401** — `Authorization token is missing`

---

### Access it with a malformed token

```bash
curl "$BASE/api/auth/me" -H "Authorization: Bearer not-a-real-token"
```

**Expected: 401** — `Invalid token`

---

### Access it with a valid token

```bash
curl "$BASE/api/auth/me" -H "Authorization: Bearer $TOKEN"
```

**Expected: 200** — returns the profile, including email and preferences.

*Note: `to_dict()` strips the email by default. This route adds it back
explicitly, so the safe behaviour is the default one.*

---

### Token expiry

Access tokens last one hour. After that:

**Expected: 401** — `Token has expired`

*Observed in real conditions during development, after roughly an hour of
testing. This is why the refresh endpoint exists.*

---

### Update the profile

```bash
curl -X PUT "$BASE/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio":"Digging since the tape era."}'
```

**Expected: 200**

---

### Delete an account without the password

```bash
curl -X DELETE "$BASE/api/auth/account" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected: 400** — `Password confirmation is required`

---

### Delete an account with a wrong password

```bash
curl -X DELETE "$BASE/api/auth/account" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"definitely-not-it"}'
```

**Expected: 403** — `Invalid password`

*A stolen token must not be enough to destroy an account. This is
re-authentication for a sensitive action.*

---

## 2. Digs

### Trending without a token

```bash
curl "$BASE/api/digs/trending"
```

**Expected: 200** — the page is public, per the Must Have user story.

---

### Trending with a period filter

```bash
curl "$BASE/api/digs/trending?period=week"
```

**Expected: 200**

---

### Trending with an invalid period

```bash
curl "$BASE/api/digs/trending?period=century"
```

**Expected: 400** — `period must be day, week or all`

---

### Read a single dig

```bash
curl "$BASE/api/digs/<dig_id>"
```

**Expected: 200** — public, this is the shareable URL.

---

### Read a dig that does not exist

```bash
curl "$BASE/api/digs/00000000-0000-0000-0000-000000000000"
```

**Expected: 404**

---

### Search without a token

```bash
curl "$BASE/api/digs/search?q=Halftime"
```

**Expected: 401** — searching the external catalogue costs API quota, so it
requires an account.

---

### Search for a track

```bash
curl "$BASE/api/digs/search?q=Halftime+Nas" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 200** — each result carries a `source` field, `spotify` or
`youtube`, which the front end shows as a badge.

---

### Create a dig without an opinion

```bash
curl -X POST "$BASE/api/digs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"spotify","external_id":"3ZFTkvIE7kyPt6Nu3PEa7V","content":""}'
```

**Expected: 400** — `An opinion is required to post a DIG`

*This is the core product rule, enforced server-side. The disabled button in
the browser is convenience, not security.*

---

### Create a dig with an unknown genre

```bash
curl -X POST "$BASE/api/digs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"spotify","external_id":"...","content":"nice","genre":"NotAGenre"}'
```

**Expected: 400** — `Unknown genre`

*The genre must belong to the canonical list. The client cannot invent one.*

---

### Create a dig with no track at all

```bash
curl -X POST "$BASE/api/digs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"a track would be nice"}'
```

**Expected: 400** — `A track or manual song details are required`

---

### Edit someone else's dig

```bash
curl -X PUT "$BASE/api/digs/<dig_id>" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"content":"I am rewriting your opinion"}'
```

**Expected: 403** — `You can only edit your own digs`

*403 rather than 404: the server knows who you are, you simply do not have the
right. Digs are public anyway, so hiding their existence would serve nothing.*

---

### Delete someone else's dig

```bash
curl -X DELETE "$BASE/api/digs/<dig_id>" \
  -H "Authorization: Bearer $TOKEN2"
```

**Expected: 403**

---

## 3. Interactions — counter integrity

### The toggle test

The most important test in the project. Three identical calls in a row:

```bash
curl -X POST "$BASE/api/digs/<dig_id>/upvote" -H "Authorization: Bearer $TOKEN"
curl -X POST "$BASE/api/digs/<dig_id>/upvote" -H "Authorization: Bearer $TOKEN"
curl -X POST "$BASE/api/digs/<dig_id>/upvote" -H "Authorization: Bearer $TOKEN"
```

**Expected:**

```json
{"is_upvoted": true,  "upvotes_count": 1}
{"is_upvoted": false, "upvotes_count": 0}
{"is_upvoted": true,  "upvotes_count": 1}
```

*This proves the denormalized counter stays in sync with the upvotes table.
Drift is the main risk of denormalization, and this is the check for it.*

*Reloading the page afterwards confirms the value was persisted, not just
returned.*

---

### Upvote without a token

```bash
curl -X POST "$BASE/api/digs/<dig_id>/upvote"
```

**Expected: 401**

---

### Upvote a dig that does not exist

```bash
curl -X POST "$BASE/api/digs/00000000-0000-0000-0000-000000000000/upvote" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 404**

---

### ReDig your own dig

```bash
curl -X POST "$BASE/api/digs/<your_own_dig>/redig" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 400** — `You cannot redig your own dig`

*Two reasons: it makes no sense functionally, since the dig is already in your
feed. And it would let anyone inflate their own Trending score, as a ReDig is
worth two points.*

---

### List comments without a token

```bash
curl "$BASE/api/digs/<dig_id>/comments"
```

**Expected: 200** — public.

---

### Post an empty comment

```bash
curl -X POST "$BASE/api/digs/<dig_id>/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"   "}'
```

**Expected: 400** — whitespace is stripped before validation.

---

### Post a comment

```bash
curl -X POST "$BASE/api/digs/<dig_id>/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"That sax loop is four seconds of perfection"}'
```

**Expected: 201** — returns the comment and the updated `comments_count`.

---

### Delete a comment that is not yours

```bash
curl -X DELETE "$BASE/api/digs/comments/<comment_id>" \
  -H "Authorization: Bearer $TOKEN2"
```

**Expected: 403** — `You can only delete your own comments`

---

## 4. Social

### Public profile without a token

```bash
curl "$BASE/api/users/alexwaves"
```

**Expected: 200** — returns the profile and recent digs, without the email.

---

### Profile of a user that does not exist

```bash
curl "$BASE/api/users/definitely-not-a-user"
```

**Expected: 404**

---

### Follow someone

```bash
curl -X POST "$BASE/api/users/samecho/follow" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 200**

```json
{"is_following": true, "followers_count": 1}
```

---

### Follow yourself

```bash
curl -X POST "$BASE/api/users/alexwaves/follow" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 400** — `You cannot follow yourself`

---

### The feed without a token

```bash
curl "$BASE/api/digs/feed"
```

**Expected: 401** — the feed is personal by definition.

---

### The feed with a token

```bash
curl "$BASE/api/digs/feed" -H "Authorization: Bearer $TOKEN"
```

**Expected: 200** — digs from followed users, newest first.

---

## 5. Messaging

### Open a conversation

```bash
curl -X POST "$BASE/api/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"juliemoon"}'
```

**Expected: 200** — returns the conversation.

*200 and not 201, because the operation may create nothing: if the conversation
already exists it is returned as is.*

---

### Open the same conversation again

Running the exact same command a second time.

**Expected: the same conversation id.**

*This works thanks to the canonical ordering of participant ids: the two ids
are sorted before being stored, so (A,B) and (B,A) always produce the same row.
Combined with the unique constraint, a duplicate is impossible.*

---

### Open a conversation with a user that does not exist

```bash
curl -X POST "$BASE/api/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"ghost-user-9999"}'
```

**Expected: 404**

---

### Send a message

```bash
curl -X POST "$BASE/api/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<conv_id>","content":"You need to hear this"}'
```

**Expected: 201**

---

### Send a message with a shared DIG

```bash
curl -X POST "$BASE/api/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<conv_id>","content":"Listen to this","dig_id":"<dig_id>"}'
```

**Expected: 201** — the message carries the dig, rendered as an embedded card
in the interface.

---

### Send an empty message

```bash
curl -X POST "$BASE/api/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<conv_id>","content":""}'
```

**Expected: 400**

---

### Read messages as a participant

```bash
curl "$BASE/api/conversations/<conv_id>/messages" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 200**

---

### Read with an invalid `since` parameter

```bash
curl "$BASE/api/conversations/<conv_id>/messages?since=not-a-date" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected: 400** — a malformed date gives a clear client error, not a 500.

---

## 6. Access control

The section worth showing first.

### Setup

Three accounts. `alexwaves` and `juliemoon` have a private conversation.
`samecho` is not part of it, but knows its id.

```bash
INTRUDER=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"sam@musicdigger.test","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

### An outsider tries to READ the conversation

```bash
curl "$BASE/api/conversations/<conv_id>/messages" \
  -H "Authorization: Bearer $INTRUDER"
```

**Expected: 403**

```json
{"error": "You are not part of this conversation", "code": 403}
```

---

### An outsider tries to WRITE into it

```bash
curl -X POST "$BASE/api/messages" \
  -H "Authorization: Bearer $INTRUDER" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<conv_id>","content":"I should not be able to do this"}'
```

**Expected: 403**

*The check runs on read and on write. Protecting only the send would let anyone
read a private conversation by guessing an id — that is the classic mistake
this test exists to rule out.*

---

### SQL injection attempt

```bash
curl "$BASE/api/search?q=%27%3B%20DROP%20TABLE%20users%3B--"
```

Decoded, the query is `'; DROP TABLE users;--`

**Expected: 200 with no results.**

*The ORM passes values as bound parameters, never as concatenated SQL, so the
payload is searched for literally as text. There is no raw SQL anywhere in the
project.*

---

## 7. Search

### Global search

```bash
curl "$BASE/api/search?q=Nas"
```

**Expected: 200** — users, artists, albums and tracks matching the query.

---

### Search with an invalid type

```bash
curl "$BASE/api/search?q=Nas&type=notatype"
```

**Expected: 400** — `type must be one of: all, user, artist, album, track, genre`

---

### Search with a single character

```bash
curl "$BASE/api/search?q=a"
```

**Expected: 200 with empty results** — the minimum is two characters, otherwise
a single letter would return half the database.

---

### Suggestions

```bash
curl "$BASE/api/search/suggest?q=al"
```

**Expected: 200** — a light payload with labels only, since this is called on
every keystroke.

---

## 8. DigsCover

The same endpoint behaves in three different modes.

### Anonymous, no criteria

```bash
curl "$BASE/api/digscover"
```

**Expected: 200, `mode: empty`** — with a prompt inviting the visitor to pick
criteria. A visitor with no criteria and no account provides no signal, so
returning random tracks would be dishonest.

---

### With criteria

```bash
curl "$BASE/api/digscover?artists=Nas"
```

**Expected: 200, `mode: criteria`**

---

### Logged in

```bash
curl "$BASE/api/digscover" -H "Authorization: Bearer $TOKEN"
```

**Expected: 200, `mode: personalized`** — every track carries a
`reason_label` explaining why it was picked:

```
"Because you dig The Notorious B.I.G."
"Fans also dig this"
"Matches your genre: Boom Bap"
```

*The second one comes from the collaborative filtering. It only appears when
several users have dug overlapping tracks, which is why the seed deliberately
crosses digs between accounts.*

---

### Random dig

```bash
curl "$BASE/api/digscover/random"
```

**Expected: 200** — a dig picked at random, outside any personalization.

---

## 9. Rate limiting

The login endpoint allows five attempts per minute per IP.

```bash
for i in $(seq 1 7); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"bruteforce@test.com","password":"guess"}'
done
```

**Expected:**

```
401
401
401
401
401
429    ← rate limited
429
```

*Without this, a script could try thousands of passwords a minute.*

**Known limitations:** the counters live in memory, so they reset when the
server restarts and are not shared between instances. And limiting by IP alone
does not stop credential stuffing, where one password is tried against many
accounts from many addresses. Limiting by attempted email as well would help.

---

## Summary

| Area | Endpoints | Error cases covered |
| --- | --- | --- |
| Authentication | 7 | 400, 401, 403, 409 |
| Digs | 7 | 400, 401, 403, 404 |
| Interactions | 5 | 400, 401, 403, 404 |
| Social | 4 | 400, 401, 404 |
| Messaging | 4 | 400, 403, 404 |
| Search | 2 | 400 |
| DigsCover | 2 | 404 |
| Rate limiting | — | 429 |

**Not covered by automated tests.** Every check above was run by hand. The four
priority tests from the QA plan — outsider reading a conversation, editing
someone else's dig, expired token, rate limiting — are all verified manually
but not yet written in pytest. That is the project's main technical debt.
