from __future__ import annotations

# Grad Session Urls
GRAD_SESSIONS_LIST = '/sessions'
GRAD_SESSIONS_UPLOAD_EXCEL = '/sessions/upload'
GRAD_SESSION_RETRIEVE = "/sessions/{sid:int}"
GRAD_SESSION_DELETE = "/sessions/{sid:int}"

# Grad Session Student Urls
GRAD_SESSION_ENTRY_LIST = "/sessions/{sid:int}/students"

# Professor Urls
SESSION_PROFESSOR_LIST = "/sessions/{sid:int}/professors"
SESSION_PROFESSOR_UPDATE = "/sessions/{sid:int}/professors/{session_professor_id:int}"
SESSION_PROFESSOR_SPLIT = "/sessions/{session_id:int}/professors/{session_professor_id:int}/split"
SESSION_PROFESSOR_SUBSTITUTE = "/sessions/{session_id:int}/professors/{session_professor_id:int}/substitute/{substitute_sesssion_professor_id:int}"
PROFESSOR_UPDATE = "/professors"

# Optimization Configurations Urls
GRAD_SESSION_OPT_CONF_NEW = "/sessions/{sid:int}/configuration/new"
GRAD_SESSION_OPT_CONF_UPDATE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_DELETE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_GET_COMPLETE = "/sessions/{sid:int}/configuration/{cid:int}"
GRAD_SESSION_OPT_CONF_LIST = "/sessions/{sid:int}/configuration/"
GRAD_SESSION_OPT_CONF_SOLVE = "/sessions/{session_id:int}/configuration/{config_id:int}/solve"
