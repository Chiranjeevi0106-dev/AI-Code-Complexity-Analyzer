
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from analyzer import analyze_code, detect_language
from model import predict
from ai_debugger import ai_debug
from suggestions import get_suggestions
import os
import json
import shutil
from datetime import datetime
import graphviz
from pyvis.network import Network
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///analyses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='threading')

# Database Model
class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50))
    complexity = db.Column(db.String(20))
    features = db.Column(db.Text)  # JSON string
    suggestions = db.Column(db.Text)  # JSON string
    ai_debugger = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code[:100] + '...' if len(self.code) > 100 else self.code,
            'language': self.language,
            'complexity': self.complexity,
            'features': json.loads(self.features),
            'suggestions': json.loads(self.suggestions),
            'ai_debugger': self.ai_debugger,
            'timestamp': self.timestamp.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

# SocketIO event for real-time analysis
@socketio.on('analyze_code')
def handle_analyze(data):
    code = data.get('code', '')
    if not code.strip():
        emit('analysis_result', {'error': 'No code provided'})
        return

    try:
        features, lang = analyze_code(code)
        result = predict(features)
        tips = get_suggestions(features)
        ai_result = ai_debug(code, lang)

        # Save to database
        analysis = Analysis(
            code=code,
            language=lang,
            complexity=result,
            features=json.dumps({
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            }),
            suggestions=json.dumps(tips),
            ai_debugger=ai_result
        )
        db.session.add(analysis)
        db.session.commit()

        emit('analysis_result', {
            "success": True,
            "language": lang,
            "complexity": result,
            "suggestions": tips,
            "ai_debugger": ai_result,
            "features": {
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            },
            "analysis_id": analysis.id
        })
    except Exception as e:
        emit('analysis_result', {"success": False, "error": str(e)})


@app.route('/history')
def get_history():
    analyses = Analysis.query.order_by(Analysis.timestamp.desc()).limit(10).all()
    return jsonify([a.to_dict() for a in analyses])


@app.route('/history/<int:analysis_id>')
def get_analysis(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    data = analysis.to_dict()

    if isinstance(data.get('features'), str):
        data['features'] = json.loads(data['features'])
    if isinstance(data.get('suggestions'), str):
        data['suggestions'] = json.loads(data['suggestions'])

    return jsonify(data)


@app.route('/visualize/<int:analysis_id>')
def visualize(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    features = json.loads(analysis.features)

    if shutil.which('dot') is None:
        return jsonify({
            'success': False,
            'error': 'Graphviz executable not found. Install Graphviz and add it to PATH.'
        }), 500

    # Generate AST visualization (simplified)
    dot = graphviz.Digraph()
    dot.node('root', 'Code Analysis')
    dot.node('loc', f'LOC: {features["LOC"]}')
    dot.node('loops', f'Loops: {features["Loops"]}')
    dot.node('conditions', f'Conditions: {features["Conditions"]}')
    dot.node('complexity', f'Complexity: {features["Cyclomatic Complexity"]}')
    dot.edges([('root', 'loc'), ('root', 'loops'), ('root', 'conditions'), ('root', 'complexity')])
    
    # Save as PNG
    dot.render(f'static/viz_{analysis_id}', format='png', cleanup=True)
    return send_file(f'static/viz_{analysis_id}.png', mimetype='image/png')


@app.route('/export/<int:analysis_id>')
def export_pdf(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    features = json.loads(analysis.features)
    suggestions = json.loads(analysis.suggestions)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("Code Analysis Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Language: {analysis.language}", styles['Normal']))
    story.append(Paragraph(f"Complexity: {analysis.complexity}", styles['Normal']))
    story.append(Paragraph("Features:", styles['Heading2']))
    for key, value in features.items():
        story.append(Paragraph(f"{key}: {value}", styles['Normal']))
    story.append(Paragraph("Suggestions:", styles['Heading2']))
    for tip in suggestions:
        story.append(Paragraph(f"- {tip}", styles['Normal']))
    story.append(Paragraph("AI Debugger:", styles['Heading2']))
    story.append(Paragraph(analysis.ai_debugger, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'analysis_{analysis_id}.pdf', mimetype='application/pdf')


@app.route('/')
def home():
    return render_template("index.html")


# -----------------------------
# Paste Code Analyzer
# -----------------------------
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        code = request.json['code']

        # Analyze code
        features, lang = analyze_code(code)

        # ML prediction
        result = predict(features)

        # Suggestions
        tips = get_suggestions(features)

        # AI Debugger
        ai_result = ai_debug(code, lang)

        # Save to database
        analysis = Analysis(
            code=code,
            language=lang,
            complexity=result,
            features=json.dumps({
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            }),
            suggestions=json.dumps(tips),
            ai_debugger=ai_result
        )
        db.session.add(analysis)
        db.session.commit()

        return jsonify({
            "success": True,
            "language": lang,
            "complexity": result,
            "suggestions": tips,
            "ai_debugger": ai_result,
            "features": {
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            },
            "analysis_id": analysis.id
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# -----------------------------
# File Upload Analyzer
# -----------------------------
@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']

        if not file:
            return jsonify({
                "success": False,
                "error": "No file selected."
            })

        code = file.read().decode('utf-8')

        # Analyze code
        features, lang = analyze_code(code)

        # ML prediction
        result = predict(features)

        # Suggestions
        tips = get_suggestions(features)

        # AI Debugger
        try:
            ai_result = ai_debug(code, lang)
        except Exception as e:
            ai_result = "Debugger Error: " + str(e)

        # Save to database
        analysis = Analysis(
            code=code,
            language=lang,
            complexity=result,
            features=json.dumps({
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            }),
            suggestions=json.dumps(tips),
            ai_debugger=ai_result
        )
        db.session.add(analysis)
        db.session.commit()

        return jsonify({
            "success": True,
            "filename": file.filename,
            "language": lang,
            "complexity": result,
            "suggestions": tips,
            "ai_debugger": ai_result,
            "features": {
                "LOC": features[0],
                "Loops": features[1],
                "Conditions": features[2],
                "Cyclomatic Complexity": features[3]
            },
            "analysis_id": analysis.id
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# -----------------------------
# AI Debugger Route
# -----------------------------
@app.route('/ai-debug', methods=['POST'])
def ai_debug_route():
    try:
        code = request.json['code']
        lang = detect_language(code)

        result = ai_debug(code, lang)

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "result": "AI Debugger Error: " + str(e)
        })


# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

