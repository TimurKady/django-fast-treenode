## Roadmap

The **`django-fast-treenode`** package will continue to evolve from its original concept—combining the benefits of the hybrid models into a high-performance solution for managing and visualizing hierarchical data in Django projects. 

The focus is on **speed, usability, and flexibility**.

#### Roadmap for 3.x Series

The 3.x release series will focus on strengthening TreeNode Framework in terms of security, usability, and performance scalability, while maintaining backward compatibility and architectural cleanliness.


* **Version 3.1 — JWT Authentication for API**

    - Introduce optional JWT-based token authentication for the auto-generated API.
    - Allow easy activation through a single setting (`TREENODE_API_USE_JWT = True`).
    - Preserve backward compatibility: API remains open unless explicitly protected.
    - Foundation for future security features (e.g., user-specific trees, audit trails).

* **Version 3.2 — Admin Usability Improvements**

    Focus: enhance operational safety and optimize workflows for large-scale trees.

    - **Safe Import Preview**: Implement a staging layer for imports, allowing users to review and confirm imported data before committing changes.

    - **Incremental Export**: Support selective export of nodes modified after a specified date or revision marker.

  
* **Version 3.3 — Soft Deletion Support**

    Focus: improve real-world resilience without sacrificing performance.

    - Add optional support for "soft delete" behavior (`is_deleted` field).
    - Modify core queries and cache invalidation logic to respect soft-deleted nodes.
    - Add a new task type to the internal task queue system for bulk logical deletions.
  
* **Version 3.4 — Cache System Enhancements**

    Focus: lay the foundation for scaling Treenode Framework to extreme node counts (>100,000 nodes).

    - General improvements to the in-memory cache system.
    - Research and implement better object size tracking for memory management.
    - Explore disk-based, Redis-based, or hybrid caching strategies for massive trees.

Each step in the 3.x roadmap is intended to strengthen the framework's key principles: **security, usability, scalability, simplicity**.

#### Long-Term Vision


* **Version 4.0 – Improved architecture**

    The main debut idea of ​​version 4.0 is to further develop the hybrid approach. This version will implement a new new architectural solution that is designed to increase the speed of selecting descendants, and therefore moving subtrees, and remove the existing restrictions on the maximum nesting depth of the tree (currently the recommended value when using up to 1000 levels).

    - Speed ​​up the operation of extracting descendants.
    - Speeding up operations for moving large subtrees.
    - Performance optimization when working with trees that have extreme depth (more than 2000 levels).

* **Version 5.0 – Beyond Django ORM**

    Decoupling tree structure management from Django’s ORM to increase flexibility and adaptability.

    - **Multi-Backend Storage Support**: Introduce support for alternative storage engines beyond Django ORM, such as SQLAlchemy, custom PostgreSQL functions, and other database frameworks.
    - **Redis Integration for In-Memory Trees**: Implement an optional Redis-based tree storage system, allowing high-speed in-memory hierarchy operations.
    - **JSON-Based Storage Option**: Enable lightweight embedded tree storage using JSON structures, facilitating easier use in API-driven and microservice architectures.
    - **ORM-Agnostic API Layer**: Design an API-first approach that allows tree structures to function independently from Django models, making the package usable in broader contexts.

So, each milestone is designed to improve performance, scalability, and flexibility, ensuring that the package remains relevant for modern web applications, API-driven architectures, and high-performance data processing environments support.

Stay tuned for updates!

Your wishes, objections, and comments are welcome.