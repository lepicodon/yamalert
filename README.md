# YamAlert 📊

YamAlert is a modern, user-friendly web application for managing and validating Prometheus alert rules and Alertmanager configurations. It provides a clean interface for creating, editing, and sharing monitoring templates with built-in validation and a live YAML preview.

![Screenshot showing the YamAlert interface](screenshot.png)

## 🌟 Features

- **Template Management**
  - Create and edit Prometheus rules and Alertmanager configs
  - Organize templates by job category and sensor type
  - Quick-start templates for common alert patterns
  - Merge multiple templates into a single configuration

- **Real-time Validation**
  - YAML syntax validation
  - Prometheus rule validation
  - PromQL expression checking
  - Alertmanager config validation

- **User Interface**
  - Clean, modern interface with 11 themes:
    - Light & Dark modes
    - Corporate theme for enterprise use
    - Nordic, Monokai, Cyberpunk, and more
  - Live YAML preview
  - Form-based rule editor
  - Collapsible help section with examples

- **Security**
  - Admin authentication system
  - CSRF protection
  - Input sanitization
  - Secure template storage

## 🚀 Quick Start

1. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/lepicodon/yamalert.git
   cd yamalert

   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   # Set environment variables (optional)
   export DATABASE_URL="sqlite:///data/yamalert.db"  # Default
   export SECRET_KEY="your-secure-secret-key"        # Change in production
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

   Visit `http://localhost:5000` in your browser.

## 🛠️ Development Setup

### Requirements
- Python 3.8+
- Flask 3.1+
- SQLAlchemy 2.0+
- PyYAML 6.0+

### Dependencies
```
Flask==3.1.2
Flask-WTF==1.2.2
Flask-Login==0.6.3
SQLAlchemy==2.0.44
PyYAML==6.0.3
psycopg2-binary==2.9.11
bleach==6.3.0
werkzeug==3.1.3
```

### Database Setup
The application uses SQLite by default but supports any SQLAlchemy-compatible database:

```python
# Configure your database URL
DATABASE_URL="sqlite:///data/yamalert.db"       # SQLite (default)
DATABASE_URL="postgresql://user:pass@host/db"    # PostgreSQL
```

## 📝 Usage Guide

### Creating Templates (admin only)
1. Click "New Template" to start
2. Choose template type (Prometheus Rule or Alertmanager Config)
3. Fill in metadata (name, category, sensor type)
4. Write your YAML configuration or use the Form Editor
5. Save your template

### Using the Form Editor
1. Switch to "Builder" mode for Prometheus rules
2. Add rule groups and individual rules
3. Fill in the form fields
4. Preview the generated YAML
5. Save when ready

### Merging Templates
1. Click "Merge Templates"
2. Select the templates you want to combine
3. Choose specific rules to include
4. Click "Merge Selected"
5. Review and save the merged configuration

## 🎨 Theming

YamAlert comes with 11 carefully designed themes:
- **Light** - Clean, professional design
- **Dark** - Modern dark mode
- **Corporate** - Enterprise-ready with gradient headers
- **Nordic** - Cool, minimal aesthetic
- **Monokai** - Popular code editor theme
- **Cyberpunk** - Neon accents on dark background
- **Nature** - Soft, natural green tones
- **Ocean** - Calming blue palette
- **Sunset** - Deep purples with warm accents
- **Winter** - Cool grays and blues
- **Desert** - Warm sand tones

## 🔐 Security

- **Authentication**: Admin login required for template management
- **CSRF Protection**: All forms are protected against cross-site request forgery
- **Input Sanitization**: All user input is sanitized using bleach
- **Secure Storage**: Templates are stored in a database with proper access controls

## 🙏 Acknowledgments

- [Prometheus](https://prometheus.io/) for the monitoring ecosystem
- [Flask](https://flask.palletsprojects.com/) web framework
- [Bootstrap](https://getbootstrap.com/) for the UI components

## Maintainers

- lepicodon (owner)

## Acknowledgements

Inspired by many YAML linters and validators — thank you to all open-source contributors.
