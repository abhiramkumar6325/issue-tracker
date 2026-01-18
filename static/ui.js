function toggleTheme(){
    let body = document.body;
    let theme = body.getAttribute("data-theme");
    let newTheme = theme === "light" ? "dark" : "light";
    body.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
}

function toggleSidebar(){
    document.getElementById("sidebar").classList.toggle("collapsed");
}

(function(){
    let t = localStorage.getItem("theme");
    if(t){
        document.body.setAttribute("data-theme", t);
    }
})();
