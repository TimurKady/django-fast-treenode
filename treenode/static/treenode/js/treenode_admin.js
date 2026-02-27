/**
 * treenode_admin.js
 *
 * Cleaned version 3.1.1 — TreeNode Admin extension for Django Admin.
 * - No AJAX loading of children
 * - Defensive persistence in localStorage (state is restored only for the same tree snapshot)
 * - Local-only expand/collapse logic
 * - Compatible with pre-rendered full tree
 *
 * Version: 3.1.0
 * Author: Timur Kady
 * Email: timurkady@yandex.com
 */

(function($) {

  // ------------------------------- //
  // Helpers                        //
  // ------------------------------- //

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // ------------------------------- //
  // AJAX Setup                     //
  // ------------------------------- //

  const csrftoken = getCookie('csrftoken');

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!/^https?:.*/.test(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
      $('body').css('cursor', 'wait');
    },
    complete: function() {
      $('body').css('cursor', 'default');
    },
    cache: false
  });

  // ------------------------------- //
  // Visual feedback                 //
  // ------------------------------- //

  const TreeFx = {
    flashInsert(nodeId) {
      const $row = $(`tr[data-node-id="${nodeId}"]`);
      if (!$row.length) return;

      $row.addClass("flash-insert");
      setTimeout(() => $row.removeClass("flash-insert"), 1000);
    },

    markDragging($item, enable) {
      $item.toggleClass('dragging', enable);
    }
  };

  // ------------------------------- //
  // Tree logic                      //
  // ------------------------------- //

  var ChangeList = {
    $tableBody: null,
    dropContext: null,
    isMoving: false,
    storageKey: "treenode_expanded",

    init: function() {
      this.$tableBody = $('table#result_list tbody');
      this.configureStorageKey();
      this.bindEvents();
      this.enableDragAndDrop();
    },

    configureStorageKey: function() {
      const explicitLabel = $("#changelist").data("model-label");
      const fallbackLabel = $("body").data("app-label") || "default";
      const label = explicitLabel || fallbackLabel;
      this.storageKey = `treenode_expanded:${label}`;
    },

    getTreeSignature: function() {
      if (!this.$tableBody) {
        return "";
      }

      return this.$tableBody.find("tr").map(function() {
        const $row = $(this);
        const nodeId = $row.data("node-id") || "";
        const parentId = $row.data("parent-id") || "";
        return `${nodeId}:${parentId}`;
      }).get().join("|");
    },
    
    // Save expanded nodes to localStorage
    saveTree: function() {
      if (!this.$tableBody) return;
    
      // Сохраняем ТОЛЬКО те node_id, которые раскрыты
      this.expandedNodes = this.$tableBody.find(".treenode-toggle").map(function() {
        const $btn = $(this);
        return $btn.data("expanded") ? $btn.data("node-id") : null;
      }).get().filter(Boolean);
    
      if (this.expandedNodes.length === 0) {
        localStorage.removeItem(this.storageKey);
      } else {
        localStorage.setItem(this.storageKey, JSON.stringify({
          signature: this.getTreeSignature(),
          expandedNodes: this.expandedNodes,
        }));
      }
    
      const count = $("#result_list tbody tr").length;
      if (count > 0) {
        $("p.paginator").first().text(`${count} ${ChangeList.label}`);
        localStorage.setItem("label", ChangeList.label);
      }
    },

    
    // Restore expanded nodes from localStorage
    restoreTreeState: function() {
      const raw = localStorage.getItem(this.storageKey);
      if (!raw) {
        return;
      }

      let payload;
      try {
        payload = JSON.parse(raw);
      } catch (error) {
        localStorage.removeItem(this.storageKey);
        return;
      }

      if (!payload || payload.signature !== this.getTreeSignature()) {
        localStorage.removeItem(this.storageKey);
        return;
      }

      const expanded = Array.isArray(payload.expandedNodes) ? payload.expandedNodes : [];
      for (const nodeId of expanded) {
        ChangeList.expandNode(nodeId);
      }
    },

    expandNode: function(nodeId) {
      const $row = this.$tableBody.find(`tr[data-node-id="${nodeId}"]`);
      const $btn = $row.find(".treenode-toggle");
      $btn.text("▼").data("expanded", true);
      this.showChildren(nodeId);
      this.saveTree();
    },

    collapseNode: function(nodeId) {
      const $row = this.$tableBody.find(`tr[data-node-id="${nodeId}"]`);
      const $btn = $row.find(".treenode-toggle");
      $btn.text("►").data("expanded", false);  // <-- ВАЖНО!
      this.hideChildrenRecursive(nodeId);
      this.saveTree();
    },

    toggleNode: function($btn) {
      const nodeId = $btn.data("node-id");
      const isExpanded = $btn.data("expanded");
      if (isExpanded) {
        this.collapseNode(nodeId);
      } else {
        this.expandNode(nodeId);
      }
    },

    showChildren: function(parentId) {
      const $children = this.$tableBody.find(`tr[data-parent-id="${parentId}"]`);
      $children.removeClass("treenode-hidden");

      $children.each((_, child) => {
        const $child = $(child);
        const childId = $child.data("node-id");
        const $toggle = $child.find(".treenode-toggle");
        if ($toggle.data("expanded")) {
          this.showChildren(childId);
        }
      });
    },

    hideChildrenRecursive: function(parentId) {
      const $children = this.$tableBody.find(`tr[data-parent-id="${parentId}"]`);
      $children.addClass("treenode-hidden");

      $children.each((_, child) => {
        const childId = $(child).data("node-id");
        this.hideChildrenRecursive(childId);
      });
    },

    expandAll: function() {
      const self = this;
      this.$tableBody.find("button.treenode-toggle").each(function() {
        self.expandNode($(this).data("node-id"));
      });
    },

    collapseAll: function() {
      const self = this;
      this.$tableBody.find("button.treenode-toggle").each(function() {
        self.collapseNode($(this).data("node-id"));
      });
    },

    bindEvents: function() {
      const self = this;

      $(document).on("click", "button.treenode-toggle", function(e) {
        e.preventDefault();
        self.toggleNode($(this));
      });

      $(document).on("click", ".treenode-expand-all", function() {
        self.expandAll();
      });

      $(document).on("click", ".treenode-collapse-all", function() {
        self.collapseAll();
      });

      $('#result_list').on('change', '#action-toggle', function() {
        $('input.action-select').prop('checked', this.checked);
      });
    },

    enableDragAndDrop: function() {
      const self = this;

      this.$tableBody.sortable({
        items: "tr",
        handle: ".treenode-drag-handle",
        placeholder: "treenode-placeholder",
        helper: function(e, tr) {
          const $originals = tr.children();
          const $helper = tr.clone();
          $helper.find('[id]').removeAttr('id');
          $helper.children().each(function(index) {
            $(this).width($originals.eq(index).width());
          });
          return $helper;
        },
        start: function(e, ui) {
          TreeFx.markDragging(ui.item, true);
          self.setDropContext(null, null, null);
          self.updateDndHighlight();
        },
        sort: function(e, ui) {
          self.updateDndHighlight(e, ui);
        },
        stop: function(e, ui) {
          TreeFx.markDragging(ui.item, false);
          const $item = ui.item;
          const nodeId = $item.data("node-id");
          self.updateDndHighlight(e, ui);

          const context = self.resolveDropContext();

          self.clearDndHighlights();
          self.setDropContext(null, null, null);

          self.applyMove(nodeId, context.anchorId, context.position);
          TreeFx.flashInsert(nodeId);
        },
      });
    },

    setDropContext: function($row, anchorId, position) {
      this.dropContext = {
        $row: $row || null,
        anchorId: anchorId || null,
        position: position || null,
      };
    },

    resolveDropContext: function() {
      if (this.dropContext && this.dropContext.position) {
        return {
          anchorId: this.dropContext.anchorId,
          position: this.dropContext.position,
        };
      }

      const $placeholder = this.$tableBody.find("tr.treenode-placeholder");
      const $prev = $placeholder.prev("tr[data-node-id]");

      if ($prev.length) {
        return {
          anchorId: $prev.data("node-id"),
          position: "after",
        };
      }

      return {
        anchorId: null,
        position: "inside-last",
      };
    },

    clearDndHighlights: function() {
      this.$tableBody.find("tr.drop-before, tr.drop-after, tr.drop-inside")
        .removeClass("drop-before drop-after drop-inside");
    },

    calculateDropContext: function(event, ui) {
      if (!event || typeof event.clientX !== "number" || typeof event.clientY !== "number") {
        return this.resolveDropContext();
      }

      const hoveredElement = document.elementFromPoint(event.clientX, event.clientY);
      const $hoveredRow = $(hoveredElement).closest("tr[data-node-id]");
      const $draggedRow = ui && ui.item ? ui.item : $();

      if (!$hoveredRow.length || ($draggedRow.length && $hoveredRow.is($draggedRow))) {
        return this.resolveDropContext();
      }

      const rect = $hoveredRow.get(0).getBoundingClientRect();
      const offsetY = event.clientY - rect.top;
      const zoneRatio = rect.height > 0 ? offsetY / rect.height : 0.5;
      let position = "inside-last";

      if (zoneRatio < 0.33) {
        position = "before";
      } else if (zoneRatio > 0.66) {
        position = "after";
      }

      return {
        $row: $hoveredRow,
        anchorId: $hoveredRow.data("node-id"),
        position: position,
      };
    },

    updateDndHighlight: function(event, ui) {
      const context = this.calculateDropContext(event, ui);
      const $target = context.$row;

      this.clearDndHighlights();

      if (!$target || !$target.length) {
        this.setDropContext(null, context.anchorId, context.position);
        return;
      }

      if (context.position === "before") {
        $target.addClass("drop-before");
      } else if (context.position === "after") {
        $target.addClass("drop-after");
      } else {
        $target.addClass("drop-inside");
      }

      this.setDropContext($target, context.anchorId, context.position);
    },

    applyMove: function(nodeId, anchorId, position) {
      if (this.isMoving) return;

      this.isMoving = true;

      const params = {
        node_id: nodeId,
        anchor_id: anchorId,
        position: position
      };

      $.ajax({
        url: 'move/',
        method: 'POST',
        data: params,
        dataType: 'json',
        success: function(data) {
          const msg = data.message || "Node moved successfully.";
          $("<li class='success'>" + msg + "</li>").appendTo(".messagelist");
        },
        error: function(xhr, status, error) {
          const fallback = "Error moving node.";
          $("<li class='error'>" + (xhr.responseText || fallback) + "</li>").appendTo(".messagelist");
        },
        complete: function() {
          ChangeList.isMoving = false;
          location.reload();
        }
      });
    }
  };

  $(document).ready(function () {
    if ($("table#result_list").length) {
      ChangeList.init();
      ChangeList.restoreTreeState();
    }
  });

})(django.jQuery || window.jQuery);
