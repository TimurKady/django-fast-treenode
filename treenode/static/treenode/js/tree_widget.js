/* 
TreeNode Select2 Widget

This script enhances the Select2 dropdown widget for hierarchical data 
representation in Django admin. It supports AJAX data fetching and ensures 
a structured tree-like display.

Features:
- Dynamically initializes Select2 on elements with the class `tree-widget`.
- Retrieves data via AJAX and displays it with proper indentation.
- Supports dark mode and automatically applies theme styling.
- Handles parent-child relationships and updates node priorities.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
*/


(function ($) {
    "use strict";

    /**
     * Initializes Select2 on all elements with the class "tree-widget".
     * Ensures proper AJAX data fetching and hierarchical display.
     */
    function initializeSelect2() {
        $(".tree-widget").each(function () {
            var $widget = $(this);
            var url = $widget.data("url"); // Fetch the data URL for AJAX requests

            if (!url) {
                console.error("Error: Missing data-url for", $widget.attr("id"));
                return;
            }

            // Initialize Select2 with AJAX support
            $widget.select2({
                ajax: {
                    url: url,
                    dataType: "json",
                    delay: 250, // Introduces a delay to avoid excessive API calls
                    data: function (params) {
                        var forwardData = $widget.data("forward") || {}; // Retrieve forwarded model data
                        return {
                            q: params.term, // Search query parameter
                            model: forwardData.model || null, // Pass the model name
                        };
                    },
                    processResults: function (data) {
                        if (!data.results) {
                            return { results: [] }; // Return an empty array if no results exist
                        }
                        return { results: data.results };
                    },
                },
                minimumInputLength: 0, // Allows opening the dropdown without typing
                allowClear: true, // Enables the "clear selection" button
                width: "100%", // Expands the dropdown to fit the parent container
                templateResult: formatTreeResult, // Custom rendering function for hierarchical display
            });

            // Immediately apply theme styling after Select2 initialization
            var select2Instance = $widget.data("select2");
            if (select2Instance && isDarkTheme()) {
                select2Instance.$container
                    .find(".select2-selection--single")
                    .addClass("dark-theme"); // Apply dark mode styling if enabled
            }
        });
    }

    /**
     * Checks whether dark mode is enabled.
     * It relies on the presence of the `data-theme="dark"` attribute on the <html> tag.
     * @returns {boolean} - True if dark mode is active, false otherwise.
     */
    function isDarkTheme() {
        return document.documentElement.getAttribute("data-theme") === "dark";
    }

    /**
     * Applies or removes the `.dark-theme` class to the Select2 dropdown and container.
     * Ensures the dropdown styling follows the selected theme.
     */
    function applyTheme() {
        var dark = isDarkTheme(); // Check if dark mode is enabled
        var $dropdown = $(".select2-container--open .select2-dropdown"); // Get the currently open dropdown
        var $container = $(".select2-container--open .select2-selection--single"); // Get the selection box

        if (dark) {
            $dropdown.addClass("dark-theme");
            $container.addClass("dark-theme");
        } else {
            $dropdown.removeClass("dark-theme");
            $container.removeClass("dark-theme");
        }
    }

    /**
     * Formats each result in the Select2 dropdown to visually represent hierarchy.
     * Adds indentation based on node depth and assigns folder/file icons.
     * @param {Object} result - A single result object from the AJAX response.
     * @returns {jQuery} - A formatted span element with the tree structure.
     */
    function formatTreeResult(result) {
        if (!result.id) {
            return result.text; // Return plain text for placeholder options
        }
        var level = result.level || 0; // Retrieve node depth (default: 0)
        var is_leaf = result.is_leaf || false; // Determine if it's a leaf node
        var indent = "&nbsp;&nbsp;".repeat(level); // Create indentation based on depth
        var icon = is_leaf ? "📄 " : "📂 "; // Use 📄 for leaves, 📂 for parent nodes
        return $("<span>" + indent + icon + result.text + "</span>"); // Return formatted text
    }

    /**
     * Binds event listeners and initializes Select2.
     * Ensures correct theme application on page load and during interactions.
     */
    $(document).ready(function () {
        initializeSelect2();
        applyTheme();

        // When a Select2 dropdown opens, update its theme
        $(document).on("select2:open", function () {
            applyTheme();
        });

        // When the theme toggle button is clicked, reapply the theme
        $(document).on("click", ".theme-toggle", function () {
            applyTheme();
        });

        // When a parent changes, get the number of its children and set tn_priority
        $("#id_tn_parent").on("change", function () {
            var parentId = $(this).val();
            var model = $(this).data("forward") ? $(this).data("forward").model : null;

            if (!parentId || !model) {
                console.log("No parent selected or model is missing.");
                return;
            }

            $.ajax({
                url: "/treenode/get-children-count/",
                data: { parent_id: parentId, model: model },
                dataType: "json",
                success: function (response) {
                    if (response.children_count !== undefined) {
                        $("#id_tn_priority").val(response.children_count);  // Set the value
                    }
                },
                error: function () {
                    console.error("Failed to fetch children count.");
                }
            });
        });
    });

})(django.jQuery || window.jQuery);
