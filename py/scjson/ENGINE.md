# SCXML-style execution engine with names:

### Layers
What you create when the interpreter starts	Lifetime	Typical contents

Document (global)	Document Context (sometimes “Data Model”)	Entire run	• all top-level <data> elements
• immutable constants
• a pointer to the current Root Activation (see next row)
• event queue / scheduler handle

Root state machine	Root Activation Record	Entire run	• ID of the root <scxml> element
• current configuration (set of active states)
• history snapshots, global timers, etc.
Every state / parallel that becomes active	State 

Activation Record (“local context”, “frame”, etc.)	From onentry to finishing onexit	• reference to parent activation
• runtime flags: isFinal, isParallel, hasHistory …
• any <data> scoped to the state
• temporary variables created by assign/var actions
• running timers raised by this state

## Why this layering works

### Isolation of transient data

A State Activation Record vanishes when the state exits, so any scratch variables or timers don’t leak upward. That matches SCXML’s expectation that local <data> is recreated on each re-entry.

### Hierarchy mirrors control flow

Because activations nest exactly like <state> / <parallel> nesting, algorithms like “is ancestor active?”, history restoration, and final-state detection become simple tree traversals.
Final-state bookkeeping

Mark an activation as final when its <final> child enters; propagate this upward so that a <parallel> completes only when all its children’s activations are in the final state.

### Low-level efficiency
If you implement activations as lightweight objects (or struct handles from an object pool), creating/destroying them on each entry/exit is cheap and keeps per-instance memory proportional to the active configuration, not the whole chart.

### A couple of implementation hints
Keep a “current configuration” set alongside the activation tree; most algorithms (microstep, legal transitions, conflict resolution) are set operations over the configuration.

Event queues live at the document or root level. Deliver events downward by walking the activation tree until someone consumes them.

History: store, on exit, the IDs (or pointers) of the child activations that were active. On history restore, recreate activations for those IDs instead of evaluating <initial>.

Global vs. local data: let state-level <data> shadow document-level entries; look-ups walk up the activation chain.
