from django.db import models
from treenode.models import TreeNodeModel


class TestModel(TreeNodeModel):
    """Test model for checking the operation of TreeNode."""

    name = models.CharField(max_length=255, unique=True)
    treenode_display_field = "name"

    class Meta:
        verbose_name = "TestModel"


