"""app6/__init__.py — Admin Panel Blueprint"""
from flask import Blueprint

def create_app():
    from .routes import bp
    return bp
