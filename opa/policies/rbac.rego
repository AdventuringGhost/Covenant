# RBAC policy: admin allows all actions, user allows query on non-restricted docs, auditor allows logs only

package covenant.authz

import future.keywords.if
import future.keywords.in

default allow := false

# Admins can do anything
allow if {
    input.role == "admin"
}

# Users can query documents at or below their clearance
allow if {
    input.role == "user"
    input.action == "query"
    input.classification in {"public", "internal"}
}

# Auditors can only read audit logs
allow if {
    input.role == "auditor"
    input.action == "read_logs"
}
