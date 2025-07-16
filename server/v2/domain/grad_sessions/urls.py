from __future__ import annotations

# Grad Session Urls
GRAD_SESSIONS_LIST = '/sessions'
GRAD_SESSIONS_UPLOAD_EXCEL = '/sessions/upload'
GRAD_SESSION_RETRIEVE = "/sessions/{sid:int}"
GRAD_SESSION_DELETE = "/sessions/{sid:int}"

# Grad Session Student Urls
GRAD_SESSION_ENTRY_LIST = "/sessions/{sid:int}/students"

# Professor Urls
GRAD_SESSION_PROFESSOR_LIST = "/sessions/{sid:int}/professors"
GRAD_SESSION_PROFESSOR_UPDATE = "/professors"

# Professor Availabilities Urls
GRAD_SESSION_PROF_AVAILABILITY_LIST = "/sessions/{sid:int}/availabilities"
GRAD_SESSION_PROF_AVAILABILITY_UPDATE = "/sessions/{sid:int}/availabilities"

# Optimization Configurations Urls
GRAD_SESSION_OPT_CONF_NEW = "/sessions/{sid:int}/configuration/new"
GRAD_SESSION_OPT_CONF_UPDATE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_DELETE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_GET_COMPLETE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_LIST = "/sessions/{sid:int}/configuration/"
