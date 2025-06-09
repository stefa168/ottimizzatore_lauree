from __future__ import annotations

# Grad Session Urls
GRAD_SESSIONS_LIST = '/sessions'
GRAD_SESSIONS_UPLOAD_EXCEL = '/sessions/upload'
GRAD_SESSION_RETRIEVE = "/sessions/{sid:int}"

# Grad Session Student Urls
GRAD_SESSION_ENTRY_LIST = "/sessions/{sid:int}/students"

# Professor Availabilities Urls
GRAD_SESSION_PROF_AVAILABILITY_LIST = "/sessions/{sid:int}/availabilities"
GRAD_SESSION_PROF_AVAILABILITY_CREATE = "/sessions/{sid:int}/availabilities"
 