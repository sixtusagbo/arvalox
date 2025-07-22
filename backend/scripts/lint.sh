#!/bin/bash

# Arvalox Backend Linting and Formatting Script

echo "🔍 Running Ruff linter..."
ruff check . --fix

echo "🎨 Running Ruff formatter..."
ruff format .

echo "✅ Linting and formatting complete!"
