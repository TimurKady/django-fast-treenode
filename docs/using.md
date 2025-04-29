## Using the TreeNode Framework API

The **Treetode Framework**  is built for high efficiency. But to unlock its full potential, you need to think like an engineer, not just a coder.  Working in logical blocks rather than isolated actions ensures maximum performance and minimal database load.

**Quick Strategy**: First INSET or MOVE everything that needs to be → then READ

#### Work in Logical Blocks

Try to group related operations into blocks instead of interleaving reads and writes.

For example:

- Insert multiple nodes **first**, then **read** from the tree.
- Perform a series of moves **first**, then **query** the updated structure.

Since the framework uses a lazy update mechanism, reading from the tree automatically triggers all pending updates through the internal task optimizer.  

This means you **pay the update cost only once**, rather than after every operation.

#### Insert Nodes in Batches

When adding many nodes:

- Create and save them sequentially.
- Avoid reading from the tree between inserts unless necessary.
- After all insertions, perform a single read (e.g., fetching children or descendants).

This allows the framework to optimize and execute updates in a single efficient batch.

#### Move Nodes Before Reading

When reorganizing the tree:

- Perform all move operations first.
- Then trigger any read operation like `cls.objects.filter()`, `get_ancestors()`, etc.

Reading will automatically apply and optimize all pending changes in one pass.

#### Trust the Task Optimizer

The internal task optimizer automatically:

- Merges compatible operations.
- Reorders tasks when possible for minimal SQL load.
- Skips redundant updates if no real changes occurred.

There is no need to manually *"flush"* or *"commit"* tasks — reading from the tree will handle everything automatically.

Following these practices will ensure:

- Maximum speed when building or reorganizing large trees.
- Minimal database overhead.
- Smooth and predictable performance, even with tens of thousands of nodes.

Use the framework's lazy update design to your advantage — **think in terms of blocks, not individual operations.**