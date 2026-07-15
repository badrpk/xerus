from __future__ import annotations
"""Xerus short-video social API — parity with TikTok / Reels core surfaces."""
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent))

import random
from http_util import JsonAPI, serve, uid, iso

USERS = {
    "u1": {"id": "u1", "handle": "badar", "display": "Badar", "followers": 1200, "following": 180},
    "u2": {"id": "u2", "handle": "laiba", "display": "Laiba", "followers": 5400, "following": 90},
    "u3": {"id": "u3", "handle": "rangoons", "display": "Rangoons", "followers": 890, "following": 40},
}
VIDEOS = [
    {"id": "v1", "user_id": "u2", "caption": "Kitchen reel #food", "hashtags": ["food", "reels"],
     "sound": "original_audio", "duration_sec": 18, "likes": 420, "comments": 33, "shares": 12, "views": 9200, "created_at": iso()},
    {"id": "v2", "user_id": "u1", "caption": "Build in public", "hashtags": ["buildinpublic", "dev"],
     "sound": "lofi_loop", "duration_sec": 25, "likes": 210, "comments": 14, "shares": 8, "views": 4100, "created_at": iso()},
    {"id": "v3", "user_id": "u3", "caption": "Flash sale tomorrow", "hashtags": ["shop", "sale"],
     "sound": "hype_beat", "duration_sec": 12, "likes": 980, "comments": 77, "shares": 40, "views": 22000, "created_at": iso()},
]
COMMENTS: dict[str, list] = {}
FOLLOWS: set[tuple[str, str]] = set()
LIKES: set[tuple[str, str]] = set()

def enrich(v, viewer=None):
    u = USERS.get(v["user_id"], {})
    return {**v, "author": u, "liked_by_me": (viewer, v["id"]) in LIKES if viewer else False}

class H(JsonAPI):
    def do_GET(self):
        path, q = self.parse()
        if path in ("/", "/health"):
            return self._send(200, {"ok": True, "service": "xerus", "version": "2.0.0",
                                    "parity_target": "TikTok / Instagram Reels core APIs"})
        if path == "/capabilities":
            return self._send(200, {"ok": True, "competitor": "TikTok", "features": [
                "for_you_feed", "following_feed", "upload", "like", "comment", "follow",
                "hashtag_search", "sounds", "profile", "share_count"
            ]})
        viewer = (q.get("user") or [None])[0]
        if path in ("/feed", "/feed/for-you"):
            ranked = sorted(VIDEOS, key=lambda v: v["likes"] * 2 + v["views"] * 0.01 + random.random(), reverse=True)
            return self._send(200, {"ok": True, "feed": [enrich(v, viewer) for v in ranked]})
        if path == "/feed/following":
            if not viewer:
                return self._send(400, {"ok": False, "error": "user_required"})
            following = {b for a, b in FOLLOWS if a == viewer}
            rows = [enrich(v, viewer) for v in VIDEOS if v["user_id"] in following]
            return self._send(200, {"ok": True, "feed": rows})
        if path == "/search":
            tag = ((q.get("hashtag") or q.get("q") or [""])[0] or "").lower().lstrip("#")
            rows = [enrich(v, viewer) for v in VIDEOS if tag in v["caption"].lower() or tag in v["hashtags"]]
            return self._send(200, {"ok": True, "results": rows})
        if path.startswith("/users/"):
            handle = path.split("/")[2]
            u = next((x for x in USERS.values() if x["handle"] == handle or x["id"] == handle), None)
            if not u:
                return self._send(404, {"ok": False})
            vids = [enrich(v, viewer) for v in VIDEOS if v["user_id"] == u["id"]]
            return self._send(200, {"ok": True, "user": u, "videos": vids})
        if path.startswith("/videos/") and path.endswith("/comments"):
            vid = path.split("/")[2]
            return self._send(200, {"ok": True, "comments": COMMENTS.get(vid, [])})
        if path.startswith("/videos/"):
            vid = path.split("/")[2]
            v = next((x for x in VIDEOS if x["id"] == vid), None)
            return self._send(200 if v else 404, {"ok": bool(v), "video": enrich(v, viewer) if v else None})
        self._send(404, {"ok": False})

    def do_POST(self):
        path, _ = self.parse()
        body = self._read_json()
        if path == "/videos":
            user = body.get("user_id") or "u1"
            if user not in USERS:
                return self._send(400, {"ok": False, "error": "unknown_user"})
            v = {
                "id": uid("v"), "user_id": user, "caption": body.get("caption") or "",
                "hashtags": body.get("hashtags") or [], "sound": body.get("sound") or "original_audio",
                "duration_sec": int(body.get("duration_sec") or 15),
                "likes": 0, "comments": 0, "shares": 0, "views": 0, "created_at": iso(),
                "media_url": body.get("media_url") or "",
            }
            VIDEOS.insert(0, v)
            return self._send(201, {"ok": True, "video": enrich(v, user)})
        if path.startswith("/videos/") and path.endswith("/like"):
            vid = path.split("/")[2]
            user = body.get("user") or "u1"
            v = next((x for x in VIDEOS if x["id"] == vid), None)
            if not v:
                return self._send(404, {"ok": False})
            key = (user, vid)
            if key not in LIKES:
                LIKES.add(key); v["likes"] += 1
            return self._send(200, {"ok": True, "likes": v["likes"]})
        if path.startswith("/videos/") and path.endswith("/comments"):
            vid = path.split("/")[2]
            c = {"id": uid("c"), "user": body.get("user") or "anon", "text": body.get("text") or "", "at": iso()}
            COMMENTS.setdefault(vid, []).append(c)
            v = next((x for x in VIDEOS if x["id"] == vid), None)
            if v:
                v["comments"] += 1
            return self._send(201, {"ok": True, "comment": c})
        if path.startswith("/videos/") and path.endswith("/share"):
            vid = path.split("/")[2]
            v = next((x for x in VIDEOS if x["id"] == vid), None)
            if v:
                v["shares"] += 1
            return self._send(200, {"ok": True, "shares": v["shares"] if v else 0})
        if path == "/follow":
            a, b = body.get("user"), body.get("target")
            if a not in USERS or b not in USERS:
                return self._send(400, {"ok": False, "error": "unknown_user"})
            FOLLOWS.add((a, b))
            USERS[b]["followers"] += 1
            USERS[a]["following"] += 1
            return self._send(200, {"ok": True, "following": True})
        self._send(404, {"ok": False})

def main():
    serve(H, port=int(__import__("os").environ.get("PORT", "8790")), name="Xerus v2 (TikTok parity)")

if __name__ == "__main__":
    main()
