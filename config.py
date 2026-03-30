"""
Sanskrati Patel – Job Search Profile & Filter Configuration
Edit this file to change what jobs you want to be notified about.
"""

# ── Candidate Profile ──────────────────────────────────────────────────────────
CANDIDATE = {
    "name": "Sanskrati Patel",
    "email": "patelsanskrati05@gmail.com",
    "whatsapp": "919329496348",
    "experience_years": 1.6,
}

# ── Search Keywords (used across all portals) ──────────────────────────────────
SEARCH_KEYWORDS = [
    "Python Backend Developer",
    "Backend Developer Python",
    "FastAPI Developer",
    "Django Developer",
    "Python Developer",
    "Backend Engineer Python",
    "API Developer Python",
    "Django REST Framework",
]

# ── Location ───────────────────────────────────────────────────────────────────
LOCATIONS = ["Bhopal", "India", "Remote"]  # portals cycle through these

# ── Experience Filter (years) ──────────────────────────────────────────────────
EXP_MIN_YEARS = 0    # accept freshers too
EXP_MAX_YEARS = 2    # max required experience to apply

# ── Salary Filter (LPA = Lakhs Per Annum) ─────────────────────────────────────
SALARY_MIN_LPA = 4.8   # send if minimum offered salary ≥ this value
SALARY_MAX_LPA = None  # no upper cap; set a number if you want one

# ── Skills that must appear (at least one) in the job title / description ──────
REQUIRED_SKILLS_ANY = [
    "python", "fastapi", "django", "backend", "rest api",
    "flask", "api", "postgresql", "mongodb",
]

# ── Roles to exclude (case-insensitive partial match in title) ─────────────────
EXCLUDE_TITLES = [
    "frontend", "react", "angular", "vue", "ios", "android",
    "devops", "data scientist", "machine learning", "ml engineer",
    "qa", "quality assurance", "seo", "sales", "marketing",
    "java backend", "java developer", ".net developer", "ruby", "php developer",
    "node.js", "nodejs", "golang", "go developer", "kotlin", "scala",
    "c# developer", ".net backend", "c++ developer",
    # Seniority-based exclusions (require too much experience)
    "principal", "staff engineer", "engineering manager", "vp of engineering",
    "head of engineering", "director",
]

# ── Title keywords that indicate senior roles (hard exclude if exp > 2 yrs) ────
SENIOR_TITLE_KEYWORDS = ["senior", "sr.", "lead", "architect", "manager", "head", "principal"]

# ── Portals to enable / disable ────────────────────────────────────────────────
ENABLED_PORTALS = {
    "linkedin": True,       # ✅ Working
    "internshala": True,    # ✅ Working
    "shine": True,          # ✅ Working
    "glassdoor": True,      # ✅ New
    "foundit": True,        # ✅ New (formerly Monster India)
    "timesjobs": False,     # ❌ 404 errors
    "wellfound": False,     # ❌ 403 blocked
    "naukri": False,        # ❌ reCAPTCHA at API level – check manually on site
    "indeed": False,        # ❌ RSS feed blocked (429), reCAPTCHA on HTML
}
