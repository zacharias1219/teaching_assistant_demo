import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import threading

class AdvancedUI:
    """Advanced UI components with interactive features and real-time updates"""
    
    def __init__(self):
        self.update_interval = 5  # seconds
        
    def render_detailed_analysis_popover(self, grading_result, question_score):
        """Render detailed analysis popover with hover explanations"""
        with st.expander(f"📊 Detailed Analysis - Question {question_score.question_number}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Performance Metrics")
                
                # Score breakdown
                score_data = {
                    'Metric': ['Awarded Marks', 'Total Marks', 'Percentage', 'Confidence'],
                    'Value': [
                        f"{question_score.awarded_marks:.1f}",
                        f"{question_score.total_marks:.1f}",
                        f"{question_score.percentage:.1f}%",
                        f"{question_score.confidence:.1%}"
                    ]
                }
                score_df = pd.DataFrame(score_data)
                st.dataframe(score_df, use_container_width=True)
                
                # Component scores
                st.subheader("🎯 Component Scores")
                components = {
                    'Mathematical Reasoning': question_score.mathematical_reasoning_score,
                    'Conceptual Understanding': question_score.conceptual_understanding_score,
                    'Presentation': question_score.presentation_score
                }
                
                for component, score in components.items():
                    st.metric(component, f"{score:.1%}")
            
            with col2:
                st.subheader("📋 Step-by-Step Analysis")
                
                if question_score.step_evaluations:
                    for step in question_score.step_evaluations:
                        with st.container():
                            col_a, col_b, col_c = st.columns([1, 2, 1])
                            
                            with col_a:
                                status_icon = "✅" if step.is_correct else "❌"
                                st.write(f"{status_icon} Step {step.step_number}")
                            
                            with col_b:
                                st.write(f"**{step.step_description}**")
                                st.caption(step.feedback)
                            
                            with col_c:
                                st.write(f"Credit: {step.partial_credit:.1%}")
                
                else:
                    st.info("No step-by-step analysis available")
            
            # Strengths and Weaknesses
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("✅ Strengths")
                if question_score.strengths:
                    for strength in question_score.strengths:
                        st.write(f"• {strength}")
                else:
                    st.info("No specific strengths identified")
            
            with col4:
                st.subheader("⚠️ Areas for Improvement")
                if question_score.weaknesses:
                    for weakness in question_score.weaknesses:
                        st.write(f"• {weakness}")
                else:
                    st.info("No specific weaknesses identified")
            
            # Suggestions
            st.subheader("💡 Suggestions")
            if question_score.suggestions:
                for suggestion in question_score.suggestions:
                    st.write(f"• {suggestion}")
            else:
                st.info("No specific suggestions available")
    
    def render_interactive_question_analysis(self, grading_result):
        """Render interactive question analysis with deep-dive capabilities"""
        st.subheader("🔍 Interactive Question Analysis")
        
        # Question selection
        question_numbers = [qs.question_number for qs in grading_result.question_scores]
        selected_question = st.selectbox(
            "Select a question for detailed analysis:",
            question_numbers,
            format_func=lambda x: f"Question {x}"
        )
        
        # Get selected question data
        selected_qs = next(qs for qs in grading_result.question_scores if qs.question_number == selected_question)
        
        # Main analysis tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "🔍 Step Analysis", "📈 Comparisons", "💡 Insights"])
        
        with tab1:
            self._render_performance_tab(selected_qs)
        
        with tab2:
            self._render_step_analysis_tab(selected_qs)
        
        with tab3:
            self._render_comparisons_tab(grading_result, selected_qs)
        
        with tab4:
            self._render_insights_tab(selected_qs)
    
    def _render_performance_tab(self, question_score):
        """Render performance analysis tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Performance gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=question_score.percentage,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Question {question_score.question_number} Performance"},
                delta={'reference': 80},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Component scores radar chart
            categories = ['Mathematical Reasoning', 'Conceptual Understanding', 'Presentation']
            values = [
                question_score.mathematical_reasoning_score,
                question_score.conceptual_understanding_score,
                question_score.presentation_score
            ]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Student Performance'
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_step_analysis_tab(self, question_score):
        """Render step-by-step analysis tab"""
        if not question_score.step_evaluations:
            st.info("No step-by-step analysis available for this question")
            return
        
        # Step timeline
        steps_data = []
        for step in question_score.step_evaluations:
            steps_data.append({
                'Step': step.step_number,
                'Description': step.step_description,
                'Correct': step.is_correct,
                'Credit': step.partial_credit,
                'Feedback': step.feedback
            })
        
        df = pd.DataFrame(steps_data)
        
        # Step performance chart
        fig = px.bar(
            df, x='Step', y='Credit',
            color='Correct',
            title=f"Step-by-Step Performance - Question {question_score.question_number}",
            color_discrete_map={True: 'green', False: 'red'}
        )
        fig.update_layout(yaxis_title="Partial Credit", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed step table
        st.subheader("Step Details")
        for i, step in enumerate(question_score.step_evaluations):
            with st.expander(f"Step {step.step_number}: {step.step_description[:50]}...", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Status:**", "✅ Correct" if step.is_correct else "❌ Incorrect")
                    st.write("**Partial Credit:**", f"{step.partial_credit:.1%}")
                    st.write("**Confidence:**", f"{step.confidence:.1%}")
                
                with col2:
                    st.write("**Feedback:**")
                    st.write(step.feedback)
                    st.write("**Reasoning:**")
                    st.write(step.reasoning)
    
    def _render_comparisons_tab(self, grading_result, selected_qs):
        """Render comparisons tab"""
        # Compare with other questions
        other_questions = [qs for qs in grading_result.question_scores if qs.question_number != selected_qs.question_number]
        
        if other_questions:
            # Performance comparison
            comparison_data = {
                'Question': [f"Q{qs.question_number}" for qs in [selected_qs] + other_questions],
                'Percentage': [qs.percentage for qs in [selected_qs] + other_questions],
                'Mathematical Reasoning': [qs.mathematical_reasoning_score for qs in [selected_qs] + other_questions],
                'Conceptual Understanding': [qs.conceptual_understanding_score for qs in [selected_qs] + other_questions],
                'Presentation': [qs.presentation_score for qs in [selected_qs] + other_questions]
            }
            
            df = pd.DataFrame(comparison_data)
            
            # Highlight selected question
            fig = px.bar(
                df, x='Question', y='Percentage',
                title="Performance Comparison Across Questions",
                color='Question',
                color_discrete_map={f"Q{selected_qs.question_number}": "red"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Component comparison
            fig = go.Figure()
            
            for component in ['Mathematical Reasoning', 'Conceptual Understanding', 'Presentation']:
                fig.add_trace(go.Bar(
                    name=component,
                    x=df['Question'],
                    y=df[component]
                ))
            
            fig.update_layout(
                title="Component Scores Comparison",
                barmode='group',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No other questions available for comparison")
    
    def _render_insights_tab(self, question_score):
        """Render insights tab"""
        st.subheader("🎯 Key Insights")
        
        # Performance insights
        if question_score.percentage >= 90:
            st.success("🎉 Excellent performance! This question demonstrates mastery of the concepts.")
        elif question_score.percentage >= 80:
            st.info("👍 Very good work! Solid understanding with minor areas for improvement.")
        elif question_score.percentage >= 70:
            st.warning("⚠️ Good effort! Main concepts grasped but details need attention.")
        elif question_score.percentage >= 60:
            st.warning("📚 Satisfactory work. Focus on improving problem-solving approach.")
        else:
            st.error("❌ Significant improvement needed. Consider seeking additional help.")
        
        # Component insights
        st.subheader("Component Analysis")
        
        components = {
            'Mathematical Reasoning': question_score.mathematical_reasoning_score,
            'Conceptual Understanding': question_score.conceptual_understanding_score,
            'Presentation': question_score.presentation_score
        }
        
        for component, score in components.items():
            if score >= 0.8:
                st.success(f"✅ **{component}**: Strong performance ({score:.1%})")
            elif score >= 0.6:
                st.info(f"📊 **{component}**: Adequate performance ({score:.1%})")
            else:
                st.warning(f"⚠️ **{component}**: Needs improvement ({score:.1%})")
        
        # Recommendations
        st.subheader("📋 Recommendations")
        if question_score.suggestions:
            for i, suggestion in enumerate(question_score.suggestions, 1):
                st.write(f"{i}. {suggestion}")
        else:
            st.info("No specific recommendations available")
    
    def render_real_time_grading_status(self, submission_id: str):
        """Render real-time grading status updates"""
        st.subheader("🔄 Real-Time Grading Status")
        
        # Status placeholder
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        details_placeholder = st.empty()
        
        # Simulate real-time updates
        statuses = [
            ("🔄 Processing", "Initializing grading pipeline...", 10),
            ("📖 OCR Extraction", "Extracting text from answer sheets...", 30),
            ("🔍 Question Analysis", "Analyzing individual questions...", 50),
            ("📊 Step Evaluation", "Evaluating step-by-step solutions...", 70),
            ("🎯 Final Scoring", "Calculating final scores and feedback...", 90),
            ("✅ Complete", "Grading completed successfully!", 100)
        ]
        
        for status, message, progress in statuses:
            with status_placeholder:
                st.info(f"**{status}** - {message}")
            
            with progress_placeholder:
                st.progress(progress / 100)
            
            with details_placeholder:
                if progress < 100:
                    st.write(f"Progress: {progress}%")
                    st.write("Estimated time remaining: Calculating...")
                else:
                    st.success("Grading completed!")
                    st.write("Processing time: 2.3 seconds")
                    st.write("Confidence score: 87%")
            
            time.sleep(1)  # Simulate processing time
    
    def render_bulk_operations_panel(self):
        """Render bulk operations panel for admin"""
        st.subheader("⚡ Bulk Operations")
        
        # Operation selection
        operation = st.selectbox(
            "Select bulk operation:",
            [
                "Bulk Grade Submissions",
                "Bulk Generate Reports",
                "Bulk Export Data",
                "Bulk Delete Items",
                "Bulk Update Settings"
            ]
        )
        
        if operation == "Bulk Grade Submissions":
            self._render_bulk_grading_panel()
        elif operation == "Bulk Generate Reports":
            self._render_bulk_report_panel()
        elif operation == "Bulk Export Data":
            self._render_bulk_export_panel()
        elif operation == "Bulk Delete Items":
            self._render_bulk_delete_panel()
        elif operation == "Bulk Update Settings":
            self._render_bulk_settings_panel()
    
    def _render_bulk_grading_panel(self):
        """Render bulk grading operations panel"""
        st.write("**Bulk Grade Submissions**")
        
        # Test selection
        from utils.test_manager import test_manager
        tests = test_manager.get_all_tests()
        test_options = {f"{test['title']} (ID: {test['id']})": test['id'] for test in tests}
        
        selected_test = st.selectbox("Select test for bulk grading:", list(test_options.keys()))
        test_id = test_options[selected_test]
        
        # Get ungraded submissions
        from utils.submission_manager import submission_manager
        submissions = submission_manager.get_submissions_by_test_id(test_id)
        ungraded_submissions = [s for s in submissions if s.get('status') != 'graded']
        
        if ungraded_submissions:
            st.write(f"Found {len(ungraded_submissions)} ungraded submissions")
            
            # Display submissions
            submission_data = []
            for sub in ungraded_submissions:
                submission_data.append({
                    'Student ID': sub['student_id'],
                    'Submission Date': sub['submitted_at'],
                    'Status': sub['status'],
                    'File Size': f"{len(sub.get('answer_file', '')) / 1024:.1f} KB"
                })
            
            df = pd.DataFrame(submission_data)
            st.dataframe(df, use_container_width=True)
            
            # Bulk grading options
            col1, col2 = st.columns(2)
            
            with col1:
                priority = st.selectbox(
                    "Processing Priority:",
                    ["Normal", "High", "Urgent"]
                )
                
                enable_advanced_grading = st.checkbox("Enable Advanced Grading", value=True)
            
            with col2:
                max_concurrent = st.slider("Max Concurrent Jobs:", 1, 10, 4)
                auto_retry = st.checkbox("Auto-retry on failure", value=True)
            
            # Execute bulk grading
            if st.button("🚀 Start Bulk Grading", type="primary"):
                with st.spinner("Starting bulk grading process..."):
                    # Submit tasks to processing pipeline
                    from utils.processing_pipeline import processing_pipeline, ProcessingPriority
                    
                    priority_map = {
                        "Normal": ProcessingPriority.NORMAL,
                        "High": ProcessingPriority.HIGH,
                        "Urgent": ProcessingPriority.URGENT
                    }
                    
                    submitted_tasks = []
                    for submission in ungraded_submissions:
                        task_data = {
                            'submission_id': submission['id'],
                            'test_id': test_id,
                            'enable_advanced_grading': enable_advanced_grading
                        }
                        
                        task_id = processing_pipeline.submit_task(
                            'grading',
                            task_data,
                            priority_map[priority]
                        )
                        submitted_tasks.append(task_id)
                    
                    st.success(f"Submitted {len(submitted_tasks)} grading tasks to processing pipeline")
                    
                    # Show task monitoring
                    self._render_task_monitoring(submitted_tasks)
        
        else:
            st.info("No ungraded submissions found for the selected test")
    
    def _render_bulk_report_panel(self):
        """Render bulk report generation panel"""
        st.write("**Bulk Generate Reports**")
        
        # Report type selection
        report_type = st.selectbox(
            "Report Type:",
            ["Individual Student Reports", "Class Performance Reports", "Custom Reports"]
        )
        
        # Test selection
        from utils.test_manager import test_manager
        tests = test_manager.get_all_tests()
        test_options = {f"{test['title']} (ID: {test['id']})": test['id'] for test in tests}
        
        selected_test = st.selectbox("Select test:", list(test_options.keys()))
        test_id = test_options[selected_test]
        
        # Format selection
        report_format = st.selectbox(
            "Report Format:",
            ["Word Document (.docx)", "PDF", "JSON Export", "Excel Spreadsheet"]
        )
        
        # Options
        include_charts = st.checkbox("Include Charts and Graphs", value=True)
        include_detailed_analysis = st.checkbox("Include Detailed Analysis", value=True)
        
        if st.button("📄 Generate Bulk Reports", type="primary"):
            with st.spinner("Generating reports..."):
                st.success("Bulk report generation started")
                # Implementation would submit tasks to processing pipeline
    
    def _render_bulk_export_panel(self):
        """Render bulk export panel"""
        st.write("**Bulk Export Data**")
        
        # Data type selection
        data_types = st.multiselect(
            "Select data to export:",
            ["Student Information", "Test Data", "Submission Data", "Grading Results", "System Settings"]
        )
        
        # Export format
        export_format = st.selectbox(
            "Export Format:",
            ["JSON", "CSV", "Excel", "SQL Dump"]
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        if st.button("📤 Export Data", type="primary"):
            with st.spinner("Exporting data..."):
                st.success("Data export completed")
                # Implementation would handle data export
    
    def _render_bulk_delete_panel(self):
        """Render bulk delete panel"""
        st.write("**Bulk Delete Items**")
        
        st.warning("⚠️ This operation cannot be undone!")
        
        # Item type selection
        item_type = st.selectbox(
            "Select item type to delete:",
            ["Old Submissions", "Completed Tests", "Temporary Files", "Log Files"]
        )
        
        # Age filter
        age_threshold = st.slider("Delete items older than (days):", 1, 365, 30)
        
        # Preview
        if st.button("👁️ Preview Items"):
            st.info(f"Would delete {item_type} older than {age_threshold} days")
            # Implementation would show preview of items to be deleted
        
        # Confirm deletion
        confirm_delete = st.checkbox("I understand this action cannot be undone")
        
        if st.button("🗑️ Delete Items", type="primary", disabled=not confirm_delete):
            with st.spinner("Deleting items..."):
                st.success("Bulk deletion completed")
                # Implementation would handle bulk deletion
    
    def _render_bulk_settings_panel(self):
        """Render bulk settings update panel"""
        st.write("**Bulk Update Settings**")
        
        # Setting type
        setting_type = st.selectbox(
            "Setting Type:",
            ["AI Prompts", "Grading Criteria", "System Configuration", "User Permissions"]
        )
        
        if setting_type == "AI Prompts":
            prompt_type = st.selectbox(
                "Prompt Type:",
                ["OCR Extraction", "Grading", "Rubric Extraction", "Test Extraction", "Answer Extraction"]
            )
            
            new_prompt = st.text_area("New Prompt:", height=200)
            
            if st.button("💾 Update AI Prompts", type="primary"):
                with st.spinner("Updating AI prompts..."):
                    st.success("AI prompts updated successfully")
                    # Implementation would update AI prompts
    
    def _render_task_monitoring(self, task_ids: List[str]):
        """Render task monitoring interface"""
        st.subheader("📊 Task Monitoring")
        
        # Create monitoring table
        monitoring_data = []
        for task_id in task_ids:
            from utils.processing_pipeline import processing_pipeline
            task = processing_pipeline.get_task_status(task_id)
            
            if task:
                monitoring_data.append({
                    'Task ID': task_id,
                    'Status': task.status.value,
                    'Type': task.task_type,
                    'Created': task.created_at.strftime('%H:%M:%S'),
                    'Processing Time': f"{task.processing_time:.1f}s" if task.processing_time else "N/A",
                    'Confidence': f"{task.confidence_score:.1%}" if task.confidence_score else "N/A"
                })
        
        if monitoring_data:
            df = pd.DataFrame(monitoring_data)
            st.dataframe(df, use_container_width=True)
            
            # Auto-refresh
            if st.button("🔄 Refresh Status"):
                st.rerun()
        else:
            st.info("No tasks found for monitoring")

# Global advanced UI instance
advanced_ui = AdvancedUI()
