# VeriFast - AI-Powered Speed Reading Platform

*Last Updated: July 21, 2025*

VeriFast is a comprehensive web application that combines speed reading techniques with AI-powered comprehension testing, gamification, and social features to create an engaging learning experience.

## 🚀 Quick Start

### Installation
```bash
git clone <repository-url>
cd verifast
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit `http://localhost:8000` to get started.

**For detailed setup:** [Installation Guide](documentation/setup/installation.md)

## 📚 Documentation Hub

### 🏗️ Setup & Development
- [📋 Installation Guide](documentation/setup/installation.md) - Get VeriFast running locally
- [🔧 Development Setup](documentation/setup/development.md) - Development environment configuration
- [🤖 Gemini + Kiro Workflow](GEMINI_KIRO_WORKFLOW.md) - Multi-developer collaboration guide

### 🏛️ Architecture & Design
- [🏗️ System Overview](documentation/architecture/overview.md) - High-level architecture
- [🏛️ Architecture Guide](documentation/PROJECT_ARCHITECTURE_GUIDE.md) - Detailed architecture documentation
- [📊 Technical Specification](documentation/Technical-Specification.md) - Detailed technical specs

### ✨ Features
- [🏷️ Tag System](documentation/features/tag-system.md) - Wikipedia-validated content tagging
- [⭐ XP System](documentation/features/xp-system.md) - Gamification and premium features
- [📖 Speed Reader](documentation/features/speed-reader.md) - Immersive reading experience
- [🌍 Internationalization](documentation/internationalization-implementation.md) - Multi-language support (Spanish)

### 📈 Project Information
- [📊 Current Status](documentation/PROJECT-STATUS.md) - Implementation progress and roadmap
- [🎉 Project Summary](documentation/FINAL_PROJECT_SUMMARY.md) - Complete transformation summary
- [📋 Product Requirements](documentation/VeriFast_PRD_v1.1_Django_EN.md) - Original requirements document

## 🎯 Key Features

### 📖 Speed Reading (HTMX Hybrid Architecture)
- **Single Immersive Mode** - Full-screen interface with full-width white text strip (ONLY reading mode)
- **HTMX Integration** - Server-side processing with minimal Alpine.js (max 30 lines)
- **Complete Article Pages** - Image, metadata, tags, comments, related articles
- **Progressive Enhancement** - Works without JavaScript, enhanced with minimal client code
- **Configurable WPM** - Adjustable reading speed from 50-1000 WPM with user power-ups

### 🤖 AI-Powered Quizzes
- **Google Gemini Integration** - Intelligent quiz generation
- **Adaptive Difficulty** - Quizzes tailored to content complexity
- **Instant Feedback** - Immediate results and explanations

### 🏆 Gamification System
- **XP Economy** - Earn points for reading and quiz performance
- **Premium Features** - Spend XP on customizations and enhancements
- **Social Interactions** - Comment system with XP rewards

### 🏷️ Smart Tagging
- **Wikipedia Validation** - Tags verified against Wikipedia
- **Content Discovery** - Find articles by topic
- **Tag Analytics** - Popular and trending topics

## 🛠️ Technology Stack

- **Backend:** Django 4.2+ with Python 3.10+
- **Database:** SQLite (development) / PostgreSQL (production)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **AI Integration:** Google Gemini API
- **External APIs:** Wikipedia API
- **Testing:** Django Test Framework, MyPy
- **Code Quality:** Ruff (formatting & linting)

## 📊 Project Status

**Overall Completion: 95%** ✅

- ✅ **Core Platform** - Fully functional web application
- ✅ **Speed Reader** - Complete with immersive mode
- ✅ **XP System** - Comprehensive gamification
- ✅ **Tag System** - Wikipedia-validated tagging
- ✅ **AI Integration** - Google Gemini quiz generation
- ✅ **User Management** - Authentication and profiles
- ✅ **Admin Interface** - Content management
- 🔄 **Documentation** - Currently being consolidated

## 🤝 Contributing

1. **Read the Documentation** - Start with [Development Setup](documentation/setup/development.md)
2. **Check Current Status** - Review [Project Status](documentation/PROJECT-STATUS.md)
3. **Follow Standards** - Use our coding standards and testing practices
4. **Submit PRs** - Create feature branches and submit pull requests

## 📁 Project Structure

```
verifast/
├── 📁 config/              # Django configuration
├── 📁 verifast_app/        # Main application
├── 📁 core/                # Shared utilities
├── 📁 documentation/       # Project documentation
├── 📁 .kiro/               # Kiro specifications
├── 📁 templates/           # HTML templates
├── 📁 static/              # Static files
└── 📄 manage.py            # Django management
```

## 🔗 Quick Links

- **Admin Interface:** `/admin/` (requires superuser)
- **API Documentation:** `/api/` (REST endpoints)
- **Speed Reader:** `/reader/` (main reading interface)
- **User Profile:** `/profile/` (user dashboard)

## 📞 Support

- **Documentation Issues:** Check [Documentation Status](documentation/PROJECT-STATUS.md)
- **Bug Reports:** Create an issue with detailed reproduction steps
- **Feature Requests:** Review existing specs in `.kiro/specs/`

## 📜 License

[Add your license information here]

---

**🎯 Ready to start?** Begin with the [Installation Guide](documentation/setup/installation.md) or explore the [Architecture Overview](documentation/architecture/overview.md) to understand how VeriFast works.