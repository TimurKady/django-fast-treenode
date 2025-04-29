## Import&Export Functionality
### Overview

**The Treenode Framework** includes **built-in export and import features** for easier data migration. Supported Formats: `csv`, `json`, `xlsx`, `yaml` and `tsv`. The system supports importing and exporting data for any models, allowing users to efficiently manage and update data while preserving its structure and relationships.

### Data Processing Logic
When importing data into the system, **two key fields** must be present:

- **`id`** – the unique identifier of the record.
- **`parent`** – the identifier of the parent node.

It is also desirable to have a **`priority`** field in the import file, which specifies the ordinal number of the node among the descendants of its parent. It is recommended to explicitly assign a `priority` value to each node during import.  

If no `priority` is provided, the system will automatically assign it based on the `sorting_field` setting. If `sorting_field` is set to `priority`, the final ordering of nodes may not be strictly predictable and will generally follow the order of nodes as they appear in the import file.

These fields ensure the correct construction of the hierarchical data structure.

!!! important
    Starting from Django 5.0, it is no longer allowed to create model instances with a manually specified value for an `id` field of type `AutoField`.  
    As a result, during import operations:

    - If the specified `id` exists in the database, the record **will be updated**.
    - If the specified `id` does not exist, a new record will be created, but it **will be assigned a different (auto-generated) `id`**.

    Don't forget to thank the developers for this very useful improvement and for caring about us when you visit the Django community

This import mechanism is designed to allow users to:

- **Export data**, edit it (e.g., in a CSV, Excel, or JSON file).
- **Upload the modified file** without disrupting the model structure.
- **Update only the changed data**, keeping relationships with other models intact (e.g., without altering primary and foreign key values).

This approach provides **flexible data management**, enabling users to safely apply modifications without manually updating each record in the system.

!!! important
    Exporting objects with M2M fields may lead to serialization issues. 
    Some formats (e.g., CSV) do not natively support many-to-many relationships. If you encounter errors, consider exporting data in `json` or `yaml` format, which better handle nested structures.
