// Trivial client-side search over the build-time search-index.json.
// No indexing library: for a personal blog's page count, a linear
// substring scan on keystroke is imperceptibly fast and needs no deps.
(function () {
  "use strict";
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  if (!input || !results) return;

  var index = [];
  fetch("/search-index.json").then(function (r) { return r.json(); }).then(function (data) {
    index = data;
  });

  function render(matches) {
    results.innerHTML = "";
    matches.slice(0, 50).forEach(function (page) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = page.url;
      a.textContent = page.title;
      var p = document.createElement("p");
      p.className = "summary";
      p.textContent = page.summary;
      li.appendChild(a);
      li.appendChild(p);
      results.appendChild(li);
    });
  }

  input.addEventListener("input", function () {
    var q = input.value.trim().toLowerCase();
    if (!q) { results.innerHTML = ""; return; }
    var matches = index.filter(function (page) {
      return (
        page.title.toLowerCase().includes(q) ||
        page.summary.toLowerCase().includes(q) ||
        page.tags.some(function (t) { return t.toLowerCase().includes(q); })
      );
    });
    render(matches);
  });
})();
