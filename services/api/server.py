from __future__ import annotations
"""Xerus v3 — TikTok gaps + boost/creator undercut monetization."""
import sys, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_util import JsonAPI, serve, uid, iso
import payments as pay
import auth as authmod

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
COMMENTS, FOLLOWS, LIKES, LIVES, GIFTS = {}, set(), set(), {}, []

def enrich(v, viewer=None):
    return {**v, "author": USERS.get(v["user_id"], {}), "liked_by_me": (viewer, v["id"]) in LIKES if viewer else False}

class H(JsonAPI):
    def do_GET(self):
        _path_early = (self.path.split("?")[0].rstrip("/") or "/")
        if _path_early.startswith("/auth"):
            hdrs = {k: v for k, v in self.headers.items()}
            code, body = authmod.handle_auth_request("GET", _path_early, {}, hdrs, product="xerus")
            return self._send(code, body)
        path, q = self.parse()
        if path in ("/", "/health"):
            return self._send(200, {"ok": True, "service": "xerus", "version": "3.0.0",
                "gaps_closed": ["boosts", "live", "gifts", "creator_plan", "stripe", "signup", "login", "otp", "oauth_google", "oauth_facebook"]})
        if path == "/capabilities":
            return self._send(200, {"ok": True, "competitor": "TikTok",
                "features": ["for_you","following","upload","like","comment","follow","boost","live","gifts","creator_billing","stripe"]})
        if path == "/pricing": return self._send(200, {"ok": True, **pay.pricing_for("xerus")})
        if path == "/payments/rails": return self._send(200, {"ok": True, "rails": pay.list_rails()})
        if path == "/gap-analysis":
            return self._send(200, {"ok": True, "added": ["boosts $1.49 vs ~$5", "live+gifts 15% fee vs ~50%", "creator $2.99 vs ~$9.99"]})
        viewer = (q.get("user") or [None])[0]
        if path in ("/feed", "/feed/for-you"):
            ranked = sorted(VIDEOS, key=lambda v: v["likes"]*2 + v["views"]*0.01 + random.random(), reverse=True)
            return self._send(200, {"ok": True, "feed": [enrich(v, viewer) for v in ranked]})
        if path == "/feed/following":
            if not viewer: return self._send(400, {"ok": False, "error": "user_required"})
            following = {b for a,b in FOLLOWS if a==viewer}
            return self._send(200, {"ok": True, "feed": [enrich(v, viewer) for v in VIDEOS if v["user_id"] in following]})
        if path == "/search":
            tag = ((q.get("hashtag") or q.get("q") or [""])[0] or "").lower().lstrip("#")
            return self._send(200, {"ok": True, "results": [enrich(v, viewer) for v in VIDEOS if tag in v["caption"].lower() or tag in v["hashtags"]]})
        if path == "/live": return self._send(200, {"ok": True, "lives": list(LIVES.values())})
        if path.startswith("/users/"):
            handle = path.split("/")[2]
            u = next((x for x in USERS.values() if x["handle"]==handle or x["id"]==handle), None)
            if not u: return self._send(404, {"ok": False})
            return self._send(200, {"ok": True, "user": u, "videos": [enrich(v, viewer) for v in VIDEOS if v["user_id"]==u["id"]]})
        if path.startswith("/videos/") and path.endswith("/comments"):
            return self._send(200, {"ok": True, "comments": COMMENTS.get(path.split("/")[2], [])})
        self._send(404, {"ok": False})

    def do_POST(self):
        _path_early = (self.path.split("?")[0].rstrip("/") or "/")
        if _path_early.startswith("/auth"):
            hdrs = {k: v for k, v in self.headers.items()}
            body = self._read_json() if hasattr(self, "_read_json") else self._read()
            code, resp = authmod.handle_auth_request("POST", _path_early, body if isinstance(body, dict) else {}, hdrs, product="xerus")
            return self._send(code, resp)
        path, _ = self.parse()
        body = self._read_json()
        if path == "/videos":
            user = body.get("user_id") or "u1"
            if user not in USERS: return self._send(400, {"ok": False})
            v = {"id": uid("v"), "user_id": user, "caption": body.get("caption") or "", "hashtags": body.get("hashtags") or [],
                 "sound": body.get("sound") or "original_audio", "duration_sec": int(body.get("duration_sec") or 15),
                 "likes": 0, "comments": 0, "shares": 0, "views": 0, "created_at": iso(), "media_url": body.get("media_url") or ""}
            VIDEOS.insert(0, v); return self._send(201, {"ok": True, "video": enrich(v, user)})
        if path.startswith("/videos/") and path.endswith("/like"):
            vid = path.split("/")[2]; user = body.get("user") or "u1"
            v = next((x for x in VIDEOS if x["id"]==vid), None)
            if not v: return self._send(404, {"ok": False})
            if (user, vid) not in LIKES: LIKES.add((user, vid)); v["likes"] += 1
            return self._send(200, {"ok": True, "likes": v["likes"]})
        if path.startswith("/videos/") and path.endswith("/boost"):
            vid = path.split("/")[2]
            inv = pay.create_invoice("xerus", 0, "USD", method=body.get("method") or "stripe", sku="boost_1k", customer=body.get("user") or "u1")
            v = next((x for x in VIDEOS if x["id"]==vid), None)
            if v: v["views"] += 1000
            return self._send(201, {"ok": True, "boosted": vid, "invoice": inv, "note": "$1.49 boost vs ~$5"})
        if path.startswith("/videos/") and path.endswith("/comments"):
            vid = path.split("/")[2]
            c = {"id": uid("c"), "user": body.get("user") or "anon", "text": body.get("text") or "", "at": iso()}
            COMMENTS.setdefault(vid, []).append(c)
            v = next((x for x in VIDEOS if x["id"]==vid), None)
            if v: v["comments"] += 1
            return self._send(201, {"ok": True, "comment": c})
        if path == "/follow":
            a, b = body.get("user"), body.get("target")
            if a not in USERS or b not in USERS: return self._send(400, {"ok": False})
            FOLLOWS.add((a, b)); USERS[b]["followers"] += 1; USERS[a]["following"] += 1
            return self._send(200, {"ok": True})
        if path == "/live/start":
            lid = uid("live")
            LIVES[lid] = {"id": lid, "user_id": body.get("user_id") or "u1", "title": body.get("title") or "Live", "viewers": 0, "at": iso()}
            return self._send(201, {"ok": True, "live": LIVES[lid]})
        if path == "/live/gift":
            amount = float(body.get("amount_usd") or 1)
            fee = round(amount * 0.15, 2)  # 15% vs ~50%
            inv = pay.create_invoice("xerus", amount, "USD", method=body.get("method") or "stripe", customer=body.get("from") or "u1", description="Live gift")
            g = {"id": uid("g"), "to": body.get("to"), "amount_usd": amount, "platform_fee_usd": fee, "creator_net_usd": round(amount-fee, 2), "invoice": inv, "at": iso()}
            GIFTS.append(g)
            return self._send(201, {"ok": True, "gift": g, "note": "15% fee vs ~50% on major apps"})
        if path == "/creator/subscribe":
            inv = pay.create_invoice("xerus", 0, "USD", method=body.get("method") or "stripe", sku="creator", customer=body.get("user") or "u1")
            return self._send(201, {"ok": True, "invoice": inv})
        if path == "/payments/create":
            inv = pay.create_invoice("xerus", float(body.get("amount") or 0), body.get("currency") or "USD",
                method=body.get("method") or "stripe", sku=body.get("sku"))
            return self._send(201, {"ok": True, "invoice": inv})
        self._send(404, {"ok": False})

def main():
    serve(H, port=int(__import__("os").environ.get("PORT", "8790")), name="Xerus v3")
if __name__ == "__main__":
    main()
