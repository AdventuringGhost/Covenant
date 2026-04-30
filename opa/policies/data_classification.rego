# Data classification policy: maps document sensitivity levels to the minimum role required to access them

package covenant.classification

import future.keywords.if

# Classification hierarchy: public < internal < confidential < restricted
minimum_role := "user" if { input.classification == "public" }
minimum_role := "user" if { input.classification == "internal" }
minimum_role := "admin" if { input.classification == "confidential" }
minimum_role := "admin" if { input.classification == "restricted" }

# Auditors never access document content regardless of classification
visible if {
    input.role != "auditor"
    minimum_role == input.role
}

visible if {
    input.role == "admin"
}
