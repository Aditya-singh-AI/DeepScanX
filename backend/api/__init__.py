"""api/__init__.py — REST API Blueprint"""
from flask import Blueprint

def create_app():
    from .routes import bp
    return bp
