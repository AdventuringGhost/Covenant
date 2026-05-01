package covenant.authz

default allow := false

allow if {
    input.role == "admin"
}

allow if {
    input.role == "user"
    input.action == "query"
    input.classification in {"public", "internal"}
}

allow if {
    input.role == "auditor"
    input.action == "read_logs"
}
