/* 
TreeNode Select2 Widget

This script replaces Django's Select widget for presenting hierarchical data
in the Django admin panel. The widget is intended for a parent field, but
can be used to select a tree node with a different purpose. It provides
structured tree display.
The widget supports AJAX fetching, which avoids loading the entire tree.

Features:
- Dynamically initializes select-like elements with the `tree-widget` class.
- Fetches data via AJAX and displays it with the correct indentation.
- Supports dark mode and automatically applies theme styles.
- Handles parent-child relationships and updates node priorities.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
*/

(function ($) {
  "use strict";

  var TreeWidget = {
    // Initialize each widget by container with class .tree-widget
    init: function (selector) {
      $(selector).each(function () {
        var $widget = $(this);

        // Find the hidden input, dropdown list and display area inside
        // the container
        var $select = $widget.find('input[type="hidden"]').first();
        var $dropdown = $widget.find('.tree-widget-dropdown').first();
        var $display = $widget.find('.tree-widget-display').first();

        // Get URL for AJAX and model data from data attributes
        var ajaxUrl = $select.data('url');
        var ajaxUrlChildren = $select.data('url-children');
        var model = $select.attr("data-model");
        
        var selectedId = $select.val();
        if (selectedId === undefined) {
            selectedId = "";
        }
        
        var widgetData = {
            $widget: $widget,
            $select: $select,
            $dropdown: $dropdown,
            $display: $display,
            ajaxUrl: ajaxUrl,
            urlChildren: ajaxUrlChildren,
            model: model,
            selectedId: selectedId,
        };
        
        $widget.data('widgetData', widgetData);

        // Load data for the current mode (default, selected or search)
        TreeWidget.loadData(widgetData);

        // Bind event handlers
        TreeWidget.bindEvents(widgetData);
      });
    },

    // Method of loading data via AJAX
    loadData: function (widgetData, searchQuery) {
      var params = {
        model: widgetData.model,
        select_id: widgetData.selectedId
      };
      if (searchQuery) {
        params.q = searchQuery;
      } 
      
      $.ajax({
        url: widgetData.ajaxUrl,
        data: params,
        dataType: 'json',
        success: function (response) {
          var $treeList = widgetData.$dropdown.find('.tree-list');
          $treeList.empty();
          TreeWidget.renderNodes(response.results, $treeList);
          // If needed, you can show a dropdown after loading the data
          // widgetData.$dropdown.show();
        },
        error: function (error) {
          console.error("Error loading data:", params, error);
        }
      });
    },
    
    // Method for formatting a node
    formatNode: function(node, levelOverride) {
      // If levelOverride is passed, use it, otherwise take node.level
      var level = (typeof levelOverride !== 'undefined') ? levelOverride : parseInt(node.level, 10);
      var $li = $('<li></li>')
        .addClass('tree-node')
        .attr('data-id', node.id)
        .attr('data-level', level);
      var indent = level * 20;
      $li.css('margin-left', indent + 'px');
    
      // If the node is not a leaf node, add a button to expand it,
      // otherwise insert an empty element for alignment
      if (!node.is_leaf) {
        var $expandBtn = $('<button type="button" class="expand-button">⏵</button>');
        $li.append($expandBtn);
        $li.append('<span class="node-icon">📁</span>').css({
          display: 'inline-block'
        })
      } else {
        $li.append($('<span class="no-expand"></span>').css({
          display: 'inline-block'
        }));
        $li.append('<span class="node-icon">📄</span>').css({
          display: 'inline-block'
        })
      }
    
      $li.append($('<span class="node-text"></span>').text(node.text));
    
      return $li;
    },
    
    // Method of drawing a node
    renderNodes: function (nodes, $container) {
      $container.empty();
      $.each(nodes, function (index, node) {
        var $nodeElem = TreeWidget.formatNode(node);
        $container.append($nodeElem);
      });
    },
    
    // Handler for clicking on the node's expand button
    expandNode: function ($button, widgetData) {
      var $li = $button.closest('li.tree-node');
      var nodeId = $li.data('id');
      if ($button.data('expanded')) {
        TreeWidget.collapseNode($li);
        $button.text('⏵').data('expanded', false);
      } else {
        $.ajax({
          url: widgetData.urlChildren,
          data: { model: widgetData.model, reference_id: nodeId },
          dataType: 'json',
          success: function (response) {
              var parentLevel = parseInt($li.data('level'), 10);
              var $childrenFragment = $();
              $.each(response.results, function (index, node) {
                  var $childLi = TreeWidget.formatNode(node, parentLevel + 1);
                  $childrenFragment = $childrenFragment.add($childLi);
              });
              $li.after($childrenFragment);
              $button.text('⏷').data('expanded', true);
          },
          error: function (data, error) {
              console.error("Error loading children: ", data, error);
          }
        });
      }
    },

    // Node collapse method
    // Remove child elements that are higher than the parent
    collapseNode: function ($li) {
      var currentLevel = parseInt($li.data('level'), 10);
      var $next = $li.next();
      while ($next.length && parseInt($next.data('level'), 10) > currentLevel) {
        var $temp = $next.next();
        $next.remove();
        $next = $temp;
      }
    },

    // Binding events for widget operation
    bindEvents: function (widgetData) {
      var $dropdown = widgetData.$dropdown;
      var $widget = widgetData.$widget;
      var $select = widgetData.$select;
      var $display = widgetData.$display;

      // Handle click on node expand button
      $dropdown.on('click', '.expand-button', function (e) {
        e.preventDefault();
        e.stopPropagation();
        TreeWidget.expandNode($(this), widgetData);
      });

      // Handle node selection (click on node text)
      $dropdown.on('click', 'li.tree-node', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var $li = $(this).closest('li.tree-node');
        var nodeId = $li.data('id');
        $select.val(nodeId);
        $select.data('selected', nodeId);
        // Update the displayed selected value
        $widget.find('.selected-node').text($(this).text());
        $dropdown.hide();
      });

      // Processing input in the search field
      $dropdown.on('keyup', '.tree-search', function (e) {
        var query = $(this).val();
        if (query.length > 0) {
          TreeWidget.loadData(widgetData, query);
        } else {
          TreeWidget.loadData(widgetData);
        }
      });

      // Handle clicking on the search field clear button
      $dropdown.on('click', '.tree-search-clear', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var $search = $dropdown.find('.tree-search');
        $search.val('');
        TreeWidget.loadData(widgetData);
      });

      // Toggle the visibility of the dropdown list when clicking on the
      // display area
      $display.on('click', function (e) {
        e.preventDefault();
        $dropdown.toggle();
      });

      // Hide the dropdown when clicking outside the widget
      $(document).on('click', function (e) {
        if (!$widget.is(e.target) && $widget.has(e.target).length === 0) {
          $dropdown.hide();
        }
      });
    }
  };


  /**
   * Checks whether dark mode is enabled.
   * It relies on the presence of the `data-theme="dark"` attribute on the
   * <html> tag.
   * @returns {boolean} - True if dark mode is active, false otherwise.
   */
  function isDarkTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  /**
   * Applies or removes the `.dark-theme` class to the Select2 dropdown and
   * container. Ensures the dropdown styling follows the selected theme.
   */
  function applyTheme() {
    var dark = isDarkTheme(); // Check if dark mode is enabled
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

  // Initialize the widget when the page loads using the .tree-widget container
  $(document).ready(function () {
    applyTheme();
    TreeWidget.init('.tree-widget');

    // When a widget dropdown opens, update its theme
    // $(document).on("select2:open", function () {
    //  applyTheme();
    // });

    // When the theme toggle button is clicked, reapply the theme
    $(document).on("click", ".theme-toggle", function () {
      applyTheme();
    });
        
  });

})(django.jQuery || window.jQuery);
