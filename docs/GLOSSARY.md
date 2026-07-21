# Project Notes Glossary

This document serves as the Ubiquitous Language and Data Dictionary (Glossary) for the Project Notes feature as mandated by the `BARCAN-TAG-02` Backend API Role Charter.

## Core Terms

- **Note**: A small, user-specific piece of information composed of a title, a body text, and automatically managed created/updated timestamps.
- **User**: An authenticated actor who owns notes and performs operations on them.
- **Owner**: The specific User who created a given Note and has exclusive rights to view, update, or delete it.
- **Idempotency**: The property where subsequent requests return the same state without unintended side-effects (e.g. GET, PUT, DELETE operations).
- **Atomicity**: Transaction boundaries ensuring that API requests either complete fully or leave the data unaltered.
- **Search Query**: An optional text parameter used to filter the list of notes by checking if the title contains the queried string (case-insensitive).
