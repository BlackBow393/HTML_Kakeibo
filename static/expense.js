document.addEventListener("DOMContentLoaded", function () {
    const expenseTable = document.getElementById("expense-table").getElementsByTagName("tbody")[0];
    const addRowBtn = document.getElementById("add-row");
    const totalAmountInput = document.getElementById("amount");
    const expenseForm = document.getElementById("expense-form");
    const deleteButton = document.getElementById("data-delete");

    // 🔥 金額の合計を計算し、合計金額欄に反映する
    function updateTotalAmount() {
        let total = 0;
        document.querySelectorAll(".expense-input").forEach(input => {
            total += Number(input.value) || 0;
        });
        totalAmountInput.value = total; // 合計金額を反映
    }

    // 🔥 行を追加する関数
    function addRow() {
        let newRow = document.createElement("tr");

        // 番号セル
        let indexCell = document.createElement("td");
        indexCell.textContent = expenseTable.rows.length + 1;

        // 金額セル（input + 削除ボタン）
        let amountCell = document.createElement("td");
        amountCell.classList.add("expense-cell");

        let amountInput = document.createElement("input");
        amountInput.type = "number";
        amountInput.classList.add("expense-input");
        amountInput.min = "0";
        amountInput.value = "0";

        amountInput.addEventListener("input", updateTotalAmount); // 入力変更時に合計を更新

        let deleteButton = document.createElement("button");
        deleteButton.classList.add("delete-btn");
        deleteButton.textContent = "✖";

        deleteButton.addEventListener("click", function () {
            newRow.remove();
            updateTotalAmount(); // 削除後に合計を更新
        });

        // 金額セルに追加
        amountCell.appendChild(amountInput);
        amountCell.appendChild(deleteButton);

        // 行にセルを追加
        newRow.appendChild(indexCell);
        newRow.appendChild(amountCell);

        // テーブルに行を追加
        expenseTable.appendChild(newRow);
    }

    // 🔥 初期行の金額入力フォームにもイベントを追加
    document.querySelectorAll(".expense-input").forEach(input => {
        input.addEventListener("input", updateTotalAmount);
    });

    // 🔥 行追加ボタンのイベント設定
    addRowBtn.addEventListener("click", addRow);

    // 🚀 登録ボタンに確認ポップアップを追加
    expenseForm.addEventListener("submit", function (event) {
        event.preventDefault(); // 🔍 デフォルト送信を防ぐ

        const year = document.getElementById("year").value;
        const month = document.getElementById("month").value;
        const category = document.getElementById("category").value;
        const amount = document.getElementById("amount").value;
        const user = document.getElementById("user").value;

        // 🔍 入力チェック
        if (!year || !month || !category || !amount || !user) {
            alert("入力項目が不足しています！");
            return;
        }

        // 🔍 既存データがあるかチェック
        fetch(`/get_data`)
            .then(response => response.json())
            .then(data => {
                let existingData = data.find(expense =>
                    expense[1] == year &&
                    expense[2] == month &&
                    expense[3] == category &&
                    expense[5] == user
                );

                let confirmMessage;
                if (existingData) {
                    // 既に登録されている場合の警告
                    alert("既に登録されているデータがあります。上書きします。");

                    confirmMessage = `以下の内容で上書き登録しますか？\n\n`
                        + `年: ${year}\n`
                        + `月: ${month}\n`
                        + `分類: ${category}\n`
                        + `合計金額: ${amount} 円\n`
                        + `ユーザー: ${user}`;
                } else {
                    // 新規登録のメッセージ
                    confirmMessage = `以下の内容で登録しますか？\n\n`
                        + `年: ${year}\n`
                        + `月: ${month}\n`
                        + `分類: ${category}\n`
                        + `合計金額: ${amount} 円\n`
                        + `ユーザー: ${user}`;
                }

                if (confirm(confirmMessage)) {
                    alert(existingData ? "上書き登録完了しました！" : "登録完了しました！"); // 🎉 完了メッセージ
                    expenseForm.submit(); // フォーム送信
                }
            })
            .catch(error => {
                console.error("データ取得エラー:", error);
                alert("データの取得に失敗しました。");
            });
    });

    // 🚀 削除ボタンのクリックイベントを追加
    if (deleteButton) {
        deleteButton.addEventListener("click", function () {
            const year = document.getElementById("year").value;
            const month = document.getElementById("month").value;
            const category = document.getElementById("category").value;
            const user = document.getElementById("user").value;

            // 削除確認ポップアップ
            const confirmMessage = `以下のデータを削除しますか？\n\n`
                + `年: ${year}\n`
                + `月: ${month}\n`
                + `分類: ${category}\n`
                + `ユーザー: ${user}`;

            if (!confirm(confirmMessage)) {
                return; // キャンセルされたら処理を中断
            }

            // サーバーに削除リクエストを送信
            fetch("/delete", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    year: year,
                    month: month,
                    category: category,
                    user: user
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("データを削除しました。");
                    location.reload(); // 成功時にページをリロード
                } else {
                    alert("削除に失敗しました。");
                }
            })
            .catch(error => {
                console.error("削除エラー:", error);
                alert("エラーが発生しました。");
            });
        });
    }
});
