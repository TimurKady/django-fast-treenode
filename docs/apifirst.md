## API-First Support

### Approach

**The TreeNode Framework** embraces a true **API-First** approach. This means that as soon as you create a model inherited from `TreeNodeModel`, you automatically get a fully functional set of RESTful API endpoints — without writing any serializers, views, routers, or manually configuring anything.

No extra setup. No DRF overhead. No boilerplate code. Just **model ➔ ready-to-use API**, instantly.

What Makes It Special:

- **Zero configuration:** No need for serializers, views, or routers.
- **Uniform structure:** All tree models behave consistently.
- **High performance:** Optimized lazy updates minimize database load.
- **Developer happiness:** Focus on your logic, not boilerplate code.

Create your model. Run the server. Enjoy your instant API.

### How It Works

The framework automatically scans your project for models based on `TreeNodeModel` and dynamically generates API routes.

You do not need to:

- Create view classes
- Write serializers
- Manually register URLs
- Configure routers

As soon as the server starts, all tree-enabled models are discovered and their endpoints are created. This happens through the `AutoTreeAPI` engine built into the framework.

For each `TreeNodeModel`, the following endpoints are available:

| Method   | Endpoint                                | Description |
|:---------|:----------------------------------------|:------------|
| `GET`    | `/api/<model>/?flat=true`               | List all nodes, ordered by tree structure |
| `POST`   | `/api/<model>/`                         | Create a new node |
| `GET`    | `/api/<model>/<id>/`                    | Retrieve a single node |
| `PUT`    | `/api/<model>/<id>/`                    | Replace a node completely |
| `PATCH`  | `/api/<model>/<id>/`                    | Update a node partially |
| `DELETE` | `/api/<model>/<id>/?cascade=true|false` | Delete a node (with or without subtree) |
| `GET`    | `/api/<model>/tree/?flat=true`          | Retrieve the entire tree |
| `GET`    | `/api/<model>/tree/?annotated=true`     | Retrieve the tree with depth [annotations](api.md#get_tree_annotated) |
| `GET`    | `/api/<model>/<id>/children/`           | Retrieve direct children of a node |
| `GET`    | `/api/<model>/<id>/descendants/`        | Retrieve all descendants of a node |
| `GET`    | `/api/<model>/<id>/family/`             | Retrieve the family |

!!! note
    * All API endpoints are automatically generated under the `treenode` namespace (f.e., `treenode/api/<model>/`).
    * `<model>` refers to the lowercased model name (e.g., `category`, `department`, `location`, etc.).

!!! danger "Important Note for Production Environments"
    In production environments, **API endpoints must not remain open**. Always secure your API using [authentication mechanisms](#basic-access-control) or any other appropriate method.

    Leaving APIs open in production exposes your system to unauthorized access, data leaks, and potential security breaches.


---

### Example Usage

Create a node:

```bash
POST treenode/api/category/
{
  "name": "New Node",
  "parent_id": 123,
  "priority": 0
}
```

Retrieve all nodes:

```bash
GET treenode/api/category/
```

Get the tree structure:

```bash
GET treenode/api/category/tree/
```

Move a node:

Simply `PATCH` its `parent_id` and/or `priority` field:

```bash
PATCH treenode/api/category/456/
{
  "parent_id": 789,
  "priority": 1
}
```

Delete a node (with or without descendants):

```bash
DELETE treenode/api/category/456/?cascade=true
```

- `cascade=true` (default): Delete the node and all its descendants.
- `cascade=false`: Move the node's children up before deleting it.

All endpoints use standard JSON format for input and output.

No complicated payloads. No custom formats.  **TreeNode Framework** believes that models should define your API — not the other way around.

---

### Basic Access Control
TreeNode Framework follows an API-First philosophy: API endpoints are generated automatically for each tree model, without the need to manually register views or routes.

However, API protection is currently basic — based on login sessions using Django's standard authentication system (login_required). This is simple but effective for many internal or admin-side applications.

In the future, full token-based authentication (e.g., JWT) will be introduced for more robust and flexible security.

#### How to Secure Your API Step-by-Step
Since TreeNode Framework does not provide an authentication system itself, you need to set up basic login endpoints in your project.

Here’s how you can do it:

**Step 1. Enable login protection**

Either:

  - Set `api_login_required` = True in your tree model, or
  - Set `TREENODE_API_LOGIN_REQUIRED = True` in **settings.py** of your project .

**Step 2. Add login and logout views**

In your **urls.py**, add:

```python
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

This creates standard login and logout endpoints using Django’s built-in authentication system.

**Step 3. Configure your login URL**

In your **settings.py**:

```python
LOGIN_URL = '/accounts/login/'
```

This tells Django where to redirect unauthorized users trying to access protected API endpoints.

!!! note
    Token support (JWT) will be introduced in future releases for full API-level security. Until then, make sure you correctly configure login protection if you are deploying the API to a production environment.

