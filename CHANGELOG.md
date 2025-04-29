# Changelog

## [3.0.0] – 2025-04-29

### Major update
- Complete refactoring of the package architecture with division into submodules (views, utils, managers, models, admin).
- Removed deprecated approaches (closure), replaced with a single model with path-based and priority-based logic.
- Introduced automatic tree integrity check: `check_tree_integrity()`.
- Expanded serialization capabilities: `get_tree()`, `get_tree_json()`, `load_tree_json()`, `load_tree()`.
- Support for new interfaces for import/export, autocomplete, CRUD and search.
- Added Django-compatible `unittest` tests for automatic CI/CD checking.

### Added
- `treenode/admin/{exporter, importer, mixin}.py` — new modules for extended work in the admin panel.
- `treenode/models/models.py` — new main container of the tree model.
- `treenode/utils/db/` — new subsystem for low-level SQL logic and compatibility with various DBMS.
- `treenode/views/*` — modular structure of views (autocomplete, search, api).
- `treenode/settings.py` — default configuration with customization support.
- New system of decorators, factories and updates (e.g. `models/decorators.py`, `models/mixins/update.py`).
- `tests.py` file with unit tests.

### Removed
- `closure.py`, `adjacency.py`, `base36.py`, `base16.py`, `radix.py` — deprecated storage and encoding schemes.
- `treenode/views.py` — monolithic view replaced with modular structure.
- Temporary or deprecated modules: `utils/aid.py`, `utils/db.py`, `utils/importer.py`, `classproperty.py`.

### Changed
- Refactoring of almost all mixins (`ancestors`, `descendants`, `siblings`, `roots`, `properties`, `logical`, etc.).
- Rewritten `admin.py`, `changelist.py`, `cache.py`, `widgets.py`, `factory.py` and others.
- Improved compatibility with Django 4/5, performance, readability and code extensibility.
- Improved logic of `version.py`, `urls.py`, added type annotations and documentation.

### Requirements
- Python ≥ 3.9
- Django ≥ 4.0
- msgpack>=1.0.0
- openpyxl>=3.0.0
- pyyaml>=5.1