# YamAlert

**YamAlert** is a lightweight, responsive, and highly customizable YAML Rule Builder. It helps you design, validate, and test alert rules with a professional-grade UI.

---

## 🚀 Key Features

- **🎨 Multi-Theme UI**: Choose from a dozen high-quality themes (Cyberpunk, Nordic, Monokai, Neon, and more) to match your environment.
- **🛠️ Template Library**: Jump-start your rules using pre-configured templates for common monitoring scenarios (Email, Interlink, EDA).
- **🛡️ Robust Validation**: Persistent offline validation for both YAML structure and PromQL syntax.
- **🌐 Live Prometheus testing**: Connect to your real Prometheus clusters directly from the editor to verify if your queries return the data you expect.
- **🏗️ Production Ready**: Built with Flask and optimized for deployment via Gunicorn.
- **⚙️ Environment Configuration**: Securely configure secret keys and Prometheus presets using environment variables.

---

## 🛠️ Getting Started

### 1. Installation
Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configuration
Configure the application using environment variables:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session secret key | `your-secure-key` |
| `PROMETHEUS_URLS` | Comma-separated list of `Name\|URL` presets | `Production\|http://prom-prod:9090,Dev\|http://localhost:9090` |

### 3. Running for Development
Navigate to the `v2` directory and run:

```bash
cd v2
python app.py
```
The app will be available at `http://localhost:5000`.

### 4. Running for Production (Gunicorn)
From the `v2` directory:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

---

## 🔍 Validation & Testing

### Offline PromQL Check
The application performs a deep lexical check on your `expr` fields, ensuring balanced delimiters (`{}`, `[]`, `()`) and proper syntax before you ever hit "Download".

### Live Check
Use the **Presets** dropdown in the footer to select a configured Prometheus URL, or type one manually. Hit **Test Query** to see live results (status, match count, and labels) directly in the UI.

---

## 📁 Project Structure

- `/v1`: Legacy version (stable).
- `/v2`: Current modernized version with enhanced validation and live testing.
- `requirements.txt`: Unified dependency list.

---

## 🤝 Contributing
Contributions are welcome! Please ensure any new features follow the current theme system and maintain clean backend-frontend separation.
