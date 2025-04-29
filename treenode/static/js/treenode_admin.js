/**
 * treenode_admin.js
 *
 * Advanced TreeNode Admin extension for Django Admin.
 * Adds dynamic drag-and-drop sorting, AJAX-based subtree loading,
 * real-time visual feedback, and persistent tree state.
 *
 * Features:
 * - Drag-and-drop node movement with Shift for child placement
 * - Visual animations for feedback (insert flash, drag highlight)
 * - Inline AJAX expansion and collapse of subtrees
 * - Server-side re-rendering and recovery after node movement
 * - Lightweight localStorage persistence using compressed HTML
 *
 * Version: 3.0.0
 * Author: Timur Kady
 * Email: timurkady@yandex.com
 */


(function($) {

  // ------------------------------- //
  // Service and auxiliary functions //
  // ------------------------------- //

  function debounce(func, wait) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        func.apply(context, args);
      }, wait);
    };
  }
  
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
  
  function showAdminMessage(text, level = "info", duration = 6000) {
    const $ = django.jQuery || window.jQuery;

    // Make sure the block exists
    let msgList = $(".messagelist");
    if (!msgList.length) {
      msgList = $('<ul class="messagelist"></ul>');
      $("#content").before(msgList);
    }

    // Create a message
    const msg = $(`<li class="${level}">${text}</li>`);

    msgList.append(msg);

    // Auto disappear after 6 seconds (default)
    setTimeout(() => {
      msg.fadeOut(500, () => msg.remove());
    }, duration);
  }

  function hangleAjaxSuccess(data) {
    const msg = data.message || "The request was successfully completed.";
    showAdminMessage(msg, "success");
    ChangeList.saveTree()
    ChangeList.restoreTree(ChangeList.expandedNodes);
  }
  
  function handleAjaxError(xhr, status, error) {
    ChangeList.restoreTree(ChangeList.expandedNodes);

    const fallbackMessage = "An unknown error occurred while executing the request.";
    const $ = django.jQuery || window.jQuery;
    let message = "";

    // Try to extract the JSON error
    try {
      const contentType = xhr.getResponseHeader("Content-Type") || "";
      if (contentType.includes("application/json")) {
        const data = xhr.responseJSON || JSON.parse(xhr.responseText);
        if (data?.error) {
          message = data.error;
        } else if (typeof data?.detail === "string") {
          message = data.detail;
        } else if (typeof data === "string") {
          message = data;
        }
      }
    } catch (e) {
      // Not JSON – silently continue
    }

    // Try to parse plain HTML Django error and extract exception summary
    if (!message && xhr.responseText) {
      try {
        // Try to extract main exception message from Django debug HTML
        const match = xhr.responseText.match(/<pre class="exception_value">([^<]+)<\/pre>/);
        if (match && match[1]) {
          message = match[1].trim();
        } else {
          // As fallback, extract first lines of cleaned HTML
          const plain = xhr.responseText.replace(/<\/?[^>]+(>|$)/g, "").trim();
          const lines = plain.split("\n").map(line => line.trim()).filter(Boolean);
          if (lines.length) {
            message = lines.slice(0, 3).join(" — ");  // keep it brief
          }
        }
      } catch (e) {
        // Parsing failed, do nothing
      }
    }
  
    // If there is still nothing, build a generic fallback
    if (!message) {
      if (xhr.status) {
        message = `${xhr.status}: ${error || status}`;
      } else {
        message = fallbackMessage;
      }
    }
  
    showAdminMessage(message, "error");
  }

  function isDarkTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function applyTheme() {
    var dark = isDarkTheme();
    var $container = $(".tree-widget");
    var $dropdown = $(".tree-widget-dropdown");

    if (dark) {
      $dropdown.addClass("dark-theme");
      $container.addClass("dark-theme");
    } else {
      $dropdown.removeClass("dark-theme");
      $container.removeClass("dark-theme");
    }
  }
  
  let ajaxCounter = 0;
  
  function clearCursor() {
    ajaxCounter--;
    if (ajaxCounter === 0) {
      $('body').css('cursor', 'default');
    }
  }

  // ------------------------------- //
  //            AJAX Setup           //
  // ------------------------------- //

  const csrftoken = getCookie('csrftoken');

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!/^https?:.*/.test(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
      ajaxCounter++;
      $('body').css('cursor', 'wait');
    },
    cache: false
  });

  // ------------------------------- //
  //  Animations and visual feedback //
  // ------------------------------- //

  const TreeFx = {
    // Highlight the line where the element was moved
    flashInsert(nodeId) {
      const $row = $(`tr[data-node-id="${nodeId}"]`);
      if (!$row.length) return;

      $row.addClass("flash-insert");
      setTimeout(() => $row.removeClass("flash-insert"), 1000);
    },

    // Fading in a new tbody (e.g. after reloadTree)
    fadeInTbody(newHTML, callback) {
      const $tbody = $('table#result_list tbody');
      $tbody.stop(true, true).fadeOut(100, () => {
        $tbody.html(newHTML).fadeIn(150, callback);
      });
    },

    // Visual cue when drag starts and ends
    markDragging($item, enable) {
      $item.toggleClass('dragging', enable);
    },
  };


  // ------------------------------- //
  //            Main Class           //
  // ------------------------------- //


  var ChangeList = {
    $tableBody: null,
    isShiftPressed: false,
    activeTargetRow: null,
    isMoving: false,
    expandedNodes: [],
    label: '',

    init: function() {
      this.$tableBody = $('table#result_list tbody');
      this.bindEvents();
      this.restoreTree();
      this.enableDragAndDrop();
    },

    saveTree: function() {
      if (!this.$tableBody) return;
      
      this.expandedNodes = [];
      this.$tableBody.find(".treenode-toggle").each(function () {
        $btn = $(this)
        if ($btn.data('expanded')) {
          ChangeList.expandedNodes.push($btn.data('node-id'));
        }
      });
      if (!(this.expandedNodes ) || (this.expandedNodes.length === 0)) {
        localStorage.removeItem("saved_tbody");
      } else {
        localStorage.setItem("saved_tbody", JSON.stringify(this.expandedNodes));
      }
      const count = $("#result_list tbody tr").length;
      if (count > 0) {
        $("p.paginator").first().text(`${count} ${ChangeList.label}`);
        localStorage.setItem("label", ChangeList.label);
      }
      
    },

    restoreTree: function(expandedList = null) {
      const expanded = expandedList || JSON.parse(localStorage.getItem("saved_tbody") || "[]");
      ChangeList.label = localStorage.getItem("label") || "";
      if (!expanded.length) return;
    
      const params = { expanded: JSON.stringify(expanded) };
      
      $.ajax({
        url: 'change_list/',
        method: 'GET',
        data: params,
        dataType: 'json',
        success: function(data) {
          ChangeList.$tableBody.html(data.html);
          ChangeList.expandedNodes = expanded;

          ChangeList.$tableBody.find(".treenode-toggle").each(function () {
            const $btn = $(this);
            const nodeId = $btn.data('node-id');
            if (ChangeList.expandedNodes.includes(nodeId)) {
              $btn.data("expanded", true);
              $btn.text("▼");
            }
          });
          
          if (data.label) ChangeList.label = data.label;
          const count = $("#result_list tbody tr").length;
          $("p.paginator").first().text(`${count} ${ChangeList.label}`);
        },
        error: function(xhr, status, error) {
          handleAjaxError(xhr, status, error);
          // console.error("Restore error:", status, error);
        },
        complete: function() {
          clearCursor();
        }
      });
    },
    
    searchRows: function(searchQuery) {
      var params = { q: searchQuery };

      $.ajax({
        url: 'change_list/',
        method: 'GET',
        data: params,
        dataType: 'json',
        success: function(data) {
          ChangeList.$tableBody.html(data.html);
        },
        error: function(xhr, status, error) {
          handleAjaxError(xhr, status, error);
          // console.error("Search error:", status, error);
        },
        complete: function() {
          clearCursor();
        }
      });
    },

    insertRows: function($parentRow, parentId) {
      var parent_id = parentId
      var params = {parent_id: parent_id};

      $.ajax({
        url: 'change_list/',
        method: 'GET',
        data: params,
        dataType: 'json',
        success: function(data) {
          $parentRow.after(data.html);
          if (data.label) ChangeList.label = data.label;
        },
        error: function(xhr, status, error) {
          handleAjaxError(xhr, status, error);
          // console.error("Insert rows error:", status, error);
        },
        complete: function() {
          ChangeList.saveTree();
          clearCursor();
        }
      });
    },

    removeRows: function(parentId) {
      var $children = this.$tableBody.find(`tr[data-parent-of="${parentId}"]`);
      $children.each(function () {
        var childId = $(this).data('node-id');
        ChangeList.removeRows(childId);
      });
      $children.remove();
      this.saveTree();
    },

    toggleNode: function($btn) {
      var expanded = $btn.data('expanded');
      var $parentRow = $btn.closest('tr');
      var parentId = $btn.data('node-id');

      if (expanded) {
        $btn.html('►').data('expanded', false);
        this.removeRows(parentId);
      } else {
        $btn.html('▼').data('expanded', true);
        this.insertRows($parentRow, parentId);
      }
    },

    bindEvents: function() {
      var self = this;

      // Search listener
      $('input[name="q"]')
        .on("focus", function() {
          self.saveTree();
        })
        .on("keyup", debounce(function() {
          var query = $.trim($(this).val());
          if (query === '') {
            self.restoreTree(ChangeList.expandedNodes);
          } else {
            self.searchRows(query);
          }
        }, 300));

      // Toggle buttons listener
      $(document).on("click", "button.treenode-toggle", function(e) {
        e.preventDefault();
        var $btn = $(this);
        self.toggleNode($btn);
      });
      
      // Shift key hold listener
      $(document).on("keydown", function(e) {
        if (e.key === "Shift") {
          ChangeList.isShiftPressed = true;
          ChangeList.updateDndHighlight();
        }
      })
      .on("keyup", function(e) {
        if (e.key === "Shift") {
          ChangeList.isShiftPressed = false;
          ChangeList.updateDndHighlight();
        }
      });
      
      // Listener for admin panel theme change button
      $(document).on("click", "button.theme-toggle", function() {
        applyTheme();
      });
      
      // Fix action selets  
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
        activeTargetRow: null,
        helper: function(e, tr) {
          const $originals = tr.children();
          const $helper = tr.clone();
          $helper.find('[id]').each(function() {
            $(this).removeAttr('id');
          });
          $helper.children().each(function(index) {
            $(this).width($originals.eq(index).width());
          });
          return $helper;
        },
        start: function(e, ui) {
          TreeFx.markDragging(ui.item, true);
          // ChangeList.updateDndHighlight();
          // console.log("Drag started:", ui.item.data("node-id"));
        },
        over: function(e, ui) {
          ChangeList.updateDndHighlight();
          // console.log("over")
        },
        stop: function(e, ui) {
          TreeFx.markDragging(ui.item, false);

          const $item = ui.item;
          const nodeId = $item.data("node-id");
          const prevId = $item.prev().data("node-id") || null;
          const nextId = $item.next().data("node-id") || null;
          const isChild = ChangeList.isShiftPressed;

          if (ChangeList.activeTargetRow) {
            ChangeList.activeTargetRow.removeClass("target-as-child");
            ChangeList.activeTargetRow = null;
          }

          mode = isChild ? 'child' : 'after';
          ChangeList.applyMove(nodeId, prevId, mode)

          TreeFx.flashInsert(nodeId);
        },
      });
    },
    
    updateDndHighlight: function() {
      const $placeholder = this.$tableBody.find("tr.treenode-placeholder");
      const $target = $placeholder.prev();
    
      if (!($target && $target.length && $target.data("node-id"))) {
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
        mode: mode,
        expanded: JSON.stringify(this.expandedNodes)
      };
      
      // console.log(params);
    
      $.ajax({
        url: 'move/',
        method: 'POST',
        data: params,
        dataType: 'json',
        success: function(data) {
          hangleAjaxSuccess(data);
        },
        error: function(xhr, status, error) {
          handleAjaxError(xhr, status, error);
        },
        complete: function() {
          ChangeList.isMoving = false;
          clearCursor();
        }
      });
    }
  }

  // ------------------------------- //
  //               Init              //
  // ------------------------------- //

  $(document).ready(function () {
    document.body.style.cursor = '';
    applyTheme();
      if ($("table#result_list").length) {
        ChangeList.init();
      }
  });

})(django.jQuery || window.jQuery);

