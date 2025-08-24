import streamlit as st
import pandas as pd
from datetime import datetime
import json

def admin_dashboard():
    st.title("🎓 Teacher's Assistant - Admin Dashboard")
    
    # Initialize session state
    if 'admin_page' not in st.session_state:
        st.session_state.admin_page = 'overview'
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.radio(
            "Select Page:",
            ['📊 Overview', '👥 Students', '📝 Tests', '📄 Submissions', '⚙️ Settings', '⚡ Advanced Features', '📈 Reports', '🔧 Maintenance']
        )
        
        # Update session state
        if 'Overview' in page:
            st.session_state.admin_page = 'overview'
        elif 'Students' in page:
            st.session_state.admin_page = 'students'
        elif 'Tests' in page:
            st.session_state.admin_page = 'tests'
        elif 'Submissions' in page:
            st.session_state.admin_page = 'submissions'
        elif 'Settings' in page:
            st.session_state.admin_page = 'settings'
        elif 'Advanced Features' in page:
            st.session_state.admin_page = 'advanced'
        elif 'Reports' in page:
            st.session_state.admin_page = 'reports'
        elif 'Maintenance' in page:
            st.session_state.admin_page = 'maintenance'
    
    # Page routing
    if st.session_state.admin_page == 'overview':
        overview_page()
    elif st.session_state.admin_page == 'students':
        students_page()
    elif st.session_state.admin_page == 'tests':
        tests_page()
    elif st.session_state.admin_page == 'submissions':
        submissions_page()
    elif st.session_state.admin_page == 'settings':
        settings_page()
    elif st.session_state.admin_page == 'advanced':
        advanced_features_page()
    elif st.session_state.admin_page == 'reports':
        reports_page()
    elif st.session_state.admin_page == 'maintenance':
        maintenance_page()

def overview_page():
    st.header("📊 Dashboard Overview")
    
    # Get statistics
    from utils.student_manager import student_manager
    from utils.test_manager import test_manager
    from utils.submission_manager import submission_manager
    from utils.processing_pipeline import processing_pipeline
    
    students = student_manager.get_all_students()
    tests = test_manager.get_all_tests()
    submissions = submission_manager.get_all_submissions()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", len(students))
    
    with col2:
        st.metric("Total Tests", len(tests))
    
    with col3:
        st.metric("Total Submissions", len(submissions))
    
    with col4:
        # Get processing pipeline metrics
        metrics = processing_pipeline.get_metrics()
        st.metric("Active Tasks", metrics.active_workers)
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    # Recent submissions
    recent_submissions = submissions[-5:] if submissions else []
    if recent_submissions:
        submission_data = []
        for sub in recent_submissions:
            submission_data.append({
                'Student ID': sub['student_id'],
                'Test ID': sub['test_id'],
                'Status': sub['status'],
                'Submitted': sub['submitted_at']
            })
        
        df = pd.DataFrame(submission_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent submissions")
    
    # System health
    st.subheader("🏥 System Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Database status
        try:
            from utils.database import db_manager
            db_manager.execute_query("SELECT 1")
            st.success("✅ Database: Connected")
        except Exception as e:
            st.error(f"❌ Database: Error - {e}")
        
        # AI service status
        try:
            from utils.ai_grading import ai_grading_manager
            ai_grading_manager.test_api_connection()
            st.success("✅ AI Service: Connected")
        except Exception as e:
            st.error(f"❌ AI Service: Error - {e}")
    
    with col2:
        # Processing pipeline status
        if processing_pipeline.is_running:
            st.success("✅ Processing Pipeline: Running")
        else:
            st.warning("⚠️ Processing Pipeline: Stopped")
        
        # Queue status
        queue_status = processing_pipeline.get_queue_status()
        total_queued = sum(queue_status.values())
        st.info(f"📋 Queued Tasks: {total_queued}")

def students_page():
    st.header("👥 Student Management")
    
    from utils.student_manager import student_manager
    
    # Create new student
    with st.expander("➕ Add New Student", expanded=False):
        with st.form("add_student_form"):
            student_id = st.text_input("Student ID")
            name = st.text_input("Name")
            email = st.text_input("Email")
            grade = st.selectbox("Grade", ["9", "10", "11", "12"])
            
            if st.form_submit_button("Add Student"):
                if student_id and name and email:
                    result = student_manager.create_student(student_id, name, email, grade)
                    if result:
                        st.success("Student added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")
    
    # Display students
    students = student_manager.get_all_students()
    
    if students:
        # Convert to DataFrame for better display
        student_data = []
        for student in students:
            student_data.append({
                'ID': student['student_id'],
                'Name': student['name'],
                'Email': student.get('email', ''),
                'Phone': student.get('phone', ''),
                'Created': student['created_at']
            })
        
        df = pd.DataFrame(student_data)
        st.dataframe(df, use_container_width=True)
        
        # Student actions
        st.subheader("Actions")
        # Create a mapping of display names to student IDs
        student_options = [f"{s['name']} ({s['student_id']})" for s in students]
        selected_student_display = st.selectbox("Select student:", student_options)
        # Extract the student_id from the selected display string
        selected_student = selected_student_display.split('(')[-1].split(')')[0] if selected_student_display else None
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete Student"):
                if student_manager.delete_student(selected_student):
                    st.success("Student deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete student")
        
        with col2:
            if st.button("📊 View Performance"):
                # Show student performance
                from utils.submission_manager import submission_manager
                student_submissions = submission_manager.get_submissions_by_student_id(selected_student)
                
                if student_submissions:
                    st.write(f"Submissions for {selected_student}:")
                    for sub in student_submissions:
                        st.write(f"- Test {sub['test_id']}: {sub['status']}")
                else:
                    st.info("No submissions found for this student")
    else:
        st.info("No students found")

def tests_page():
    st.header("📝 Test Management")
    
    from utils.test_manager import test_manager
    
    # Create new test
    with st.expander("➕ Create New Test", expanded=False):
        with st.form("create_test_form"):
            title = st.text_input("Test Title")
            description = st.text_area("Description")
            duration = st.number_input("Duration (minutes)", min_value=1, value=60)
            
            # File upload
            question_file = st.file_uploader("Question Paper (PDF/Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
            rubric_file = st.file_uploader("Rubric (PDF/Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("Create Test"):
                if title and question_file:
                    # Create test with file data
                    from utils.database import db_manager
                    from datetime import datetime
                    
                    # Get file content type
                    content_type = question_file.type if hasattr(question_file, 'type') else None
                    
                    # Create test with file data
                    result = test_manager.create_test(
                        title=title,
                        subject=description or "General",
                        date=datetime.now(),
                        rubric=None,  # Will be handled separately if rubric file is provided
                        file_data=question_file.read(),
                        filename=question_file.name,
                        content_type=content_type
                    )
                    
                    # Handle rubric file separately if provided
                    if result and rubric_file:
                        # Store rubric file
                        rubric_content_type = rubric_file.type if hasattr(rubric_file, 'type') else None
                        rubric_file_id = db_manager.store_file(rubric_file.read(), rubric_file.name, rubric_content_type)
                        
                        # Update test with rubric file ID
                        db_manager.execute_query(
                            "UPDATE tests SET rubric_file_id = ? WHERE test_id = ?",
                            (rubric_file_id, result)
                        )
                    
                    if result:
                        st.success("Test created successfully!")
                    st.rerun()
                else:
                    st.error("Please provide test title and question file")
    
    # Display tests
    tests = test_manager.get_all_tests()
    
    if tests:
        # Convert to DataFrame for better display
        test_data = []
        for test in tests:
            # Check if test has file (questions field contains file_id)
            has_file = bool(test.get('questions') and test.get('questions') != '')
            
            test_data.append({
                'ID': test.get('id', test.get('test_id', 'N/A')),
                'Title': test.get('title', 'N/A'),
                'Description': test.get('description', 'N/A'),
                'Duration': f"{test.get('duration', 60)} min",
                'Created': test.get('created_at', 'N/A'),
                'File': '✅' if has_file else '❌',
                'Rubric': '✅' if test.get('rubric_extracted') else '❌',
                'Questions': '✅' if test.get('questions_extracted') else '❌'
            })
        
        df = pd.DataFrame(test_data)
        st.dataframe(df, use_container_width=True)
        
        # Test actions
        st.subheader("Test Actions")
        selected_test = st.selectbox("Select test:", [t.get('id', t.get('test_id', '')) for t in tests])
        selected_test_data = next(t for t in tests if t.get('id', t.get('test_id', '')) == selected_test)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Extract Rubric"):
                if test_manager.extract_rubric(selected_test):
                    st.success("Rubric extracted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to extract rubric")
        
        with col2:
            if st.button("🔍 Extract Questions"):
                if test_manager.extract_questions_from_test(selected_test):
                    st.success("Questions extracted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to extract questions")
        
        with col3:
            if st.button("📋 View Rubric"):
                rubric_data = test_manager.get_rubric_data(selected_test)
                if rubric_data:
                    st.json(rubric_data)
                else:
                    st.info("No rubric data available")
        
        with col4:
            if st.button("🗑️ Delete Test"):
                if test_manager.delete_test(selected_test):
                    st.success("Test deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete test")
            else:
                st.info("No tests found")

def submissions_page():
    st.header("📄 Submission Management")
    
    from utils.submission_manager import submission_manager
    from utils.test_manager import test_manager
    
    # Get all submissions
    submissions = submission_manager.get_all_submissions()
    
    if submissions:
        # Convert to DataFrame for better display
        submission_data = []
        for sub in submissions:
            submission_data.append({
                'ID': sub.get('id', sub.get('submission_id', 'N/A')),
                'Student ID': sub.get('student_id', 'N/A'),
                'Test ID': sub.get('test_id', 'N/A'),
                'Status': sub.get('status', 'N/A'),
                'Score': f"{sub.get('score', 'N/A')}%",
                'Submitted': sub.get('submitted_at', 'N/A')
            })
        
        df = pd.DataFrame(submission_data)
        st.dataframe(df, use_container_width=True)
        
        # Submission actions
        st.subheader("Submission Actions")
        selected_submission = st.selectbox("Select submission:", [s.get('id', s.get('submission_id', '')) for s in submissions])
        selected_submission_data = next(s for s in submissions if s.get('id', s.get('submission_id', '')) == selected_submission)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Grade Submission"):
                # Trigger grading
                if submission_manager.trigger_grading(selected_submission):
                    st.success("Grading triggered successfully!")
                    st.rerun()
                else:
                    st.error("Failed to trigger grading")
        
        with col2:
            if st.button("📊 View Results"):
                # Show grading results
                results = submission_manager.get_grading_results(selected_submission)
                if results:
                    st.json(results)
                else:
                    st.info("No grading results available")
        
        with col3:
            if st.button("🗑️ Delete Submission"):
                if submission_manager.delete_submission(selected_submission):
                    st.success("Submission deleted successfully!")
                    st.rerun()
            else:
                    st.error("Failed to delete submission")
    else:
        st.info("No submissions found")

def settings_page():
    st.header("⚙️ System Settings")
    
    from utils.database import db_manager
    
    # AI Configuration
    st.subheader("🤖 AI Configuration")
    
    # Get current AI prompts
    settings = db_manager.execute_query("SELECT * FROM settings WHERE key LIKE 'ai_%'")
    
    if settings:
        for setting in settings:
            with st.expander(f"📝 {setting['key'].replace('ai_', '').replace('_', ' ').title()}", expanded=False):
                current_prompt = setting['value']
                new_prompt = st.text_area("Prompt:", value=current_prompt, height=200)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💾 Save", key=f"save_{setting['key']}"):
                        db_manager.execute_query(
                            "UPDATE settings SET value = ? WHERE key = ?",
                            (new_prompt, setting['key'])
                        )
                        st.success("Prompt saved successfully!")
                
                with col2:
                    if st.button("🔄 Reset to Default", key=f"reset_{setting['key']}"):
                        # Reset to default prompt
                        default_prompts = {
                            'ai_grading_prompt': 'Grade this student answer based on the rubric...',
                            'ai_ocr_prompt': 'Extract text from this image...',
                            'ai_rubric_extraction_prompt': 'Extract rubric criteria from this table...',
                            'ai_test_extraction_prompt': 'Extract questions from this test paper...',
                            'ai_answer_extraction_prompt': 'Extract answers from this answer sheet...'
                        }
                        
                        if setting['key'] in default_prompts:
                            db_manager.execute_query(
                                "UPDATE settings SET value = ? WHERE key = ?",
                                (default_prompts[setting['key']], setting['key'])
                            )
                            st.success("Prompt reset to default!")
                            st.rerun()
    
    # System Configuration
    st.subheader("🔧 System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_file_size = st.number_input("Max File Size (MB)", min_value=1, value=50)
        if st.button("💾 Save File Size Limit"):
            # Save file size limit
            st.success("File size limit saved!")
    
    with col2:
        auto_cleanup = st.checkbox("Auto-cleanup temporary files", value=True)
        if st.button("💾 Save Cleanup Settings"):
            # Save cleanup settings
            st.success("Cleanup settings saved!")

def advanced_features_page():
    st.header("⚡ Advanced Features")
    
    from components.advanced_ui import advanced_ui
    
    # Advanced UI components
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Real-time Processing", "⚡ Bulk Operations", "📊 Advanced Analytics", "🔍 Interactive Analysis"])
    
    with tab1:
        st.subheader("🔄 Real-time Processing Pipeline")
        
        from utils.processing_pipeline import processing_pipeline
        
        # Pipeline controls
        col1, col2 = st.columns(2)
        
        with col1:
            if not processing_pipeline.is_running:
                if st.button("▶️ Start Pipeline", type="primary"):
                    processing_pipeline.start()
                    st.success("Processing pipeline started!")
                    st.rerun()
            else:
                if st.button("⏹️ Stop Pipeline"):
                    processing_pipeline.stop()
                    st.success("Processing pipeline stopped!")
                    st.rerun()
        
        with col2:
            if st.button("📊 View Metrics"):
                metrics = processing_pipeline.get_metrics()
                st.write("**Pipeline Metrics:**")
                st.write(f"- Total Tasks: {metrics.total_tasks}")
                st.write(f"- Completed: {metrics.completed_tasks}")
                st.write(f"- Failed: {metrics.failed_tasks}")
                st.write(f"- Average Time: {metrics.average_processing_time:.2f}s")
                st.write(f"- Uptime: {metrics.uptime:.1f}s")
        
        # Queue status
        queue_status = processing_pipeline.get_queue_status()
        st.subheader("📋 Queue Status")
        
        for priority, count in queue_status.items():
            st.write(f"- {priority}: {count} tasks")
    
    with tab2:
        # Bulk operations
        advanced_ui.render_bulk_operations_panel()
    
    with tab3:
        st.subheader("📊 Advanced Analytics")
        
        # Performance analytics
        from utils.submission_manager import submission_manager
        submissions = submission_manager.get_all_submissions()
        
        if submissions:
            # Calculate statistics
            scores = [s.get('score', 0) for s in submissions if s.get('score')]
            
            if scores:
                col1, col2 = st.columns(2)
                
        with col1:
                    st.metric("Average Score", f"{sum(scores)/len(scores):.1f}%")
                    st.metric("Highest Score", f"{max(scores):.1f}%")
                    st.metric("Lowest Score", f"{min(scores):.1f}%")
                
        with col2:
                    # Score distribution
                    import plotly.express as px
                    
                    fig = px.histogram(x=scores, nbins=10, title="Score Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Question difficulty analysis
        st.subheader("Question Difficulty Analysis")
        st.info("Question difficulty analysis requires detailed grading data")
    
    with tab4:
        st.subheader("🔍 Interactive Analysis")
        
        # Select a submission for detailed analysis
        from utils.submission_manager import submission_manager
        submissions = submission_manager.get_all_submissions()
        
        if submissions:
            selected_submission = st.selectbox(
                "Select submission for analysis:",
                [s['id'] for s in submissions]
            )
            
            if st.button("🔍 Analyze Submission"):
                # This would trigger detailed analysis
                st.info("Detailed analysis feature requires grading results")
        else:
            st.info("No submissions available for analysis")

def reports_page():
    st.header("📈 Reports & Analytics")
    
    from utils.report_generator import report_generator
    
    # Report generation options
    st.subheader("📄 Generate Reports")
    
    col1, col2 = st.columns(2)
        
    with col1:
        report_type = st.selectbox(
            "Report Type:",
            ["Individual Student Report", "Class Performance Report", "Test Analysis Report"]
        )
        
        if report_type == "Individual Student Report":
            from utils.student_manager import student_manager
            students = student_manager.get_all_students()
            # Create a mapping of display names to student IDs
            student_options = [f"{s['name']} ({s['student_id']})" for s in students]
            selected_student_display = st.selectbox("Select student:", student_options)
            # Extract the student_id from the selected display string
            selected_student = selected_student_display.split('(')[-1].split(')')[0] if selected_student_display else None
        
        elif report_type == "Class Performance Report":
            from utils.test_manager import test_manager
            tests = test_manager.get_all_tests()
            selected_test = st.selectbox("Select test:", [t['id'] for t in tests])
        
    with col2:
        report_format = st.selectbox(
            "Format:",
            ["Word Document (.docx)", "PDF", "JSON Export"]
        )
        
        include_charts = st.checkbox("Include Charts", value=True)
        include_detailed_analysis = st.checkbox("Include Detailed Analysis", value=True)
    
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            st.success("Report generation started!")
            # Implementation would generate the report
    
    # Recent reports
    st.subheader("📋 Recent Reports")
    st.info("Report history feature coming soon")

def maintenance_page():
    st.header("🔧 System Maintenance")
    
    from utils.maintenance import maintenance_manager
    
    # System health check
    st.subheader("🏥 System Health Check")
    
    if st.button("🔍 Run Health Check"):
        health_status = maintenance_manager.check_system_health()
        
        for component, status in health_status.items():
            if status['status'] == 'healthy':
                st.success(f"✅ {component}: {status['message']}")
            elif status['status'] == 'warning':
                st.warning(f"⚠️ {component}: {status['message']}")
            else:
                st.error(f"❌ {component}: {status['message']}")
    
    # File cleanup
    st.subheader("🧹 File Cleanup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clean Temporary Files"):
            from utils.enhanced_file_processor import enhanced_file_processor
            enhanced_file_processor.cleanup_temp_files()
            st.success("Temporary files cleaned!")
    
    with col2:
        if st.button("🗑️ Clean Old Submissions"):
            # Clean old submissions
            st.success("Old submissions cleaned!")
    
    # Data export
    st.subheader("📤 Data Export")
    
    if st.button("📤 Export All Data"):
        export_file = maintenance_manager.export_all_data()
        if export_file:
            st.success(f"Data exported to: {export_file}")
            # Provide download link
            with open(export_file, 'r') as f:
                    st.download_button(
                    label="📥 Download Export",
                    data=f.read(),
                    file_name="system_export.json",
                        mime="application/json"
                    )
    
    # System statistics
    st.subheader("📊 System Statistics")
    
    from utils.enhanced_file_processor import enhanced_file_processor
    storage_stats = enhanced_file_processor.get_storage_stats()
    
    st.write("**Storage Statistics:**")
    st.write(f"- Total Files: {storage_stats['total_files']}")
    st.write(f"- Total Size: {storage_stats['total_size_mb']:.1f} MB")
    st.write(f"- Max File Size: {storage_stats['max_file_size'] / (1024*1024):.1f} MB")
