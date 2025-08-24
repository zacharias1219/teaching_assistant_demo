import streamlit as st
from datetime import datetime
from utils.assignment_manager import assignment_manager
from utils.submission_manager import submission_manager
from utils.test_manager import test_manager
from utils.student_manager import student_manager
from utils.pdf_generator import pdf_generator

def show_student_dashboard():
    """Main student dashboard"""
    st.title("📚 Student Dashboard")
    
    # Get current student ID
    student_id = get_current_student_id()
    if not student_id:
        st.error("Student account not properly configured. Please contact admin.")
        return
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📋 My Tests", "📤 Upload Answer", "📊 My Results"])
    
    with tab1:
        show_assigned_tests(student_id)
    
    with tab2:
        show_upload_interface(student_id)
    
    with tab3:
        show_my_results(student_id)

def get_current_student_id():
    """Get the current student's ID from session"""
    try:
        # For demo purposes, create a student record if username is 'student'
        if st.session_state.username == "student":
            # Check if student record exists
            students = student_manager.get_all_students()
            demo_student = None
            for student in students:
                if student['name'].lower() == 'demo student':
                    demo_student = student
                    break
            
            if not demo_student:
                # Create demo student
                if student_manager.create_student("Demo Student", "10A"):
                    students = student_manager.get_all_students()
                    for student in students:
                        if student['name'].lower() == 'demo student':
                            demo_student = student
                            break
            
            return demo_student['student_id'] if demo_student else None
        
        return st.session_state.get('student_id')
        
    except Exception as e:
        print(f"Error getting student ID: {e}")
        return None

def show_assigned_tests(student_id: str):
    """Show tests assigned to the student"""
    st.subheader("📋 My Assigned Tests")
    
    try:
        assigned_tests = assignment_manager.get_assigned_tests(student_id)
        
        if not assigned_tests:
            st.info("No tests assigned yet. Check back later!")
            return
        
        # Display tests
        for test in assigned_tests:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{test['title']}**")
                    st.caption(f"Subject: {test['subject']} | Date: {test['date'].strftime('%Y-%m-%d')}")
                    if test.get('rubric'):
                        with st.expander("📝 Rubric"):
                            st.write(test['rubric'])
                
                with col2:
                    # Check submission status
                    has_submitted = submission_manager.has_student_submitted(test['test_id'], student_id)
                    if has_submitted:
                        st.success("✅ Submitted")
                    else:
                        st.warning("⏳ Pending")
                
                with col3:
                    if not has_submitted:
                        if st.button("📤 Upload", key=f"upload_{test['test_id']}"):
                            st.session_state.selected_test_for_upload = test['test_id']
                    else:
                        if st.button("👁️ View", key=f"view_{test['test_id']}"):
                            st.session_state.selected_test_for_view = test['test_id']
                
                st.divider()
    
    except Exception as e:
        st.error("Error loading assigned tests. Please try again.")
        print(f"Error in show_assigned_tests: {e}")

def show_upload_interface(student_id: str):
    """Show answer upload interface"""
    st.subheader("📤 Upload Answer")
    
    try:
        # Get tests available for upload
        assigned_tests = assignment_manager.get_assigned_tests(student_id)
        available_tests = []
        
        for test in assigned_tests:
            if not submission_manager.has_student_submitted(test['test_id'], student_id):
                available_tests.append(test)
        
        if not available_tests:
            st.info("No tests available for submission. All assigned tests have been completed!")
            return
        
        # Test selection
        test_options = {test['test_id']: f"{test['title']} - {test['subject']}" for test in available_tests}
        
        selected_test_id = st.selectbox(
            "Select Test:",
            options=list(test_options.keys()),
            format_func=lambda x: test_options[x]
        )
        
        if selected_test_id:
            selected_test = next(test for test in available_tests if test['test_id'] == selected_test_id)
            
            # Show test details
            st.write(f"**Test:** {selected_test['title']}")
            st.write(f"**Subject:** {selected_test['subject']}")
            st.write(f"**Date:** {selected_test['date'].strftime('%Y-%m-%d')}")
            
            # Upload form
            with st.form("upload_answer_form"):
                st.write("**Upload Your Answer**")
                
                uploaded_file = st.file_uploader(
                    "Choose your answer file:",
                    type=['pdf', 'png', 'jpg', 'jpeg'],
                    help="Upload your completed answer sheet (PDF or image)"
                )
                
                st.info("📝 Make sure your answers are clear and legible before uploading.")
                
                submit = st.form_submit_button("🚀 Submit Answer", type="primary")
                
                if submit:
                    if uploaded_file:
                        try:
                            file_data = uploaded_file.read()
                            filename = f"{selected_test['title']}_answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{uploaded_file.name.split('.')[-1]}"
                            
                            if submission_manager.create_submission(
                                selected_test_id, 
                                student_id, 
                                file_data, 
                                filename, 
                                uploaded_file.type
                            ):
                                st.success("🎉 Answer submitted successfully!")
                                st.info("Your answer will be graded automatically. Check the 'My Results' tab for updates.")
                                st.rerun()
                            else:
                                st.error("Failed to submit answer. You may have already submitted for this test.")
                        except Exception as e:
                            st.error("Error uploading file. Please try again.")
                            print(f"Upload error: {e}")
                    else:
                        st.error("Please select a file to upload.")
    
    except Exception as e:
        st.error("Error loading upload interface. Please try again.")
        print(f"Error in show_upload_interface: {e}")

def show_my_results(student_id: str):
    """Show student's submission results"""
    st.subheader("📊 My Results")
    
    try:
        submissions = submission_manager.get_submissions_by_student(student_id)
        
        if not submissions:
            st.info("No submissions yet. Upload some answers to see results here!")
            return
        
        # Show all results summary
        st.write(f"**Total Submissions: {len(submissions)}**")
        
        for submission in submissions:
            try:
                # Get test details
                test = test_manager.get_test_by_id(submission['test_id'])
                if not test:
                    continue
                
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{test['title']}**")
                        st.caption(f"Subject: {test['subject']} | Submitted: {submission['date'].strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        if submission['graded']:
                            st.metric("Score", f"{submission['total_score']:.1f}")
                        else:
                            st.warning("⏳ Grading...")
                    
                    with col3:
                        if submission['graded']:
                            col3a, col3b = st.columns(2)
                            with col3a:
                                st.success("✅ Graded")
                            with col3b:
                                if st.button("📄 PDF", key=f"pdf_{submission['submission_id']}"):
                                    try:
                                        # Generate PDF
                                        pdf_data = pdf_generator.generate_result_pdf(
                                            submission, test, 
                                            {"name": "Demo Student", "class_name": "10A"}
                                        )
                                        st.download_button(
                                            label="📥 Download Results PDF",
                                            data=pdf_data,
                                            file_name=f"{test['title']}_results.pdf",
                                            mime="application/pdf",
                                            key=f"dl_pdf_{submission['submission_id']}"
                                        )
                                    except Exception as e:
                                        st.error("Error generating PDF")
                        else:
                            st.info("🔄 Pending")
                    
                    st.divider()
            
            except Exception as e:
                print(f"Error displaying submission: {e}")
                continue
    
    except Exception as e:
        st.error("Error loading results. Please try again.")
        print(f"Error in show_my_results: {e}")

# Initialize session state
if 'selected_test_for_upload' not in st.session_state:
    st.session_state.selected_test_for_upload = None
if 'selected_test_for_view' not in st.session_state:
    st.session_state.selected_test_for_view = None
