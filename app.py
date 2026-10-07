from flask import Flask, render_template, request, jsonify, Response
import os
import core.static_analyzer as static_analyzer
from core.dynamic_profiler import GreenCodeProfiler
from core.ai_optimizer import GreenCodeAIOptimizer
import database

app = Flask(__name__)
database.init_db()

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), 'samples')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    code = data.get('code', '')
    project_name = data.get('project_name', 'Untitled Green Audit')
    language = data.get('language', 'python')

    if not code.strip():
        return jsonify({"error": "Please provide valid source code to analyze."}), 400

    # 1. Static Analysis on Original Code
    orig_static = static_analyzer.analyze_code_sustainability(code)

    # 2. Dynamic Profiling on Original Code
    orig_dynamic = GreenCodeProfiler.profile_code(code)

    # 3. AI Refactoring Optimization
    opt_result = GreenCodeAIOptimizer.optimize_code(code, orig_static["issues"])
    opt_code = opt_result["optimized_code"]

    # 4. Static & Dynamic Profiling on Optimized Code
    opt_static = static_analyzer.analyze_code_sustainability(opt_code)
    opt_dynamic = GreenCodeProfiler.profile_code(opt_code)

    # 5. Profile Comparison & Carbon Reduction Metrics
    comparison = GreenCodeProfiler.compare_profiles(orig_dynamic, opt_dynamic)

    # 6. Store in Database
    audit_id = database.save_audit(
        project_name=project_name,
        language=language,
        original_code=code,
        optimized_code=opt_code,
        orig_score=orig_static["eco_score"],
        opt_score=opt_static["eco_score"],
        orig_joules=orig_dynamic["energy_joules"],
        opt_joules=opt_dynamic["energy_joules"],
        carbon_saved_pct=comparison["carbon_reduced_pct"],
        speedup_factor=comparison["speedup_factor"],
        issue_count=orig_static["issue_count"]
    )

    return jsonify({
        "audit_id": audit_id,
        "project_name": project_name,
        "original_code": code,
        "optimized_code": opt_code,
        "original_static": orig_static,
        "optimized_static": opt_static,
        "original_dynamic": orig_dynamic,
        "optimized_dynamic": opt_dynamic,
        "transformations": opt_result["transformations"],
        "comparison": comparison
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    audits = database.get_all_audits(limit=15)
    stats = database.get_sustainability_stats()
    return jsonify({
        "audits": audits,
        "stats": stats
    })

@app.route('/api/audit/<int:audit_id>', methods=['DELETE'])
def delete_audit(audit_id):
    success = database.delete_audit(audit_id)
    if success:
        return jsonify({"message": "Audit record deleted successfully.", "success": True})
    return jsonify({"error": "Audit record not found."}), 404

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    database.clear_all_audits()
    return jsonify({"message": "All audit history cleared successfully.", "success": True})

@app.route('/api/sample/<sample_name>', methods=['GET'])
def get_sample(sample_name):
    filename = f"sample_{sample_name}.py"
    file_path = os.path.join(SAMPLES_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"code": content, "sample": sample_name})
    return jsonify({"error": "Sample script not found."}), 404

@app.route('/api/export/<int:audit_id>', methods=['GET'])
def export_audit(audit_id):
    audit = database.get_audit_by_id(audit_id)
    if not audit:
        return jsonify({"error": "Audit record not found."}), 404

    report_md = f"""# GreenCode AI - Sustainability Audit Report
**Project Name:** {audit['project_name']}
**Audit ID:** #{audit['id']}
**Date:** {audit['created_at']}
**Language:** {audit['language'].upper()}

---

## 1. Executive Summary
- **Original Eco-Score:** {audit['original_eco_score']} / 100
- **Optimized Eco-Score:** {audit['optimized_eco_score']} / 100
- **Carbon Emissions Reduced:** {audit['carbon_saved_pct']}%
- **Execution Speedup:** {audit['speedup_factor']}x Faster
- **Energy Saved:** {round(audit['original_joules'] - audit['optimized_joules'], 6)} Joules

---

## 2. Energy Consumption Comparison
| Metric | Original Code | Green AI Optimized | Improvement |
| :--- | :--- | :--- | :--- |
| **Energy Consumed** | {audit['original_joules']} Joules | {audit['optimized_joules']} Joules | {round(audit['original_joules'] - audit['optimized_joules'], 6)} J saved |
| **Eco Score** | {audit['original_eco_score']} / 100 | {audit['optimized_eco_score']} / 100 | +{audit['optimized_eco_score'] - audit['original_eco_score']} pts |
| **Issue Count** | {audit['issue_count']} issues | 0 issues | Cleaned |

---

## 3. Original Code
```python
{audit['original_code']}
```

---

## 4. Eco-Optimized Green Code
```python
{audit['optimized_code']}
```

*Generated automatically by GreenCode AI Sustainable Code Engine.*
"""
    return Response(report_md, mimetype='text/markdown', headers={"Content-Disposition": f"attachment;filename=GreenCode_Audit_{audit_id}.md"})

if __name__ == '__main__':
    print("Starting GreenCode AI Sustainable Code Server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
