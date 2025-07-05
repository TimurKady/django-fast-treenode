/**
 * treenode_admin.js
 *
 * Cleaned version 3.1.0 — TreeNode Admin extension for Django Admin.
 * - No AJAX loading of children
 * - No persistence in localStorage
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
    isShiftPressed: false,
    activeTargetRow: null,
    isMoving: false,

    init: function() {
      this.$tableBody = $('table#result_list tbody');
      this.bindEvents();
      this.enableDragAndDrop();
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
        localStorage.removeItem("treenode_expanded");
      } else {
        localStorage.setItem("treenode_expanded", JSON.stringify(this.expandedNodes));
      }
    
      const count = $("#result_list tbody tr").length;
      if (count > 0) {
        $("p.paginator").first().text(`${count} ${ChangeList.label}`);
        localStorage.setItem("label", ChangeList.label);
      }
    },

    
    // Restore expanded nodes from localStorage
    restoreTreeState: function() {
      const expanded = JSON.parse(localStorage.getItem("treenode_expanded") || "[]");
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

      $(document).on("keydown", function(e) {
        if (e.key === "Shift") {
          self.isShiftPressed = true;
          self.updateDndHighlight();
        }
      }).on("keyup", function(e) {
        if (e.key === "Shift") {
          self.isShiftPressed = false;
          self.updateDndHighlight();
        }
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
        },
        over: function(e, ui) {
          self.updateDndHighlight();
        },
        stop: function(e, ui) {
          TreeFx.markDragging(ui.item, false);
          const $item = ui.item;
          const nodeId = $item.data("node-id");
          const prevId = $item.prev().data("node-id") || null;
          const mode = self.isShiftPressed ? 'child' : 'after';

          if (self.activeTargetRow) {
            self.activeTargetRow.removeClass("target-as-child");
            self.activeTargetRow = null;
          }

          self.applyMove(nodeId, prevId, mode);
          TreeFx.flashInsert(nodeId);
        },
      });
    },

    updateDndHighlight: function() {
      const $placeholder = this.$tableBody.find("tr.treenode-placeholder");
      const $target = $placeholder.prev();

      if (!$target.length || !$target.data("node-id")) {
        this.$tableBody.find("tr.target-as-child").removeClass("target-as-child");
        this.activeTargetRow = null;
        return;
      }

      if (this.isShiftPressed) {
        if (!this.activeTargetRow || !this.activeTargetRow.is($target)) {
          this.$tableBody.find("tr.target-as-child").removeClass("target-as-child");
          $target.addClass("target-as-child");
          this.activeTargetRow = $target;
        }
      } else {
        if (this.activeTargetRow) {
          this.activeTargetRow.removeClass("target-as-child");
          this.activeTargetRow = null;
        }
      }
    },

    applyMove: function(nodeId, targetId, mode) {
      if (this.isMoving) return;

      this.isMoving = true;
      this.activeTargetRow = null;

      const params = {
        node_id: nodeId,
        target_id: targetId,
        mode: mode
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