document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    menuToggle.addEventListener("click", function () {
        sidebar.classList.toggle("active");

        // 🔥 ボタンのアイコンを切り替え
        if (sidebar.classList.contains("active")) {
            menuToggle.innerHTML = "&times;"; // ✖マークに変更
        } else {
            menuToggle.innerHTML = "&#9776;"; // ☰マークに戻す
        }
    });
});
