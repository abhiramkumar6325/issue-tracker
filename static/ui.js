const sidebar = document.getElementById("sidebar");

/* ================================
   THEME HANDLING
================================ */

function applyTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
}

function toggleTheme() {
    const current = document.body.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    applyTheme(next);
}

/* ================================
   SIDEBAR HANDLING
================================ */

function setSidebarCollapsed(collapsed) {
    if (collapsed) {
        sidebar.classList.add("collapsed");
        localStorage.setItem("sidebar", "collapsed");
    } else {
        sidebar.classList.remove("collapsed");
        localStorage.setItem("sidebar", "expanded");
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("mobileOverlay");

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle("open");
        overlay.classList.toggle("show");
    } else {
        sidebar.classList.toggle("collapsed");
    }
}


/* ================================
   INIT ON LOAD
================================ */

(function initUI() {
    const savedTheme = localStorage.getItem("theme") || "light";
    applyTheme(savedTheme);

    const sidebarState = localStorage.getItem("sidebar");
    if (sidebarState === "collapsed") {
        setSidebarCollapsed(true);
    }

    // Auto collapse on small screens
    if (window.innerWidth < 900) {
        setSidebarCollapsed(true);
    }
})();
