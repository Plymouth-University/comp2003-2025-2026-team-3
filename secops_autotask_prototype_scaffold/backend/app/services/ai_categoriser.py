"""
MVP AI categoriser (keyword-based).

Toby can replace this file with his NLP/weighting implementation later.
Keep the return shape stable:
{
  "category": str,
  "score": int (0-100),
  "reason": str
}
"""

def categorise_ticket(title: str, description: str) -> dict:
    text = (title + "\n" + description).lower()

    rules = [
        ("Email blocked/held", ["quarantine", "held", "quarantined", "blocked", "phishing", "message held"]),
        ("Backup failed", ["backup failed", "job failed", "snapshot failed", "backup job failed"]),
        ("Backup suspended", ["backup suspended", "suspended/paused", "paused", "policy disabled", "suspended"]),
        ("Hardware offline", ["device offline", "offline", "not responding", "unreachable", "agent offline", "host not responding"]),
        ("Patching vulnerabilities", ["vulnerab", "missing security updates", "critical vulnerabilities", "patch compliance"]),
        ("Patch failed", ["patch install failed", "install failed", "kb", "windows update corruption", "retry patch"]),
    ]

    for category, kws in rules:
        if any(k in text for k in kws):
            score = 90 if category in ["Email blocked/held", "Hardware offline"] else 80
            return {"category": category, "score": score, "reason": f"Matched keywords for '{category}'."}

    return {"category": "Patching vulnerabilities", "score": 50, "reason": "No strong keyword match; defaulted for MVP."}
