import os
import sys
import random
import hashlib
import json
import time
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from textwrap import dedent

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    attempts = relationship("UserQuestionAttempt", back_populates="user")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    difficulty = Column(String)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    incorrect_answers = Column(Text, nullable=False)

class UserQuestionAttempt(Base):
    __tablename__ = 'attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    is_correct = Column(Integer)
    category = Column(String)
    user = relationship("User", back_populates="attempts") 
    question = relationship("Question")

engine = create_engine('sqlite:///tech_quiz.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

def init_db():
    Base.metadata.create_all(engine)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def seed_database():
    filename = 'questoes.json'
    if not os.path.exists(filename):
        print(f"Aviso: Arquivo {filename} não encontrado. O banco ficará vazio.")
        time.sleep(2)
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        for item in data:
            exists = session.query(Question).filter_by(question_text=item['question_text']).first()
            if not exists:
                q = Question(
                    category=item['category'],
                    difficulty=item['difficulty'],
                    question_text=item['question_text'],
                    correct_answer=item['correct_answer'],
                    incorrect_answers=json.dumps(item['incorrect_answers'])
                )
                session.add(q)
                count += 1
        
        session.commit()
        if count > 0:
            print(f"Carregadas {count} novas questões do arquivo JSON.")
            time.sleep(1)
            
    except Exception as e:
        session.rollback()
        print(f"Erro ao ler JSON: {e}")
        time.sleep(2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register():
    clear_screen()
    print(dedent("""
    ╔════════════════════════╗
    ║      🚪 CADASTRO       ║
    ╚════════════════════════╝
    """))
    username = input("👤 Usuário: ").strip()
    
    try:
        if session.query(User).filter_by(username=username).first():
            print("❌ Erro: Usuário já existe.")
            input("Enter para continuar...")
            return None
        
        password = input("🔒 Senha: ").strip()
        new_user = User(username=username, password_hash=hash_password(password))
        session.add(new_user)
        session.commit()
        print("✅ Cadastro realizado! Faça login.")
        input("Enter para continuar...")
        return new_user
    except Exception:
        session.rollback()
        print("Erro no cadastro.")
        input("Enter...")
        return None

def login():
    clear_screen()
    print(dedent("""
    ╔════════════════════════╗
    ║         🔑 LOGIN        ║
    ╚════════════════════════╝
    """))
    username = input("👤 Usuário: ").strip()
    password = input("🔒 Senha: ").strip()
    
    try:
        user = session.query(User).filter_by(username=username, password_hash=hash_password(password)).first()
        if user:
            return user
        else:
            print("❌ Credenciais inválidas.")
            input("Enter para continuar...")
            return None
    except Exception:
        session.rollback()
        print("Erro no login.")
        input("Enter...")
        return None

def play_game(user):
    clear_screen()
    print(dedent("""
    ╔═════════════════════════════╗
    ║       🕹️ INICIANDO QUIZ      ║
    ╚═════════════════════════════╝
    """))
    
    try:
        questions = session.query(Question).order_by(func.random()).limit(5).all()
    except Exception:
        session.rollback()
        return
    
    if not questions:
        print("⚠️ Banco vazio. Verifique o arquivo questoes.json.")
        input("Enter...")
        return

    score = 0
    for i, q in enumerate(questions):
        print(f"\n--- PERGUNTA {i+1} ---")
        print(f"[Matéria: {q.category} | Nível: {q.difficulty}]")
        print(f"❓ {q.question_text}")
        
        options = json.loads(q.incorrect_answers)
        options.append(q.correct_answer)
        random.shuffle(options)
        
        for idx, opt in enumerate(options):
            print(f"   {idx + 1}. {opt}")
            
        try:
            answ_str = input("\nSua resposta (número): ")
            if not answ_str.isdigit():
                raise ValueError
            answ = int(answ_str)
            
            selected = options[answ - 1]
            if selected == q.correct_answer:
                print("✅ CORRETO!")
                score += 1
                correct = 1
            else:
                print(f"❌ ERRADO! A resposta era: {q.correct_answer}")
                correct = 0
            
            attempt = UserQuestionAttempt(
                user_id=user.id, question_id=q.id, is_correct=correct, category=q.category
            )
            session.add(attempt)
            session.commit()
            
        except (ValueError, IndexError):
            print("⚠️ Entrada inválida. Contado como erro.")
            try:
                session.add(UserQuestionAttempt(user_id=user.id, question_id=q.id, is_correct=0, category=q.category))
                session.commit()
            except:
                session.rollback()

        time.sleep(1.5)
        clear_screen()

    print(f"🏁 FIM! Você acertou {score}/5.")
    input("Enter para voltar...")

def show_analytics(user):
    clear_screen()
    try:
        total = session.query(UserQuestionAttempt).filter_by(user_id=user.id).count()
        correct = session.query(UserQuestionAttempt).filter_by(user_id=user.id, is_correct=1).count()
        
        print(f"📊 ESTATÍSTICAS DE {user.username.upper()}")
        if total > 0:
            print(f"Acertos: {correct}/{total} ({(correct/total)*100:.1f}%)")
            
            attempts = session.query(UserQuestionAttempt).filter_by(user_id=user.id).all()
            cats = {}
            for a in attempts:
                if a.category not in cats: cats[a.category] = {'ok':0, 'total':0}
                cats[a.category]['total'] += 1
                if a.is_correct: cats[a.category]['ok'] += 1
            
            print("\nDesempenho por Matéria:")
            for c, d in cats.items():
                print(f"- {c}: {d['ok']}/{d['total']}")
        else:
            print("Nenhum jogo registrado.")
            
    except Exception:
        session.rollback()
        
    input("\nEnter para voltar...")

def show_ranking():
    clear_screen()
    print("🏆 TOP 10 JOGADORES")
    try:
        ranking = session.query(User.username, func.sum(UserQuestionAttempt.is_correct)).join(UserQuestionAttempt).group_by(User.id).order_by(func.sum(UserQuestionAttempt.is_correct).desc()).limit(10).all()
        
        for i, (name, pts) in enumerate(ranking):
            pts = pts if pts else 0
            print(f"{i+1}. {name} - {pts} pts")
    except Exception:
        session.rollback()
        
    input("\nEnter para voltar...")

def main_menu():
    session.rollback()
    init_db()
    seed_database()
    
    user = None
    
    while True:
        clear_screen()
        print("=== 🚀 TECH QUIZ MASTER (LOCAL) ===")
        if user:
            print(f"Olá, {user.username}")
            print("1. Jogar")
            print("2. Ver Estatísticas")
            print("3. Ranking")
            print("4. Logout")
            print("0. Sair")
        else:
            print("1. Login")
            print("2. Criar Conta")
            print("0. Sair")
            
        op = input("\nOpção: ")
        
        if not user:
            if op == '1': user = login()
            elif op == '2': user = register()
            elif op == '0': sys.exit()
        else:
            if op == '1': play_game(user)
            elif op == '2': show_analytics(user)
            elif op == '3': show_ranking()
            elif op == '4': user = None
            elif op == '0': sys.exit()

if __name__ == "__main__":
    main_menu()