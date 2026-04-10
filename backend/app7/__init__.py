"""app7/__init__.py — Gemini AI Chatbot Blueprint"""
from flask import Blueprint

def create_app():
    from .routes import bp
    return bp
