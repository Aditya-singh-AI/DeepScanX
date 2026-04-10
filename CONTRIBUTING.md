# 🤝 Contributing to DeepScanX AI

Thank you for your interest in contributing to DeepScanX AI! We welcome contributions from the community to help improve this project. This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [How to Contribute](#-how-to-contribute)
- [Development Setup](#-development-setup)
- [Making Changes](#-making-changes)
- [Submitting Pull Requests](#-submitting-pull-requests)
- [Coding Standards](#-coding-standards)
- [Testing](#-testing)
- [Reporting Bugs](#-reporting-bugs)
- [Suggesting Features](#-suggesting-features)

---

## 🎯 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the development team.

---

## 🚀 How to Contribute

### Ways to Contribute:
1. **Report Bugs** — Found an issue? Let us know!
2. **Suggest Features** — Have an idea? We'd love to hear it
3. **Improve Documentation** — Help make docs clearer and more helpful
4. **Add New Cancer Models** — Implement new diagnostic modules
5. **Performance Optimization** — Speed up inference or reduce memory usage
6. **UI/UX Improvements** — Enhance the user interface
7. **Test Coverage** — Add tests for better code reliability

---

## 💻 Development Setup

### 1. Fork the Repository
```bash
# Go to https://github.com/Aditya-singh-ai/DeepScanX-AI
# Click the "Fork" button in the top-right corner
```

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR-USERNAME/DeepScanX-AI.git
cd "DeepScanX AI"
```

### 3. Add Upstream Remote
```bash
git remote add upstream https://github.com/Aditya-singh-ai/DeepScanX-AI.git
```

### 4. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix-name
```

### 5. Setup Development Environment

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd ../frontend
npm install
```

---

## ✏️ Making Changes

### Backend Changes

1. **Add/Update Models:**
   - Place model files in appropriate app directories (e.g., `backend/app4/`)
   - Update routes in `routes.py`
   - Add utilities in `backend/utils/`

2. **Code Style:**
   - Follow PEP 8 guidelines
   - Use meaningful variable names
   - Add docstrings to functions
   - Keep functions concise and focused

3. **Example:**
```python
def analyze_image(image_path, model_name):
    """
    Analyze a medical image and return predictions.
    
    Args:
        image_path (str): Path to the medical image
        model_name (str): Name of the model to use
        
    Returns:
        dict: Prediction results with confidence scores
    """
    # Implementation here
    pass
```

### Frontend Changes

1. **Component Structure:**
   - Create reusable components in `src/components/`
   - Use React Hooks for state management
   - Keep components focused on a single responsibility

2. **Styling:**
   - Use CSS modules when possible
   - Follow BEM (Block Element Modifier) naming convention
   - Ensure responsive design

3. **Example Component:**
```jsx
import React, { useState } from 'react';
import './AnalysisCard.css';

export const AnalysisCard = ({ data, onSubmit }) => {
  const [loading, setLoading] = useState(false);
  
  return (
    <div className="analysis-card">
      {/* Component JSX */}
    </div>
  );
};
```

---

## 📤 Submitting Pull Requests

### Before Submitting:
1. **Sync with main branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Test your changes:**
   ```bash
   # Backend tests
   cd backend
   python -m pytest
   
   # Frontend tests
   cd ../frontend
   npm test
   ```

3. **Check code quality:**
   ```bash
   # Python lint (if setup)
   pylint backend/
   
   # Frontend lint
   npm run lint
   ```

### Creating a PR:

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request:**
   - Go to https://github.com/Aditya-singh-ai/DeepScanX-AI/pulls
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

3. **PR Description Template:**
   ```markdown
   ## Description
   Brief description of what this PR does.
   
   ## Related Issue
   Closes #[issue number]
   
   ## Changes Made
   - Change 1
   - Change 2
   - Change 3
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   
   ## Testing
   How was this tested? Include steps to reproduce.
   
   ## Screenshots (if applicable)
   Add screenshots or GIFs demonstrating the change.
   ```

---

## 📏 Coding Standards

### Python (Backend)

```python
# Good practices
import os
from utils.helpers import process_image

class ImageAnalyzer:
    """Analyzes medical images using deep learning models."""
    
    def __init__(self, model_path):
        self.model = self.load_model(model_path)
    
    def analyze(self, image):
        """Analyze image and return predictions."""
        preprocessed = self.preprocess(image)
        predictions = self.model.predict(preprocessed)
        return self.postprocess(predictions)
```

### JavaScript/React (Frontend)

```jsx
// Good practices
import React from 'react';
import { useEffect, useState } from 'react';
import api from '../api/client';

export const AnalysisPage = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    // Component initialization
  }, []);
  
  return (
    <div className="analysis-page">
      {/* JSX content */}
    </div>
  );
};
```

---

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

### Manual Testing Checklist
- [ ] Feature works as expected
- [ ] No console errors or warnings
- [ ] Responsive on mobile devices
- [ ] Works in Chrome, Firefox, Safari
- [ ] API responses handled correctly

---

## 🐛 Reporting Bugs

### How to Report:
1. **Check existing issues** — Don't report duplicates
2. **Be specific** — Include clear, reproducible steps
3. **Include environment** — OS, Python version, Node version
4. **Provide logs** — Include error messages and stack traces

### Bug Report Template:
```markdown
### Description
Clear description of the bug.

### Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

### Expected Behavior
What should happen.

### Actual Behavior
What actually happened.

### Environment
- OS: [e.g., Windows 10, macOS 11, Ubuntu 20.04]
- Python: [version]
- Node: [version]
- Browser: [if applicable]

### Logs/Error Messages
```
[paste error logs here]
```
```

---

## 💡 Suggesting Features

### Feature Request Template:
```markdown
### Description
Clear description of the feature.

### Motivation
Why is this feature important? What problem does it solve?

### Proposed Solution
How should this feature work?

### Alternative Solutions
Other possible approaches.

### Additional Context
Screenshots, mockups, or references.
```

---

## ⚡ Quick Tips

✅ **Do:**
- Write clear commit messages
- Test before submitting
- Follow existing code style
- Keep PRs focused (one feature per PR)
- Document your changes
- Be respectful and constructive

❌ **Don't:**
- Submit without testing
- Mix multiple features in one PR
- Change unrelated code
- Ignore code review feedback
- Use offensive language

---

## 📞 Questions?

- 💬 Open an issue for discussion
- 📧 Contact: deepscanx@example.com
- 📖 Check documentation first

---

## 🙏 Thank You!

Your contributions make DeepScanX AI better for everyone. We appreciate your effort and look forward to collaborating with you!

**Happy coding!** 🚀
