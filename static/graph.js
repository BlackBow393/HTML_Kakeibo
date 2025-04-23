document.addEventListener("DOMContentLoaded", () => {
    const year = document.getElementById("year").value;
    const category = document.getElementById("category").value;
    const user = document.getElementById("user").value;
  
    // 月別支出グラフ（カテゴリ別）を描画する関数
    function loadCategoryChart(year, category, user) {
        const params = new URLSearchParams({ year, category, user });
      
        fetch(`/api/monthly_expense_by_category?${params.toString()}`)
          .then(res => res.json())
          .then(data => {
            const months = Array.from({ length: 12 }, (_, i) => i + 1);
            const traces = [];
      
            // 各月の合計額を初期化（0でスタート）
            const monthlyTotals = Array(12).fill(0);
      
            data.forEach(item => {
              const values = months.map(m => {
                const idx = item.months.indexOf(m);
                const value = idx !== -1 ? item.amounts[idx] : 0;
                // 合計値に加算
                monthlyTotals[m - 1] += value;
                return value;
              });
      
              traces.push({
                x: months.map(m => `${m}月`),
                y: values,
                name: item.category,
                type: 'bar',
                hovertemplate: '%{x}<br>%{y:,}円<extra>' + item.category + '</extra>'
              });
            });
      
            // 合計ラベル（棒の上に表示）
            const totalLabels = {
              x: months.map(m => `${m}月`),
              y: monthlyTotals,
              text: monthlyTotals.map(val => `${val.toLocaleString()}円`),
              mode: 'text',
              textposition: 'top center',
              showlegend: false,
              type: 'scatter',
              hoverinfo: 'skip',  // ホバーでは表示しない
            };
      
            const layout = {
              barmode: 'stack',
              xaxis: { title: '月' },
              yaxis: { 
                title: '支出金額（円）' ,
                tickformat: ',d'
                },
              margin: { t: 40 },
            };
      
            Plotly.newPlot('interactive-category-chart', [...traces, totalLabels], layout);
          });
      }
      
      function loadPieChart(year, category, user) {
        const params = new URLSearchParams({ year, category, user });
    
        fetch(`/api/pie_data_by_category?${params.toString()}`)
            .then(res => res.json())
            .then(data => {
                if (!data || data.length === 0) {
                    document.getElementById("interactive-pie-chart").innerHTML = "データがありません。";
                    return;
                }
    
                // 🔁 金額順にソート（降順）
                data.sort((a, b) => b[1] - a[1]);
    
                const labels = data.map(item => item[0]);      // カテゴリ名
                const values = data.map(item => item[1]);      // 金額
                //const percentages = data.map(item => item[2]); // 割合（%）
    
                const trace = {
                    labels: labels,
                    values: values,
                    type: 'pie',
                    textinfo: 'label+percent',
                    hovertemplate: '%{label}<br>%{value:,}円 (%{percent})<extra></extra>',
                    sort: false,  // ← 自分で並べた順に表示
                    direction: 'clockwise',  // ← 時計回り
                };
    
                const layout = {
                    
                };
    
                Plotly.newPlot('interactive-pie-chart', [trace], layout);
            })
            .catch(err => {
                console.error("円グラフデータの取得エラー:", err);
            });
    }
    
      
  
    // 初期化処理：ページ読み込み時に実行
    const page = document.body.dataset.page;
    if (page === "analysis") {
      loadCategoryChart(year, category, user);
      loadPieChart(year, category, user);
    }
  });
  