## Roadmap

### Last Update
The latest version provides optimized database operations, an improved caching mechanism, and enhanced integration capabilities, making it a **robust and efficient choice** for handling tree structures.

**Version 2.1 – Compatibility and Optimization**
Reducing dependencies and simplifying migration from other libraries.

- **Expanding functionality** to simplify migration from other tree packages.
- Introducing node **filtering and search with AJAX**.
- **Optimizing query performance** by reducing query complexity and improving indexing strategies.
- **Reducing database load** from the `TreeNodeAdmin` when working with large trees.
- Removing `numpy` in favor of lighter alternatives.
- Removing `Select2` in favor of light custom select2-like implementation.


### Planned Roadmap for Future Versions
The **django-fast-treenode** package will continue to evolve from its original concept—combining the benefits of the **Adjacency List** and **Closure Table** models—into a high-performance solution for managing and visualizing hierarchical data in Django projects. The focus is on **speed, usability, and flexibility**.

#### Version 2.2 – Performance Enhancements
Focusing on optimizing query efficiency, reducing database load, and improving API interactions.

- **Optimized Query Execution**: Minimize query overhead by restructuring SQL operations, reducing redundant lookups, and introducing batched operations for bulk inserts.
- **API-First CRUD Implementation**: Introduce full Create, Read, Update, and Delete (CRUD) operations for tree structures, ensuring seamless API-based interaction with hierarchical data.
- **Efficient Serialization**: Develop a lightweight tree serialization format optimized for API responses, reducing payload size while preserving structural integrity.
- **Advanced Node Filtering & Search**: Implement AJAX-based filtering and search mechanisms in Django Admin and API endpoints to enhance usability and response time.

#### Version 2.3 – Drag-and-Drop and Admin UI Improvements
Improving the usability and management of hierarchical structures in Django Admin.

- **Drag-and-Drop Node Reordering**: Introduce interactive drag-and-drop functionality for reordering nodes within the tree structure directly in Django Admin.
- **Hierarchical Sorting Strategies**: Enable various sorting methods, including manual ordering, weight-based prioritization, and hybrid approaches that combine automatic and manual sorting.
- **Admin Panel Enhancements**: Expand Django Admin capabilities for tree structures, including better visualization, inline node editing, and bulk actions.

#### Version 3.0 – Third-Generation Cache Management System
Introducing a more advanced caching system to improve scalability and efficiency.

- **Two-Level FIFO/LRU Cache**: Implement a hybrid caching mechanism combining First-In-First-Out (FIFO) and Least Recently Used (LRU) strategies to optimize cache retention for tree nodes.
- **Multi-Process Cache Synchronization**: Ensure cache consistency across different execution environments (WSGI, Gunicorn, Uvicorn) with a distributed synchronization mechanism.
- **Background Synchronization**: Introduce delayed closure table updates via Celery or RQ, preventing blocking operations while maintaining data consistency.

#### Version 4.0 – Asynchronous Operations
Refactoring the package to support fully asynchronous operations for non-blocking execution.

- **Asynchronous API Execution**: Convert existing synchronous operations to asynchronous, leveraging `async/await` for improved performance.
- **Async Database Support**: Implement async-friendly database operations compatible with Django’s evolving asynchronous ORM.
- **Optimized Tree Node Caching**: Shift from caching precomputed query results to caching raw tree nodes, reducing recomputation overhead and improving retrieval speed.
- **Asynchronous Testing**: Expand the test suite to cover async behavior and the new caching mechanism under concurrent loads.
- **Documentation Update**: Revise and expand documentation to reflect changes in the asynchronous execution model and best practices for implementation.

#### Version 5.0 – Beyond Django ORM
Decoupling tree structure management from Django’s ORM to increase flexibility and adaptability.

- **Multi-Backend Storage Support**: Introduce support for alternative storage engines beyond Django ORM, such as SQLAlchemy, custom PostgreSQL functions, and other database frameworks.
- **Redis Integration for In-Memory Trees**: Implement an optional Redis-based tree storage system, allowing high-speed in-memory hierarchy operations.
- **JSON-Based Storage Option**: Enable lightweight embedded tree storage using JSON structures, facilitating easier use in API-driven and microservice architectures.
- **ORM-Agnostic API Layer**: Design an API-first approach that allows tree structures to function independently from Django models, making the package usable in broader contexts.

So, each milestone is designed to improve performance, scalability, and flexibility, ensuring that the package remains relevant for modern web applications, API-driven architectures, and high-performance data processing environments support.

Stay tuned for updates!

Your wishes, objections, and comments are welcome.
