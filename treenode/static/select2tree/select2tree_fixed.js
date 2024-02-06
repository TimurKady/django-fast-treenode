
/*!
 * Select2-to-Tree 1.1.1
 * https://github.com/clivezhg/select2-to-tree
 */
window.addEventListener("load", function() {
    (function ($) {
        $.fn.select2ToTree = function (options) {
            var opts = $.extend({}, $.fn.select2ToTree.defaults, options);

            function escapeHtml(text) {
                var map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                };
                return text.replace(/[&<>"']/g, function(m) { return map[m]; });
            }

            if (opts.treeData) {
                buildSelect(opts.treeData, this);
            }

            opts._templateResult = opts.templateResult;
            opts.templateResult = function (data, container) {
                if (data.element) {
                    container.setAttribute("data-val", escapeHtml(data.element.value));
                    if (data.element.className) container.className += " " + escapeHtml(data.element.className);
                    if (data.element.getAttribute("data-pup")) {
                        container.setAttribute("data-pup", escapeHtml(data.element.getAttribute("data-pup")));
                    }
                }
                return data.text;
            };

            function toggleSubOptions(target) {
                $(target).closest('.select2-results__option').toggleClass('opened');
            }

            window.expColMouseupHandler = function (evt) {
                toggleSubOptions(evt.target);
                evt.stopPropagation();
                evt.preventDefault();
            }

            var s2 = this.select2(opts);
            s2.data('select2').$container.on('mouseup', '.expand-collapse', expColMouseupHandler);
            return s2;
        };

        $.fn.select2ToTree.defaults = {
            templateResult: function (data) {
                if (!data.id) { return data.text; }
                var $result = $('<span></span>');
                var $expandCollapse = $('<span class="expand-collapse"></span>').text(data.text);
                return $result.append($expandCollapse);
            }
        };

        function buildSelect(treeData, $el) {

            /* Support the object path (eg: `item.label`) for 'valFld' & 'labelFld' */
            function readPath(object, path) {
                var currentPosition = object;
                for (var j = 0; j < path.length; j++) {
                    var currentPath = path[j];
                    if (currentPosition[currentPath]) {
                        currentPosition = currentPosition[currentPath];
                        continue;
                    }
                    return 'MISSING';
                }
                return currentPosition;
            }

            function buildOptions(dataArr, curLevel, pup) {
                var labelPath;
                if (treeData.labelFld && treeData.labelFld.split('.').length> 1){
                    labelPath = treeData.labelFld.split('.');
                }
                var idPath;
                if (treeData.valFld && treeData.valFld.split('.').length > 1) {
                    idPath = treeData.valFld.split('.');
                }

                for (var i = 0; i < dataArr.length; i++) {
                    var data = dataArr[i] || {};
                    var $opt = $("<option></option>");
                    if (labelPath) {
                        $opt.text(readPath(data, labelPath));
                    } else {
                        $opt.text(data[treeData.labelFld || "text"]);
                    }
                    if (idPath) {
                        $opt.val(readPath(data, idPath));
                    } else {
                        $opt.val(data[treeData.valFld || "id"]);
                    }
                    if (data[treeData.selFld || "selected"] && String(data[treeData.selFld || "selected"]) === "true") {
                        $opt.prop("selected", data[treeData.selFld || "selected"]);
                    }
                    if($opt.val() === "") {
                        $opt.prop("disabled", true);
                        $opt.val(getUniqueValue());
                    }
                    $opt.addClass("l" + curLevel);
                    if (pup) $opt.attr("data-pup", pup);
                    $el.append($opt);
                    var inc = data[treeData.incFld || "inc"];
                    if (inc && inc.length > 0) {
                        $opt.addClass("non-leaf");
                        buildOptions(inc, curLevel+1, $opt.val());
                    }
                } // end 'for'
            } // end 'buildOptions'

            buildOptions(treeData.dataArr, 1, "");
            if (treeData.dftVal) $el.val(treeData.dftVal);
        }

        var uniqueIdx = 1;
        function getUniqueValue() {
            return "autoUniqueVal_" + uniqueIdx++;
        }

        function toggleSubOptions(target) {
            $(target.parentNode).toggleClass("opened");
            showHideSub(target.parentNode);
        }

        function showHideSub(ele) {
            var curEle = ele;
            var $options = $(ele).parent(".select2-results__options");
            var shouldShow = true;
            do {
                var pup = ($(curEle).attr("data-pup") || "").replace(/'/g, "\\'");
                curEle = null;
                if (pup) {
                    var pupEle = $options.find(".select2-results__option[data-val='" + pup + "']");
                    if (pupEle.length > 0) {
                        if (!pupEle.eq(0).hasClass("opened")) { // hide current node if any parent node is collapsed
                            $(ele).removeClass("showme");
                            shouldShow = false;
                            break;
                        }
                        curEle = pupEle[0];
                    }
                }
            } while (curEle);
            if (shouldShow) $(ele).addClass("showme");

            var val = ($(ele).attr("data-val") || "").replace(/'/g, "\\'");
            $options.find(".select2-results__option[data-pup='" + val + "']").each(function () {
                showHideSub(this);
            });
        }
    })(django.jQuery);
});
