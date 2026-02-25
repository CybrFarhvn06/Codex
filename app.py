import json
import os
import re
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

from research_engine import ResearchService


db = SQLAlchemy()
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    institution = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    research_logs = db.relationship("ResearchLog", backref="student", lazy=True, cascade="all, delete-orphan")


class ResearchLog(db.Model):
    __tablename__ = "research_logs"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    topic = db.Column(db.String(300), nullable=False)
    query = db.Column(db.Text, nullable=False)
    report_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def _validate_research_payload(payload: dict) -> tuple[bool, str]:
    required = ["student_name", "student_email", "topic", "query"]
    for key in required:
        if not payload.get(key, "").strip():
            return False, f"{key} is required"

    if not EMAIL_REGEX.match(payload.get("student_email", "").strip().lower()):
        return False, "student_email format is invalid"

    if len(payload.get("topic", "")) > 300:
        return False, "topic must be <= 300 characters"

    if len(payload.get("query", "")) > 5000:
        return False, "query must be <= 5000 characters"

    return True, ""


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///research_assistant.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/research")
    def run_research():
        payload = request.get_json(silent=True) or {}
        is_valid, error = _validate_research_payload(payload)
        if not is_valid:
            return jsonify({"error": error}), 400

        student_name = payload.get("student_name", "").strip()
        student_email = payload.get("student_email", "").strip().lower()
        institution = payload.get("institution", "").strip()[:200]
        topic = payload.get("topic", "").strip()
        query = payload.get("query", "").strip()

        student = Student.query.filter_by(email=student_email).first()
        if not student:
            student = Student(name=student_name, email=student_email, institution=institution)
            db.session.add(student)
            db.session.flush()
        else:
            student.name = student_name
            student.institution = institution

        report = ResearchService.generate_report(topic=topic, query=query)

        research_log = ResearchLog(student_id=student.id, topic=topic, query=query, report_json=json.dumps(report))
        db.session.add(research_log)
        db.session.commit()

        return jsonify(
            {
                "message": "Research report generated successfully.",
                "research_id": research_log.id,
                "student_id": student.id,
                "report": report,
            }
        )

    @app.get("/api/history/<int:student_id>")
    def get_history(student_id: int):
        student = Student.query.get_or_404(student_id)
        logs = (
            ResearchLog.query.filter_by(student_id=student_id)
            .order_by(ResearchLog.created_at.desc())
            .all()
        )

        return jsonify(
            {
                "student": {
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                    "institution": student.institution,
                },
                "history": [
                    {
                        "research_id": log.id,
                        "topic": log.topic,
                        "query": log.query,
                        "created_at": log.created_at.isoformat(),
                    }
                    for log in logs
                ],
            }
        )

    @app.get("/api/history/detail/<int:research_id>")
    def get_history_detail(research_id: int):
        log = ResearchLog.query.get_or_404(research_id)
        return jsonify(
            {
                "research_id": log.id,
                "student_id": log.student_id,
                "topic": log.topic,
                "query": log.query,
                "created_at": log.created_at.isoformat(),
                "report": json.loads(log.report_json),
            }
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
