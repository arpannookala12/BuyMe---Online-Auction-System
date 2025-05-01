from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Question, Answer, User
from datetime import datetime
from sqlalchemy import or_

question_bp = Blueprint('question', __name__, url_prefix='/support')

@question_bp.route('/')
def index():
    """Show support main page with FAQ and option to ask questions"""
    # Get most recent answered questions for FAQ section
    recent_questions = Question.query.filter_by(status='answered').order_by(Question.updated_at.desc()).limit(5).all()
    return render_template('support/index.html', recent_questions=recent_questions)

@question_bp.route('/questions')
def browse():
    """Browse all questions"""
    # Get search and filter parameters
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Question.query
    
    # Apply search if provided
    if search:
        query = query.filter(or_(
            Question.title.ilike(f'%{search}%'),
            Question.content.ilike(f'%{search}%')
        ))
    
    # Apply status filter
    if status != 'all':
        query = query.filter_by(status=status)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Question.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Question.created_at.asc())
    elif sort == 'recent_activity':
        query = query.order_by(Question.updated_at.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    questions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('support/browse.html', 
                          questions=questions, 
                          search=search, 
                          status=status, 
                          sort=sort)

@question_bp.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    """Ask a new question"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Validate input
        if not title or not content:
            flash('Title and content are required', 'danger')
            return render_template('support/ask.html')
        
        # Create question
        question = Question(
            user_id=current_user.id,
            title=title,
            content=content,
            status='open'
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Your question has been submitted successfully', 'success')
        return redirect(url_for('question.view', id=question.id))
    
    return render_template('support/ask.html')

@question_bp.route('/question/<int:id>')
def view(id):
    """View a question and its answers"""
    question = Question.query.get_or_404(id)
    answers = Answer.query.filter_by(question_id=id).order_by(Answer.created_at.asc()).all()
    
    return render_template('support/view.html', question=question, answers=answers)

@question_bp.route('/question/<int:id>/answer', methods=['POST'])
@login_required
def answer_question(id):
    """Answer a question (for customer reps only)"""
    if not current_user.is_customer_rep():
        flash('Only customer representatives can answer questions', 'danger')
        return redirect(url_for('question.view', id=id))
    
    question = Question.query.get_or_404(id)
    content = request.form.get('content')
    
    if not content:
        flash('Answer content is required', 'danger')
        return redirect(url_for('question.view', id=id))
    
    # Create answer
    answer = Answer(
        question_id=id,
        rep_id=current_user.id,
        content=content
    )
    
    # Update question status
    question.status = 'answered'
    question.updated_at = datetime.utcnow()
    
    db.session.add(answer)
    db.session.commit()
    
    flash('Your answer has been posted successfully', 'success')
    return redirect(url_for('question.view', id=id))

@question_bp.route('/my-questions')
@login_required
def my_questions():
    """View my questions"""
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.created_at.desc()).all()
    return render_template('support/my_questions.html', questions=questions)

@question_bp.route('/customer-rep/questions')
@login_required
def rep_questions():
    """Show questions for customer representatives to answer"""
    if not current_user.is_customer_rep() and not current_user.is_admin():
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    status = request.args.get('status', 'open')
    
    # Base query
    query = Question.query
    
    # Apply status filter
    if status != 'all':
        query = query.filter_by(status=status)
    
    # Sort by most recent
    questions = query.order_by(Question.created_at.desc()).all()
    
    return render_template('support/rep_questions.html', questions=questions, status=status)

@question_bp.route('/search')
def search():
    """Search questions by keyword"""
    query = request.args.get('q', '')
    if not query:
        return render_template('support/search.html', results=None, query=None)
    
    # Search questions
    results = Question.query.filter(or_(
        Question.title.ilike(f'%{query}%'),
        Question.content.ilike(f'%{query}%')
    )).order_by(Question.updated_at.desc()).all()
    
    return render_template('support/search.html', results=results, query=query)