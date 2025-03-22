document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    console.log("menuToggle:", menuToggle);
    console.log("sidebar:", sidebar);

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", function () {
            sidebar.classList.toggle("active");
            console.log("Sidebar toggled!");
        });
    } else {
        console.error("menuToggle または sidebar が見つかりません！");
    }
});