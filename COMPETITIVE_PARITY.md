# Xerus — competitive parity

**Target:** TikTok / Instagram Reels

| Feature | API (services/api) |
|---------|---------------------|
| For You feed | `GET /feed/for-you` |
| Following feed | `GET /feed/following?user=` |
| Upload | `POST /videos` |
| Like / comment / share | `/videos/{id}/like|comments|share` |
| Follow | `POST /follow` |
| Hashtag search | `GET /search?hashtag=` |
| Profile | `GET /users/{handle}` |

```bash
cd services/api && python3 server.py
# http://127.0.0.1:8790/feed
```
