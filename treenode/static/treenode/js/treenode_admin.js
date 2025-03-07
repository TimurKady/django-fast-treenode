(function($) {
  // Function "debounce" to delay execution
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
  
  // Function to recursively delete descendants of the current child
  function removeAllDescendants(nodeId) {
    var $children = $tableBody.find(`tr[data-parent-of="${nodeId}"]`);

    $children.each(function () {
        var childId = $(this).data('node-id');
        removeAllDescendants(childId); 
    });

    $children.remove();
  }
  
  // Function to reveal nodes stored in storage
  function restoreExpandedNodes() {
    var expandedNodes = JSON.parse(localStorage.getItem('expandedNodes')) || [];
    if (expandedNodes.length === 0) return;

    function expandNext(nodes) {
      if (nodes.length === 0) return;

      var nodeId = nodes.shift();

      $.getJSON('change_list/', { tn_parent_id: nodeId }, function (response) {
        if (response.html) {
          var $btn = $tableBody.find(`.treenode-toggle[data-node-id="${nodeId}"]`);
          var $parentRow = $btn.closest('tr');
          $parentRow.after(response.html);
          $btn.html('▼').data('expanded', true);
          // Раскрываем следующий узел после завершения AJAX-запроса
          expandNext(nodes);
        }
      });
    }

    // Начинаем раскрытие узлов по порядку
    expandNext([...expandedNodes]);
  }
  
  // Global variables ---------------------------------
  var $tableBody;
  var originalTableHtml;
  
  var expandedNodes = JSON.parse(localStorage.getItem('expandedNodes')) || [];

  // Events -------------------------------------------

  $(document).ready(function () {
      // Сохраняем оригинальное содержимое таблицы (корневые узлы)
      $tableBody = $('table#result_list tbody');
      originalTableHtml = $tableBody.html();
      restoreExpandedNodes();
  });

  // Обработчик клика для кнопок treenode-toggle через делегирование на document
  $(document).on('click', '.treenode-toggle', function(e) {
    e.preventDefault();
    var $btn = $(this);
    var nodeId = $btn.data('node-id');

    // Если узел уже развёрнут, сворачиваем его
    if ($btn.data('expanded')) {
      removeAllDescendants(nodeId);
      $btn.html('►').data('expanded', false);
      
      // Убираем узел из списка сохранённых
      expandedNodes = expandedNodes.filter(id => id !== nodeId);

    } else {
      // Иначе запрашиваем дочерние узлы через AJAX
      $.getJSON('change_list/', { tn_parent_id: nodeId }, function(response) {
        if (response.html) {
          var $parentRow = $btn.closest('tr');
          $parentRow.after(response.html);
          $btn.html('▼').data('expanded', true);
          
          // Сохраняем узел в localStorage
          if (!expandedNodes.includes(nodeId)) {
            expandedNodes.push(nodeId);
          }
          localStorage.setItem('expandedNodes', JSON.stringify(expandedNodes));
        }
      });
    }
    localStorage.setItem('expandedNodes', JSON.stringify(expandedNodes));
  });


  // Обработчик ввода для поля поиска с делегированием на document
  $(document).on('keyup', 'input[name="q"]', debounce(function(e) {
    var query = $.trim($(this).val());
    
    if (query === '') {
      $tableBody.html(originalTableHtml);
      return;
    }
    
    $.getJSON('search/', { q: query }, function(response) {
      var rowsHtml = '';
      if (response.results && response.results.length > 0) {
        $.each(response.results, function(index, node) {
          var dragCell = '<td class="drag-cell"><span class="treenode-drag-handle">↕</span></td>';
          var toggleCell = '';
          if (!node.is_leaf) {
            toggleCell = '<td class="toggle-cell"><button class="treenode-toggle" data-node-id="' + node.id + '">▶</button></td>';
          } else {
            toggleCell = '<td class="toggle-cell"><div class="treenode-space">&nbsp;</div></td>';
          }
          var displayCell = '<td class="display-cell">' + node.text + '</td>';
          rowsHtml += '<tr>' + dragCell + toggleCell + displayCell + '</tr>';
        });
      } else {
        rowsHtml = '<tr><td colspan="3">Ничего не найдено</td></tr>';
      }
      $tableBody.html(rowsHtml);
    });
  }, 500));

})(django.jQuery || window.jQuery);
