// Gwern-style hover popups for internal links. Vanilla JS, no dependencies:
// every internal link already carries its own preview text as data
// attributes (baked in at build time), so this only has to show/hide/
// position a tooltip -- no network request needed.
(function () {
  "use strict";
  var popup = document.getElementById("popup");
  if (!popup) return;

  var showTimer = null;
  var current = null;

  function show(link) {
    var title = link.getAttribute("data-preview-title");
    var preview = link.getAttribute("data-preview");
    if (!preview) return;

    popup.innerHTML = "";
    if (title) {
      var h = document.createElement("strong");
      h.textContent = title;
      popup.appendChild(h);
    }
    var p = document.createElement("p");
    p.textContent = preview;
    popup.appendChild(p);
    popup.hidden = false;

    var rect = link.getBoundingClientRect();
    var top = rect.bottom + window.scrollY + 8;
    var left = rect.left + window.scrollX;
    var maxLeft = window.scrollX + document.documentElement.clientWidth - popup.offsetWidth - 12;
    popup.style.top = top + "px";
    popup.style.left = Math.max(8, Math.min(left, maxLeft)) + "px";
  }

  function hide() {
    popup.hidden = true;
    current = null;
  }

  document.addEventListener("mouseover", function (e) {
    var link = e.target.closest && e.target.closest(".internal-link");
    if (!link || link === current) return;
    current = link;
    clearTimeout(showTimer);
    showTimer = setTimeout(function () { show(link); }, 150);
  });

  document.addEventListener("mouseout", function (e) {
    var link = e.target.closest && e.target.closest(".internal-link");
    if (!link) return;
    clearTimeout(showTimer);
    hide();
  });

  document.addEventListener("scroll", hide, { passive: true });
})();
