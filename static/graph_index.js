document.addEventListener("DOMContentLoaded", () => {
    const year = document.getElementById("year").value;
    const category = 'all';  // 'all' を設定
    const user = 'all';      // 'all' を設定
  
    // 月別支出グラフ（ユーザー別）を描画する関数
    function loadUserChart(year, category, user) {
      const params = new URLSearchParams({ year, category, user });
  
      fetch(`/api/monthly_expense_by_user?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
          const months = Array.from({ length: 12 }, (_, i) => i + 1);
          const traces = [];
          const monthlyTotals = Array(12).fill(0);
  
          // 🔥 ユーザーごとの色定義
          const userColors = {
            'タクミ': 'steelblue',
            'ミナヨ': 'coral',
            // 他のユーザーを追加する場合はここに
          };
  
          data.forEach(item => {
            // タクミの場合、支出額をマイナスに変更
            const values = months.map(m => {
              const idx = item.months.indexOf(m);
              let value = idx !== -1 ? item.amounts[idx] : 0;
              if (item.user === 'タクミ') {
                value = -value;  // タクミの支出額をマイナスに
              }
              monthlyTotals[m - 1] += value;
              return value;
            });
  
            traces.push({
              x: months.map(m => `${m}月`),
              y: values,
              name: item.user,
              type: 'bar',
              marker: { color: userColors[item.user] || 'gray' },
              hovertemplate: '%{x}<br>%{y:,}円<extra>' + item.user + '</extra>'
            });
          });
  
          const layout = {
            barmode: 'relative',
            yaxis: {
              title: '支出金額（円）',
              tickformat: ',d'
            },
            margin: { t: 40 },
            legend: {
              orientation: 'h',
              y: 1.15,
              x: 0.5,
              xanchor: 'center',
              yanchor: 'bottom',
              font: {
                size: 12
              }
            }
          };
  
          Plotly.newPlot('interactive-user-chart', traces, layout, { responsive: true });
        })
        .catch(err => {
          console.error("ユーザー別支出グラフの取得エラー:", err);
          document.getElementById("interactive-user-chart").innerHTML = "データの取得に失敗しました。";
        });
    }

    // 月別支出グラフ（食費と外食と生活用品のみ）を描画する関数
    function loadLifeCostChart(year, category, user) {
      const params = new URLSearchParams({ year, category, user });
    
      fetch(`/api/monthly_lifecost_by_user?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
          // 月と合計金額を取得
          const months = data.months || [];
          const totals = data.totals || [];
    
          // 1～12月の月の配列を定義
          const allMonths = Array.from({ length: 12 }, (_, i) => `${i + 1}月`);
          const allTotals = allMonths.map((month, idx) => {
            // データがない月には0を設定
            const monthIndex = months.indexOf(idx + 1);
            return monthIndex !== -1 ? totals[monthIndex] : 0;
          });
    
          const trace = {
            x: allMonths, // 月は1～12月
            y: allTotals, // 合計金額
            type: 'scatter',
            mode: 'lines+markers+text',
            name: '生活費合計',
            text: allTotals.map(v => `${v.toLocaleString()}円`),
            textposition: 'top center',
            line: { color: 'mediumseagreen' },
            marker: { size: 6 }
          };
    
          // layout の設定
          const layout = {
            yaxis: {
              title: '支出金額（円）',
              tickformat: ',d'
            },
            xaxis: {
              title: '月',
              tickangle: -45
            },
            margin: { t: 50 },
            showlegend: false
          };
    
          Plotly.newPlot('lifecost-line-chart', [trace], layout, { responsive: true });
        })
        .catch(err => {
          console.error("生活費折れ線グラフの取得エラー:", err);
          document.getElementById("lifecost-line-chart").innerHTML = "データの取得に失敗しました。";
        });
    }
  
    // 初期化処理：ページ読み込み時に実行
    const page = document.body.dataset.page;
    if (page === "home") {
      loadUserChart(year, category, user);
      loadLifeCostChart(year, category, user);
  
      // リサイズ対応
      window.addEventListener("resize", () => {
        const ids = ["interactive-user-chart","lifecost-line-chart"];
        ids.forEach(id => {
          const el = document.getElementById(id);
          if (el && el.data) {
            Plotly.Plots.resize(el);
          }
        });
      });
    }
  });
  