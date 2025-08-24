# 📚 Teacher's Assistant

A simple proof-of-concept Streamlit application for AI-powered test grading using OpenAI GPT-4o-mini.

## ✨ Features

### 🎓 For Teachers (Admins)
- **Student Management**: Add, edit, and manage student records
- **Test Creation**: Create tests with question papers (PDF/image upload)
- **Submission Management**: View all student submissions and grading status
- **AI Grading**: Automatic grading with GPT-4o-mini including OCR and feedback
- **PDF Reports**: Generate individual result PDFs and class performance reports
- **System Settings**: Configure AI prompts, monitor system health, and maintain data

### 📝 For Students
- **Test Dashboard**: View assigned tests and submission status
- **Answer Upload**: Submit answers as PDF or image files
- **Results Viewing**: View grades, feedback, and download result PDFs
- **Progress Tracking**: Track submission and grading status

### 🤖 AI-Powered Features
- **OCR**: Extract text from images and PDFs using GPT-4o-mini vision
- **Intelligent Grading**: Contextual assessment with rubric support
- **Detailed Feedback**: Scores, remarks, strengths, and improvement suggestions
- **Customizable Prompts**: Admin can modify OCR and grading prompts

## 🛠️ Technical Stack

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with async grading processing
- **Database**: MongoDB with GridFS for file storage
- **AI**: OpenAI GPT-4o-mini for OCR and grading
- **PDF Generation**: ReportLab for professional result documents
- **Authentication**: Secure login with bcrypt password hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or Atlas cloud)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd teaching_assistant_demo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Configure .env file**
   ```env
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=teaching_assistant
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secret_key
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the app**
   - Open http://localhost:8501 in your browser
   - Login with demo credentials:
     - Admin: `admin` / `admin123`
     - Student: `student` / `student123`

## 📋 Usage Guide

### Setting Up Your First Test

1. **Login as Admin** using `admin` / `admin123`
2. **Add Students**: Go to "Students" tab → "Add Student"
3. **Create Test**: Go to "Tests" tab → "Create Test"
   - Upload question paper (PDF/image)
   - Add optional rubric for grading criteria
4. **Monitor Submissions**: Check "Submissions" tab for student uploads

### Student Workflow

1. **Login as Student** using `student` / `student123`
2. **View Tests**: See assigned tests in "My Tests" tab
3. **Submit Answers**: Upload completed answer sheets (PDF/image)
4. **Check Results**: View grades and feedback in "My Results" tab
5. **Download PDFs**: Get professional result documents

### AI Grading Process

1. **Automatic OCR**: Extracts text from uploaded images/PDFs
2. **Contextual Analysis**: Considers questions, rubric, and subject
3. **Intelligent Scoring**: Provides total score and detailed feedback
4. **Instant Results**: Grades appear in dashboards immediately
5. **Admin Review**: Teachers can modify scores if needed

## 🔧 System Settings

### AI Configuration
- **Test API Connection**: Verify OpenAI integration
- **OCR Prompts**: Customize text extraction instructions
- **Grading Prompts**: Modify assessment criteria and feedback style

### Maintenance Tools
- **File Cleanup**: Automatic removal of files older than 7 days
- **Storage Monitoring**: Track file usage and system health
- **Data Export**: Backup student, test, and submission data

### Health Monitoring
- **Database Status**: MongoDB connection health
- **AI Service Status**: OpenAI API availability
- **Storage Health**: File system usage and cleanup status

## 📊 Performance Specifications

- **Login**: <500ms response time
- **Queries**: <300ms for 1,000+ student records
- **Grading**: <15 seconds per submission
- **PDF Generation**: <5 seconds per document
- **File Upload**: <5 seconds for submission storage

## 🔒 Security Features

- **Authentication**: Secure login with bcrypt password hashing
- **Session Management**: Proper session state handling
- **Failed Login Protection**: Account lockout after 5 failed attempts
- **File Security**: Encrypted file storage with automatic expiry
- **Input Validation**: Sanitized inputs and error handling

## 📁 Project Structure

```
teaching_assistant_demo/
├── app.py                 # Main Streamlit application
├── pages/
│   ├── admin_dashboard.py # Admin interface
│   └── student_dashboard.py # Student interface
├── utils/
│   ├── auth.py           # Authentication management
│   ├── database.py       # MongoDB operations
│   ├── student_manager.py # Student CRUD operations
│   ├── test_manager.py   # Test management
│   ├── submission_manager.py # Submission handling
│   ├── ai_grading.py     # OpenAI integration
│   ├── pdf_generator.py  # PDF creation
│   └── maintenance.py    # System maintenance
├── models/
│   └── schemas.py        # Data models
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
└── README.md            # This file
```

## 🎯 Key Features Implemented

### Phase 1: Foundation ✅
- Project structure and database setup
- Multi-page Streamlit configuration
- MongoDB connection with GridFS

### Phase 2: Authentication ✅
- Secure login system with bcrypt
- Session management and role-based routing
- Failed login protection with lockout

### Phase 3: Data Management ✅
- Complete student and test CRUD operations
- File upload and storage with GridFS
- Search and filtering capabilities

### Phase 4: Student Interface ✅
- Student dashboard with assigned tests
- Answer upload functionality
- Results viewing and tracking

### Phase 5: Admin Management ✅
- Comprehensive admin dashboard
- Submission management and filtering
- Admin upload capability for students

### Phase 6: AI Integration ✅
- OpenAI GPT-4o-mini integration
- OCR from images and PDFs
- Automated grading with detailed feedback

### Phase 7: Reports & Results ✅
- Professional PDF generation with ReportLab
- Individual student result documents
- Class performance analytics reports

### Phase 8: Settings & Polish ✅
- Comprehensive system settings panel
- Health monitoring and maintenance tools
- Data export and backup functionality

## 🔄 Data Flow

1. **Test Creation**: Admin creates test with question paper
2. **Student Assignment**: All tests assigned to all students (configurable)
3. **Answer Submission**: Students upload completed answer sheets
4. **AI Processing**: Automatic OCR and grading with GPT-4o-mini
5. **Result Generation**: Instant feedback and PDF report creation
6. **Review & Download**: Students and admins access results

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop and mobile devices
- **Intuitive Navigation**: Clean tabbed interface for all functions
- **Real-time Updates**: Instant status updates and notifications
- **Professional PDFs**: Properly formatted result documents
- **Status Indicators**: Clear visual feedback for all operations

## 🤝 Contributing

This is a proof-of-concept application. For production use, consider:
- Enhanced security measures
- Scalability improvements
- Advanced user management
- Comprehensive test assignment logic
- Additional grading algorithms

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check system health in Admin → Settings → System Health
2. Verify MongoDB and OpenAI API connections
3. Review application logs for error messages
4. Ensure all environment variables are properly configured

---

**Teacher's Assistant v1.2** - Making test grading smarter and faster with AI! 🚀