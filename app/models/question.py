from datetime import datetime
from app import db

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unanswered')  # unanswered, answered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='questions', lazy=True)
    auction = db.relationship('Auction', back_populates='questions', lazy=True)
    answers = db.relationship('Answer', back_populates='question', lazy=True)
    
    def __repr__(self):
        return f'<Question {self.id}>'
    
    @property
    def is_answered(self):
        return self.status == 'answered'
    
    def mark_as_answered(self):
        self.status = 'answered'
        self.updated_at = datetime.utcnow()

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', back_populates='answers', lazy=True)
    user = db.relationship('User', back_populates='answers', lazy=True)
    
    def __repr__(self):
        return f'<Answer {self.id}>'