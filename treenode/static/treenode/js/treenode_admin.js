/* 
TreeNode Admin JavaScript

This script enhances the Django admin interface with interactive 
tree structure visualization. It provides expand/collapse functionality 
for hierarchical data representation.

Features:
- Dynamically detects parent-child relationships in the admin table.
- Allows nodes to be expanded and collapsed with smooth animations.
- Saves expanded/collapsed states in localStorage for persistence.
- Optimizes tree traversal with efficient DOM manipulation.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
*/

(function($) {
    $(document).ready(function() {
        // Mapping parent node -> list of child nodes
        var childrenMap = {};

        // Iterate over all tree nodes to build a mapping of parent-child relationships
        $('.treenode, .treenode-wrapper').each(function() {
            var parent = $(this).data('treenode-parent'); // Get parent ID
            var pk = $(this).data('treenode-pk'); // Get node primary key
            
            if (parent) {
                if (!childrenMap[parent]) {
                    childrenMap[parent] = [];
                }
                childrenMap[parent].push(pk);
            }
        });

        // Initialize tree nodes, set up toggles
        $('.treenode, .treenode-wrapper').each(function() {
            var $node = $(this);
            var pk = $node.data('treenode-pk'); // Get current node ID
            var depth = parseInt($node.data('treenode-depth'), 10) || 0; // Get tree depth level
            var $tr = $node.closest('tr'); // Find the corresponding row in the table
            $tr.attr('data-treenode-depth', depth);
            $tr.attr('data-treenode-pk', pk);

            var $th = $tr.find('th:first');
            if ($th.find('.treenode-space, .treenode-toggle').length === 0) {
                var $placeholder = $('<span class="treenode-space"> </span>')
                    .css('margin-left', (depth * 20) + 'px'); // Indentation based on depth
                $th.prepend($placeholder);
            }

            // If node has children, add expand/collapse toggle
            if (childrenMap[pk]) {
                var expanded = loadState(pk);
                var $placeholder = $th.find('.treenode-space');
                var $toggle = $('<span class="treenode-toggle button"></span>')
                    .css('margin-left', (depth * 20) + 'px');
                
                if (expanded) {
                    $toggle.addClass('expanded').text('-');
                } else {
                    $toggle.addClass('collapsed').text('+');
                }
                $placeholder.replaceWith($toggle);
                
                if (!expanded) {
                    collapseNode($tr, true);
                }

                // Toggle node expansion/collapse on click
                $toggle.on('click', function() {
                    if ($(this).hasClass('expanded')) {
                        collapseNode($tr, false);
                        $(this).removeClass('expanded').addClass('collapsed').text('+');
                        saveState(pk, false);
                    } else {
                        expandNode($tr);
                        $(this).removeClass('collapsed').addClass('expanded').text('-');
                        saveState(pk, true);
                    }
                });
            }
        });

        // Apply initial collapsed states based on saved preferences
        function applyCollapsedStates() {
            $('tr').each(function() {
                var $tr = $(this);
                var currentDepth = parseInt($tr.attr('data-treenode-depth'), 10);
                var hide = false;
                
                // Check if any ancestor is collapsed
                $tr.prevAll('tr').each(function() {
                    var $prev = $(this);
                    var prevDepth = parseInt($prev.attr('data-treenode-depth'), 10);
                    if (prevDepth < currentDepth) {
                        var parentPk = $prev.attr('data-treenode-pk');
                        if (loadState(parentPk) === false) {
                            hide = true;
                        }
                        return false;
                    }
                });
                
                if (hide) {
                    $tr.hide();
                }
            });
        }
        applyCollapsedStates();

        // Collapse a node and all its descendants
        function collapseNode($tr, immediate) {
            var parentDepth = parseInt($tr.attr('data-treenode-depth'), 10);
            var $nextRows = $tr.nextAll('tr');
            $nextRows.each(function() {
                var $row = $(this);
                var rowDepth = parseInt($row.attr('data-treenode-depth'), 10);
                if (rowDepth > parentDepth) {
                    if (immediate) {
                        $row.hide();
                    } else {
                        $row.slideUp(300);
                    }
                    var childPk = $row.attr('data-treenode-pk');
                    saveState(childPk, false);
                } else {
                    return false;
                }
            });
        }

        // Expand a node and reveal its immediate children
        function expandNode($tr) {
            var parentDepth = parseInt($tr.attr('data-treenode-depth'), 10);
            var $nextRows = $tr.nextAll('tr');
            $nextRows.each(function() {
                var $row = $(this);
                var rowDepth = parseInt($row.attr('data-treenode-depth'), 10);
                if (rowDepth > parentDepth) {
                    if (rowDepth === parentDepth + 1) {
                        $row.slideDown('slow');
                        var childPk = $row.attr('data-treenode-pk');
                        if (loadState(childPk)) {
                            expandNode($row);
                        }
                    }
                } else {
                    return false;
                }
            });
        }

        // Save expansion state to localStorage
        function saveState(pk, isExpanded) {
            if (window.localStorage) {
                localStorage.setItem('treenode_state_' + pk, isExpanded ? '1' : '0');
            }
        }

        // Load expansion state from localStorage
        function loadState(pk) {
            if (window.localStorage) {
                var state = localStorage.getItem('treenode_state_' + pk);
                return state === '1';
            }
            return true;
        }
    });
})(django.jQuery || window.jQuery);
