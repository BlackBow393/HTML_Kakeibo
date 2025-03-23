document.addEventListener("DOMContentLoaded", function () {
    const expenseTable = document.getElementById("expense-table").getElementsByTagName("tbody")[0];
    const addRowBtn = document.getElementById("add-row");
    const totalAmountInput = document.getElementById("amount");

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
});
