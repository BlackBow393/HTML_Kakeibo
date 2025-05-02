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

    // 📌 JSON APIからデータ取得してテーブルを更新
    function fetchData() {
        fetch("/get_data")
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector(".data-table tbody");
                tableBody.innerHTML = ""; // 既存データをクリア

                data.forEach((expense, index) => {
                    const row = document.createElement("tr");
                    const amount = Number(expense[4]).toLocaleString();
                    row.innerHTML = `
                        <td>${expense[0]}</td>
                        <td>${expense[1]}</td>
                        <td>${expense[2]}</td>
                        <td>${expense[3]}</td>
                        <td id="amount-cell">${amount}</td>  <!-- 金額整形済み -->
                        <td>${expense[5]}</td>
                    `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => console.error("データ取得エラー:", error));
    }
    
    // 10秒ごとにデータを更新
    setInterval(fetchData, 10000);

    // 初回データ取得
    fetchData();

    fetch('/get_latest_date')
      .then(response => response.json())
      .then(data => {
        document.getElementById('last-updated').textContent =
          '最終更新日: ' + data.latest_date;
      })
      .catch(error => {
        console.error('データ取得エラー:', error);
      });
});
