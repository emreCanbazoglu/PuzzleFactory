Convert Concept Cards into buildable Prototype Specs.

Goals:

- Remove ambiguity
- Define exact rules
- Limit scope to MVP prototype
- Ensure playability with minimal UI

Use Prototype Spec template.

Rules:

- Replace abstract words with explicit rule statements.
- If the concept says `manage pressure`, state the exact resource or board condition under pressure.
- If the concept says `clear the board`, state what counts as cleared.
- Prototype spec must be detailed enough that a builder can implement it without guessing hidden rules.

Required approach:

1. Define the board size and object set.
2. Define the player input.
3. Define state transitions after one input.
4. Define win and lose conditions in code-like language.
5. Define what Level 1 teaches and what Level 2 adds.
