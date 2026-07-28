(function () {
  function fitPromptTextarea(textarea) {
    if (!textarea || textarea.dataset.codexPromptFit === "disabled") return;
    var maxHeight = 520;
    textarea.style.height = "auto";
    var nextHeight = Math.min(Math.max(textarea.scrollHeight, 180), maxHeight);
    textarea.style.height = nextHeight + "px";
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }

  function enhancePromptTextareas(root) {
    var scope = root || document;
    scope.querySelectorAll("textarea.prompt-textarea-auto-expand").forEach(function (textarea) {
      if (!textarea.dataset.codexPromptBound) {
        textarea.dataset.codexPromptBound = "true";
        textarea.addEventListener("input", function () {
          fitPromptTextarea(textarea);
        });
      }
      fitPromptTextarea(textarea);
    });
  }

  function getHeaderIndex(table, names) {
    var headers = Array.from(table.querySelectorAll("thead th")).map(function (th) {
      return (th.textContent || "").trim().toLowerCase();
    });
    for (var i = 0; i < headers.length; i += 1) {
      if (names.indexOf(headers[i]) !== -1) return i;
    }
    return -1;
  }

  function enhanceLongDescriptionTables(root) {
    var scope = root || document;
    scope.querySelectorAll("table").forEach(function (table) {
      var index = getHeaderIndex(table, [
        "description",
        "use case description",
        "research finding / impact claim",
        "quantitative outcome"
      ]);
      if (index < 0) return;

      table.querySelectorAll("tbody tr").forEach(function (row) {
        var cell = row.children[index];
        if (!cell || cell.dataset.codexClampBound) return;
        var original = (cell.textContent || "").trim();
        if (original.length < 120) return;

        cell.dataset.codexClampBound = "true";
        cell.dataset.codexFullText = original;
        cell.textContent = "";

        var text = document.createElement("div");
        text.className = "codex-two-line-description";
        text.textContent = original;

        var button = document.createElement("button");
        button.type = "button";
        button.className = "codex-show-more";
        button.textContent = "show more";
        button.addEventListener("click", function (event) {
          event.preventDefault();
          event.stopPropagation();
          var collapsed = text.classList.toggle("codex-two-line-description");
          button.textContent = collapsed ? "show more" : "show less";
        });

        cell.appendChild(text);
        cell.appendChild(button);
      });
    });
  }

  function enhance(root) {
    enhancePromptTextareas(root);
    enhanceLongDescriptionTables(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      enhance(document);
    });
  } else {
    enhance(document);
  }

  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType === 1) enhance(node);
      });
    });
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
