## Relevant Files

- `common/database_init.py` – Helper housing `initialize_database()` logic and idempotent guard. **(Created)**
- `common/project.py` – Refactor to delegate all DB setup to the new helper.
- `common/db.py` – Keeps Peewee `Proxy` but exposes it via `initialize_database()`.
- `common/main.py` – CLI entry point updated to call `initialize_database()` before most commands.
- `address_bundler/main.py` – Same integration as above.
- `lawn_signs/main.py` – Same integration as above.
- `tests/test_database_init.py` – Unit tests covering success and failure scenarios.
- `README.md` – Updated “Getting Started” section explaining the new initialization flow.

### Notes

- **Unit tests** should reside in the existing `tests/` directory and can be run with `pytest`.
- `initialize_database()` must be safe to call multiple times in the same process.
- The helper should raise a custom `InitializationError` with clear, actionable messages.
- Keep the existing `work on <project>` command behaviour unchanged; it should still create the project and then call `initialize_database()`.

## Tasks

- [x] 1.0 Design `initialize_database()` helper
  - [x] 1.1 Create `common/database_init.py` with a private `_initialized` flag
  - [x] 1.2 Read current project via `get_project()` and locate `.current-project`
  - [x] 1.3 Validate project directory exists and is writable, else raise `InitializationError`
  - [x] 1.4 Build database path (`students.db`) and call `peewee.SqliteDatabase`
  - [x] 1.5 Import `Student` model and create tables (`safe=True`)
  - [x] 1.6 Ensure function is a no-op on subsequent calls in same run

- [ ] 2.0 Refactor project initialization flow  
  - [x] 2.1 Remove direct DB setup from `common/project.initialize_projects()`
  - [x] 2.2 Update `common/project.set_current_project()` to invoke `initialize_database()` after creating the project
  - [x] 2.3 Guarantee no circular import issues by local-importing inside functions

- [x] 3.0 Integrate `initialize_database()` into CLI entry points
  - [x] 3.1 In `common/main.py`, call `initialize_database()` unless handling `work on` command
  - [x] 3.2 Repeat the integration pattern in `address_bundler/main.py`
  - [x] 3.3 Repeat in `lawn_signs/main.py`
  - [x] 3.4 Update CLI help texts to remind users to run `work on <project>` first

- [x] 4.0 Implement robust error handling & validation  
  - [x] 4.1 Define `InitializationError` in `common/database_init.py`  
  - [x] 4.2 Surface friendly CLI messages by catching `InitializationError` in each `main.py`  
  - [x] 4.3 Add validation for invalid project names and unwritable directories  

- [ ] 5.0 Update tests and documentation  
  - [x] 5.1 Write `tests/test_database_init.py` covering success, missing `.current-project`, invalid directory, and idempotency
  - [ ] 5.2 Amend `README.md` with new “First Run” instructions  
  - [ ] 5.3 (Optional) Document the helper in `SPECS/project_summary_mode.md`  
