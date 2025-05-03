document.addEventListener("DOMContentLoaded", function () {
    // 🚀 カテゴリーフォーム処理
    const categoryForm = document.getElementById("category-mater-form");
    if (categoryForm) {
        categoryForm.addEventListener("submit", function (event) {
            const clickedButton = document.activeElement;
            const category = categoryForm.querySelector('input[name="category"]').value.trim();

            if (!category) {
                alert("分類を入力してください！");
                event.preventDefault();
                return;
            }

            if (clickedButton.name === "form_add") {
                if (!confirm(`以下の内容で登録しますか？\n\n分類: ${category}`)) {
                    event.preventDefault();
                } else {
                    alert("登録しました！");
                }
            } else if (clickedButton.name === "form_delete") {
                if (!confirm(`「${category}」を本当に削除しますか？`)) {
                    event.preventDefault();
                } else {
                    alert("削除しました！");
                }
            }
        });
    }

    // 🚀 ユーザーフォーム処理
    const userForm = document.getElementById("user-master-form");
    if (userForm) {
        userForm.addEventListener("submit", function (event) {
            const clickedButton = document.activeElement;
            const user = userForm.querySelector('input[name="user"]').value.trim();

            if (!user) {
                alert("ユーザー名を入力してください！");
                event.preventDefault();
                return;
            }

            if (clickedButton.name === "form_add") {
                if (!confirm(`以下の内容で登録しますか？\n\nユーザー: ${user}`)) {
                    event.preventDefault();
                } else {
                    alert("登録しました！");
                }
            } else if (clickedButton.name === "form_delete") {
                if (!confirm(`「${user}」を本当に削除しますか？`)) {
                    event.preventDefault();
                } else {
                    alert("削除しました！");
                }
            }
        });
    }
});
