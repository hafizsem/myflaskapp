from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import plotly.graph_objects as go
import json

# ----------------------------
# Load and prepare dataset
# ----------------------------
cols = ["Company Name", "Organisation Type", "Industry",
        "AI Literacy", "AI Talent", "Management Support",
        "Employee Acceptance of AI", "Experimentation Culture",
        "AI Governance", "AI Risk Control", "Business Use Case",
        "Data Quality", "Reference Data", "ML Infrastructure", "Data Infrastructure"]

# ✅ Use relative path (make sure AIRI_25082025_10am.xlsx is in same folder as app.py)
df = pd.read_excel("AIRI_25082025_10am.xlsx")
df = df[cols]

df_long = df.melt(
    id_vars=["Company Name", "Organisation Type", "Industry"],
    var_name="Dimension",
    value_name="Score"
)

dimension_order = [c for c in cols if c not in ["Company Name", "Organisation Type", "Industry"]]

df_industry = df_long.groupby(["Industry", "Dimension"])["Score"].mean().reset_index()
df_type_avg_all = df_long.groupby(["Organisation Type", "Dimension"])["Score"].mean().reset_index()

# ----------------------------
# Color scheme
# ----------------------------
COLOR_COMPANY = "#FF6B6B"
COLOR_INDUSTRY = "#FFD93D"
COLOR_TYPE = "#6BCB77"
COLOR_OVERALL = "#4D96FF"

# ----------------------------
# Chart 1: Selected Company vs Industry Avg vs Company Type Avg
# ----------------------------
def chart_industry_vs_type(company):
    df_company = df_long[df_long["Company Name"] == company]
    if df_company.empty:
        return None

    industry = df_company["Industry"].iloc[0]
    company_type = df_company["Organisation Type"].iloc[0]

    df_industry_avg = df_long[df_long["Industry"] == industry].groupby("Dimension")["Score"].mean().reset_index()
    df_type_avg = df_long[df_long["Organisation Type"] == company_type].groupby("Dimension")["Score"].mean().reset_index()

    df_company = df_company.set_index("Dimension").reindex(dimension_order).reset_index()
    df_industry_avg = df_industry_avg.set_index("Dimension").reindex(dimension_order).reset_index()
    df_type_avg = df_type_avg.set_index("Dimension").reindex(dimension_order).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_company["Dimension"],
        y=df_company["Score"],
        name=company,
        marker_color=COLOR_COMPANY,
        text=df_company["Score"],
        textposition="outside"
    ))
    fig.add_trace(go.Scatter(
        x=df_industry_avg["Dimension"],
        y=df_industry_avg["Score"],
        mode="lines+markers+text",
        text=df_industry_avg["Score"].round(2),
        textposition="top center",
        name=f"Industry Avg ({industry})",
        line=dict(color=COLOR_INDUSTRY, width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=df_type_avg["Dimension"],
        y=df_type_avg["Score"],
        mode="lines+markers+text",
        text=df_type_avg["Score"].round(2),
        textposition="bottom center",
        name=f"Company Type Avg ({company_type})",
        line=dict(color=COLOR_TYPE, width=3, dash="dash"),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=f"AI Readiness Comparison - {company} vs {industry} & {company_type}",
        xaxis_title="Dimension",
        yaxis_title="Average Scores",
        template="plotly_white",
        autosize=True,
        height=700,
        margin=dict(l=60, r=60, t=80, b=140),
        xaxis=dict(
            tickangle=-15,
            categoryorder="array",
            categoryarray=dimension_order
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        yaxis=dict(
            range=[0, 1],
            tickvals=[0.2, 0.4, 0.6, 0.8, 1]
        )
    )

    return fig

# ----------------------------
# Chart 2: Industry Comparison
# ----------------------------
def chart_all_industries(company):
    df_company = df[df["Company Name"] == company]
    if df_company.empty:
        return None

    industry_selected = df_company["Industry"].iloc[0]
    fig = go.Figure()
    
    for industry in sorted(df_industry["Industry"].unique()):
        df_temp = df_industry[df_industry["Industry"] == industry].set_index("Dimension").reindex(dimension_order).reset_index()
        if industry == industry_selected:
            fig.add_trace(go.Scatter(
                x=df_temp["Dimension"],
                y=df_temp["Score"],
                mode="lines+markers+text",
                name=f"{industry} (highlighted)",
                text=df_temp["Score"].round(2),
                textposition="top center",
                line=dict(color=COLOR_INDUSTRY, width=4),
                marker=dict(size=8, color=COLOR_INDUSTRY),
                showlegend=True
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df_temp["Dimension"],
                y=df_temp["Score"],
                mode="lines+markers",
                name=industry,
                line=dict(color="lightgrey", width=1),
                marker=dict(size=5, color="lightgrey"),
                opacity=0.5,
                showlegend=False
            ))

    df_base = df_long.groupby("Dimension")["Score"].mean().reset_index()
    df_base = df_base.set_index("Dimension").reindex(dimension_order).reset_index()
    fig.add_trace(go.Scatter(
        x=df_base["Dimension"],
        y=df_base["Score"],
        mode="lines+markers+text",
        text=df_base["Score"].round(2).astype(str),
        textposition="bottom center",
        name="Overall Baseline (All Companies)",
        line=dict(color=COLOR_OVERALL, width=3, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
        showlegend=True
    ))

    fig.update_layout(
        title=f"Industry Comparison (Highlight: {industry_selected})",
        xaxis_title="Dimension",
        yaxis_title="Average Score",
        template="plotly_white",
        autosize=True,
        height=700,
        margin=dict(l=60, r=60, t=80, b=140),
        xaxis=dict(
            tickangle=-15,
            categoryorder="array",
            categoryarray=dimension_order,
            title=dict(font=dict(size=12)),
            tickfont=dict(size=8)
        ),
        yaxis=dict(
            range=[0, 1],
            tickvals=[0.2, 0.4, 0.6, 0.8, 1]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        )
    )
    return fig

# ----------------------------
# Chart 3: Company Type Comparison
# ----------------------------
def chart_all_company_types(company):
    df_company = df[df["Company Name"] == company]
    if df_company.empty:
        return None

    type_selected = df_company["Organisation Type"].iloc[0]
    fig = go.Figure()
    
    for ctype in sorted(df_type_avg_all["Organisation Type"].unique()):
        df_temp = df_type_avg_all[df_type_avg_all["Organisation Type"] == ctype].set_index("Dimension").reindex(dimension_order).reset_index()
        if ctype == type_selected:
            fig.add_trace(go.Scatter(
                x=df_temp["Dimension"],
                y=df_temp["Score"],
                mode="lines+markers+text",
                name=f"{ctype} (highlighted)",
                text=df_temp["Score"].round(2),
                textposition="top center",
                line=dict(color=COLOR_TYPE, width=4),
                marker=dict(size=10, color=COLOR_TYPE),
                showlegend=True
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df_temp["Dimension"],
                y=df_temp["Score"],
                mode="lines+markers",
                name=ctype,
                line=dict(color="lightgrey", width=1),
                marker=dict(size=5, color="lightgrey"),
                opacity=0.5,
                showlegend=False
            ))

    df_base = df_long.groupby("Dimension")["Score"].mean().reset_index()
    df_base = df_base.set_index("Dimension").reindex(dimension_order).reset_index()
    fig.add_trace(go.Scatter(
        x=df_base["Dimension"],
        y=df_base["Score"],
        mode="lines+markers+text",
        text=df_base["Score"].round(2).astype(str),
        textposition="bottom center",
        name="Overall Baseline (All Companies)",
        line=dict(color=COLOR_OVERALL, width=3, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
        showlegend=True
    ))

    fig.update_layout(
        title=f"Company Type Comparison (Highlight: {type_selected})",
        xaxis_title="Dimension",
        yaxis_title="Average Score",
        template="plotly_white",
        autosize=True,
        height=700,
        margin=dict(l=60, r=60, t=80, b=140),
        xaxis=dict(
            tickangle=-15,
            categoryorder="array",
            categoryarray=dimension_order,
            title=dict(font=dict(size=12)),
            tickfont=dict(size=8)
        ),
        yaxis=dict(
            range=[0, 1],
            tickvals=[0.2, 0.4, 0.6, 0.8, 1]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        )
    )
    return fig

# ----------------------------
# Flask App
# ----------------------------
app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AIRI Scoring Organisational Profile Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #f5f7fa; color: #333; }
        .container { max-width: 1400px; margin: 30px auto; padding: 20px; }
        h2 { text-align: center; margin-bottom: 30px; font-weight: 600; color: #222; }
        .selector { text-align: center; margin-bottom: 30px; }
        select { padding: 8px 12px; font-size: 14px; border-radius: 6px; border: 1px solid #ccc; min-width: 280px; background: #fff; }
        .chart-row { 
            display: flex; 
            gap: 20px; 
            justify-content: space-between; 
            margin-top: 40px; 
        }
        .chart-card { 
            background: #fff; 
            border-radius: 12px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.05); 
            padding: 20px; 
            flex: 1; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>AIRI Scoring Organisational Profile Dashboard</h2>
        <div class="selector">
            <label for="company"><strong>Select Company:</strong></label>
            <select id="company" onchange="updateCharts()">
                {% for c in companies %}
                    <option value="{{c}}">{{c}}</option>
                {% endfor %}
            </select>
        </div>

        <div class="chart-card"><div id="chart1"></div></div>
        <div class="chart-row">
            <div class="chart-card"><div id="chart2"></div></div>
            <div class="chart-card"><div id="chart3"></div></div>
        </div>
    </div>

<script>
function updateCharts() {
    const company = document.getElementById("company").value;
    fetch(`/charts?company=${encodeURIComponent(company)}`)
      .then(res => res.json())
      .then(data => {
          Plotly.newPlot("chart1", data.chart1.data, data.chart1.layout, {responsive:true});
          Plotly.newPlot("chart2", data.chart2.data, data.chart2.layout, {responsive:true});
          Plotly.newPlot("chart3", data.chart3.data, data.chart3.layout, {responsive:true});
      });
}
updateCharts();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    companies = sorted(df["Company Name"].unique())
    return render_template_string(TEMPLATE, companies=companies)

@app.route("/charts")
def charts():
    company = request.args.get("company")
    fig1 = chart_industry_vs_type(company)
    fig2 = chart_all_industries(company)
    fig3 = chart_all_company_types(company)
    return jsonify({
        "chart1": json.loads(fig1.to_json()) if fig1 else {},
        "chart2": json.loads(fig2.to_json()) if fig2 else {},
        "chart3": json.loads(fig3.to_json()) if fig3 else {}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
