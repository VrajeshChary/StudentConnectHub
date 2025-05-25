# ConnectNet - Student Networking Platform

ConnectNet is a modern web platform designed to help students connect, collaborate, and build their professional network. Built with Flask, HTML, CSS, and JavaScript, it provides a seamless experience for students to discover peers, chat in real-time, and collaborate on projects.

## Features

- 🔐 Secure user authentication
- 👥 Student profile management
- 🔍 Advanced search and filtering
- 💬 Real-time chat with WebSocket support
- 🌓 Dark/Light mode
- 📱 Responsive design
- 🔔 Real-time notifications
- 🔒 Student-only platform

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/connectnet.git
cd connectnet
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

- Windows:

```bash
venv\Scripts\activate
```

- Unix/MacOS:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Initialize the database:

```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

## Project Structure

```
connectnet/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── images/       # Image assets
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── index.html    # Home page
│   ├── dashboard.html # User dashboard
│   └── chat.html     # Chat interface
└── README.md         # Project documentation
```

## Development

### Adding New Features

1. Create a new branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:

```bash
git add .
git commit -m "Add your feature description"
```

3. Push to the repository:

```bash
git push origin feature/your-feature-name
```

### Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions small and focused
- Write tests for new features

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

- All passwords are hashed using Werkzeug's security functions
- CSRF protection enabled
- SQL injection prevention through SQLAlchemy
- XSS protection through proper escaping
- Rate limiting on authentication endpoints

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and its extensions
- Socket.IO for real-time communication
- Font Awesome for icons
- UI Avatars for profile pictures

## Support

For support, email hacksmithsunited@gmail.com or create an issue in the repository.

## Roadmap

- [ ] Add group chat functionality
- [ ] Implement file sharing
- [ ] Add calendar integration
- [ ] Create mobile app
- [ ] Add video calling
- [ ] Implement AI-powered matching
- [ ] Add event creation and management
- [ ] Integrate with learning management systems

## Presentation Files

Due to GitHub's file size limitations, the following presentation files are not included in this repository:

- `ConnectNet - A Place Where Students Can Connect!.pptx` (113.87 MB)
- `ConnectNet - A Place Where Students Can Connect!.pdf` (3.9 MB)

These files are available upon request. Please contact the repository owner for access to these files.
