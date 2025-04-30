## About TreeNode Framework
TreeNode Framework is a lightweight, extensible, and high-performance set of components for working with trees in Django projects. It is designed to build, manage, and publish tree structures with minimal development overhead.

### Approach

In any system that manages hierarchical data, the choice of internal representation is critical to achieving a balance between **performance**, **consistency**, and **development simplicity**.

TreeNode Framework follows the philosophy that no single tree management method is ideal for all tasks. Instead, it embraces a **hybrid approach**, combining multiple classic methods to maximize their strengths while minimizing their weaknesses.

The goal is simple: **fast reads, reliable updates, scalable growth**, and **minimal database load** even when dealing with trees containing tens of thousands of nodes.

---

### History

The original inspiration for this framework came from the outstanding work of **[Fabio Caccamo](https://github.com/fabiocaccamo)**.

Fabio's project, **[django-treenode](https://github.com/fabiocaccamo/django-treenode)**, introduced an elegant concept: using the **Adjacency List** method for tree storage, combined with **precalculated values** and aggressive **query caching**.  
This made read operations extremely fast — often achievable with a single lightweight database call or no call at all, if the cache was warm.

The original application had several undeniable advantages over traditional recursive models:

- Efficient selections without complex recursive queries.
- Smart caching for predictable response times.
- Deep integration with Django ORM.

However, certain architectural trade-offs also became apparent:

- The **precalculation strategy** introduced **heavy overhead** for write operations, particularly when adding new nodes.
- The need to calculate a large amount of data when inserting brings with it large overhead costs. Combined with the reliance on Django signals to maintain the tree, this resulted in **large delays** when inserting nodes.
- **Node ordering inside a parent** was not inherently supported, leading to difficulties when tree branches needed precise internal ordering based on priorities.

In short, the **excellent debut idea** deserved further development to fully realize its potential at scale.

TreeNode Framework was born from this insight — preserving the best aspects of the original while rethinking the internal mechanisms for greater robustness.

---

### Why a Hybrid Approach

After extensive experimentation with different tree models (Adjacency List, Materialized Path, Nested Set, Closure Table), it became clear that **no single method** could meet all practical requirements.

- **Adjacency List** is simple and efficient for single node queries, but recursive traversal is expensive.
- **Materialized Path** allows fast subtree retrieval but complicates updates during node movement.
- **Nested Set** is excellent for entire subtree reads but very costly for inserts and structural changes.
- **Closure Table** is flexible but complex and storage-heavy.

The project was initially built on a combination of **Adjacency List** and **Closing Table**. As testing data shows, the result was worth the development costs. This architecture allowed it to become one of the most productive Django tree packages.

But this approach had a weak point in the form of the need for parallel maintenance of two Django models to implement one tree. Another feature of the **Closure Table** is the fact that the overhead costs of inserting a new node grow with its depth.

Latest implementation of **TreeNode Framework** chose to combine:

- **Adjacency Table** (simple `parent` linkage) for lightweight parent/child management
- **Materialized Path** for efficient sorting, retrieval, and traversal
- **Dynamic caching and task queues** to offload expensive operations

This hybrid model ensures:

- **Fast reads** (entire subtree retrievals in one indexed query)
- **Predictable writes** (insertions and movements with minimal locking)
- **Safe bulk operations** (no reliance on Django signals or ORM events)
- **Flexible extension points** for future scaling.

---

### Architecture Overview

TreeNode Framework's architecture is built around a clear separation of concerns:

| Component        | Responsibility                           |
|:-----------------|:-----------------------------------------|
| **TreeNodeModel** | Base model handling structural fields (`parent_id`, `_path`, `_depth`, `priority`) |
| **SQL Queue (sqlq)** | Defers expensive updates into efficient batch SQL operations |
| **Task Queue (tasks)** | Manages delayed tree maintenance tasks (e.g., path recalculation) |
| **Cache Layer** | Maintains quick access to tree fragments without hitting the database |
| **Admin Extensions** | Provides drag-and-drop and advanced UI functionality for Django Admin |
| **API Generator** | Enables API-First development with automatic endpoint creation for any model |

Each layer has a minimal surface area, designed for maximum composability and customization.

Key Concepts:

- **Deferred Execution**:
  Write-heavy operations (such as bulk inserts) do not immediately trigger costly recalculations. Instead, recalculations are queued and executed efficiently afterward.

- **Materialized Path Rebuilding**:
  When a node is inserted or moved, the system can selectively rebuild only the affected subtree — avoiding full-tree recalculations.

- **Smart SQL**:
  Updates and reconstructions of the tree structure are done through direct SQL rather than slow per-object ORM updates.

- **Queue Safety**:
  The SQL queue (`sqlq`) and Task queue (`tasks`) ensure that tree state remains consistent even under concurrent modifications.

- **Optional Background Execution**:
  Cache queue maintenance has been moved to a background thread, providing increased speed and additional scalability.

- **Extensibility by Design**:
  Developers can extend Admin behavior, customize API responses, or override parts of the TreeNode behavior without touching core logic.

---

### Benchmark Tests

The performance of the **TreeNode Framework** has been validated through tests on large datasets. All operations were performed with minimal response time and high stability even on trees with more than **5,000 nodes**.

#### Test Scenario

The benchmark simulated a real-world task of building and training an ensemble of trees (a "forest") for multi-stage decision-making. It included multiple operations:

- **Node insertion**: creating new nodes, including at specific positions;
- **Get ancestors**: retrieving ancestor nodes as Django objects;
- **Get subtree**: retrieving ordered descendants as Django objects;
- **Get children**: retrieving direct child nodes;
- **Get siblings**: retrieving siblings of a node;
- **Get family**: retrieving the full family (ancestors, node, descendants);
- **Re-reading**: measuring repeated retrieval time;
- **Random read**: accessing random nodes unrelated to structure;
- **Move**: moving subtrees and trees;
- **Delete nodes**: deleting nodes with or without descendants.

The tests covered various tree structures:

- **Node count**: ~2,000 to ~10,000 nodes;
- **Root nodes**: ~10 to ~500 roots;
- **Average children per node**: ~10 to ~120;
- **Nesting depth**: ~50 to ~2,000 levels.

The following were used in the test:

- **MP_Node** (Materialized Path), **AL_Node** (Adjacency List) and **NS_Node** (Nested Set) models from the `django-treebeard` package;
- **MPTT** (Modified Nested Set) model from the `django-mptt` package;
- **FastTreeNode** model (Adjacency List & Closure Table Hybrid) - version 2.1 of the `django-fast-treenode` package;
- **Treenode Framework** model (Adjacency List & Materialized Path Hybrid)- version 3.0 of the `django-fast-treenode` package.

In all cases, only documented methods and ways of using models were used.

**PostgreSQL v.19** was used for all tests.

### Evaluation Metrics

In order to objectively evaluate and compare the performance of tree management packages, three complementary indices are used: I-index, T-index, and S-index.
Together, they provide a well-rounded view of both absolute performance and operational consistency.

**I-index (Idealness Index)**:

- **Purpose**: Measures how close a package is to theoretical ideal performance across different operation types.
- **Calculation**: For each operation type, times are normalized relative to the fastest result (fastest = 1.0). The I-index is the total sum of these normalized scores across all tested operations, divided by the theoretical minimum (which equals the number of operations).

- **Interpretation**: An I-index closer to 100% indicates near-perfect efficiency across all operations; higher values indicate less optimal and more uneven performance.


**T-index (Total Performance Index)**:

- **Purpose**: Captures the overall speed of the package based on total execution time across multiple test runs.
- **Calculation**: The best total execution time is normalized to 100 points. Other packages are scored proportionally based on the ratio of the minimum time to their execution time.
- **Formula**: T-index = 100 × (Fastest Average Total Time / Package Total Time)
- **Interpretation**: A T-index close to 100 indicates the best absolute performance. Lower scores indicate slower total execution. 
 
**S-index (Summed Performance Index)**:

- **Purpose**: Measures operational balance by summing normalized times across all operation types, independent of the absolute runtime.
- **Calculation**: The lowest total sum of normalized operation times is set to 100 points. Other packages are scored proportionally based on the ratio.
- **Formula**: S-index = 100 × (Lowest Normalized Sum / Package Normalized Sum)
- **Interpretation**: A higher S-index reflects better balance and consistently strong performance across different types of operations.

These metrics were chosen for the following reasons:

- **Comprehensive Evaluation**:
  The combination of I-index, T-index, and S-index ensures that both absolute performance (T-index) and operational balance (I-index and S-index) are assessed.

- **Normalized and Fair**:
All scores are normalized relative to the best-performing package, making comparisons fair regardless of raw performance scales.

- **Highlights Trade-offs**:
  Packages that are very fast in one type of operation but weak in others will be penalized in the I-index and S-index, promoting consistent real-world usability.

- **Simple Interpretation**:
  Scores are easy to understand: closer to 1.0 (I-index) or 100 (T- and S-index) means better.

Together, these indices provide a clear and convincing measure of how well a tree management package performs, not just in isolated benchmarks, but in realistic multi-operation scenarios.


#### Benchmark Results

All results were normalized relative to the best observed values. Lower values indicate better performance.

| Model          | MP_Node   | AL_Node    | NS_Node   | MPTT      | Fast<br>TreeNode | Treenode<br>Framework |
|:---------------|:---------:|:----------:|:-------- :|:---------:|:----------------:|:---------------------:|
| Insert         | 3,1       | 🥇1,0     | 4,1       | 🥉2,3     | 6,6             | 🥈1,2                 |
| Ancestors      | 156,9     | 🥇1,0     | 158,3     | 142,0      | 🥉1,8          | 🥈1,2                 |
| Subtree        | 🥉1,3    | 75,2       | 🥇1,0    | 3,94       | 🥈3,9          | 13,3                   |
| Children       | 🥇1,0    | 1,1        | 1,4       | 🥉1,0     | 🥈1,0          | 1,6                    |
| Siblings       | 🥇1,0    | 1,1        | 2,8       | 1,1        | 🥈1,0          | 1,1                   |
| Family         | 314,2     | 10.110,0   | 🥈236,2  | 🥉273,4   | 609,9           | 🥇1,0                 |
| Re-reading     | 338,4     | 8.416,7   | 🥉445,7   | 727,4      | 🥇1,0          | 🥈1,3                 |
| Random         | 253,8     | 1,1        | 274,5     | 🥇1,0     | 🥈1,0          | 🥉1,3                |
| Move           | 🥇1,0     | 23,75     | 🥈1,6     | 🥈1,3    | 268,2           | 7,5                    | 
| Delete         | 42,8      | 🥈3,63    | 🥈1,9     | 4,7       | 27,6            | 🥇1,0                 |
| *Sum*          | *1.113,6* | *18.790,5* | *1.127,5* | *1.158,2* | *922,2*         | *30,1*                 | 
| **I-Index**    | **0,9%**  | **0,1%**   | **0,9%**  | **0,9%**  | **1,1%**        | **33,3%**              |
| *Time (av.)*   | *4,0*     | *51,8*     | *4,7*     | 🥉*3,9*  | 🥈*2,7*         | 🥇*1,0*               |
| *> 250 levels* |     -     |      -     | *1,8*     | *11,6*    | *2,0*           | *1,0*                  |


!!! note "Comments"

    - The time in the table is averaged and normalized.
    - **MP_Node** fails at nesting depths over ~60-70 levels.
    - **AL_Node** becomes unusably slow beyond up ~250 levels.
    - Only **NS_Node**, **FastTreeNode**, and **Treenode Framework** could operate beyond 1,000 levels.
    - **FastTreeNode** crashes at extreme depths above ~1,500 levels due to inefficient caching. 
    - **Treenode Framework** crashes at extreme depths above ~1500 due to the materialized path index size exceeding the limit.
    - At nesting depths above ~1,500 levels, only **NS_Node** survived without system resource exhaustion.

**The Treenode Framework** is not an absolute champion in all disciplines. It is rather a “good athlete” who performs fairly evenly in all disciplines and comes first to the finish line.


#### Final Scores

| Model               | T-index | S-index | I-index | Final<br>Score | Comments |
|:-----------------------|--------:|--------:|:-------:|:-----------:|:---------|
| **MP_Node**            | 29      | 2       | 0.9% |      | Most operations are slow |
| **AL_Node**            | 3       | 0       | 0.1% |              | Generally slow |
| **NS_Node**            | 27      | 2       | 0.9%|  🎗️         | **The "Last Hero" Award** |
| **MPTT**               | 25      | 2       | 0.9% |  🎖️         | **The "Honorable Competitor" Award**<br>**"I Am Legend" Award** |
| **Fast<br>TreeNode**       | 30      | 2    | 1.1% | 🎗️         | Slow insertion and move operations<br>**"It Was a Blast" Award** |
| **Treenode<br>Framework** | 100     | 100    | 33.3%  | 🎖️<br>🚀<br>🧠    | High performance<br>Best balance of API<br>**The "Technical Strategist" Award** |

!!! hint "Key findings"

    - Even at a nesting depth of about **1000 levels**, **Treenode Framework** showed overall performance **23% higher** than NS_Node.
    - According to average data, **Treenode Framework** testing shows **3-fold performance** compared to the legendary **MPTT** package.
    - On most tasks with a nesting depth limited to 250 levels, **Treenode Framework** shows performance **up to 4-5 times higher** than other packages.

Thus, at the moment, **Treenode Framework** is the best architectural solution with a near industrial-grade API framework.

#### Conclusion

**Treenode Framework** demonstrates **linear scalability** with increasing tree size.

Basic operations remain fast and predictable even on very large trees, making the framework fully production-ready for high-load systems.

**Treenode Framework** is a pragmatic evolution of tree data management under Django:

- It combines the best theoretical models and practical techniques;
- It provides clean, efficient, and scalable solutions;
- It remains fully aligned with Django's philosophy of simplicity and elegance.

Whether you are building a product catalog, an organizational chart, or a complex hierarchical system, **Treenode Framework** offers a robust, future-proof foundation.


