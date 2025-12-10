import os
import sys
import random
import hashlib
import json
import time
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from textwrap import dedent

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================
HOST_SERVIDOR = "localhost" # <--- SEU IP AQUI
DB_USER = "root"
DB_PASS = "123456"
DB_NAME = "tech_quiz"

# Cores ANSI
C_R = "\033[0m"      # Reset
C_C = "\033[96m"     # Ciano
C_G = "\033[92m"     # Verde
C_Y = "\033[93m"     # Amarelo
C_E = "\033[91m"     # Vermelho (Erro)
C_B = "\033[1m"      # Negrito

# ==============================================================================
# SETUP DO BANCO AUTOMÁTICO
# ==============================================================================
def setup_database():
    print(f"{C_Y}📡 Conectando ao servidor...{C_R}")
    try:
        # Conecta sem banco para criar se não existir
        root_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{HOST_SERVIDOR}"
        root_engine = create_engine(root_url, echo=False)
        with root_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
        
        # Conecta ao banco correto
        db_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{HOST_SERVIDOR}/{DB_NAME}"
        engine = create_engine(db_url, echo=False, pool_recycle=3600)
        return engine
    except Exception as e:
        print(f"\n{C_E}❌ ERRO CRÍTICO: Não foi possível conectar/criar o banco.{C_R}")
        print(f"Detalhe: {e}")
        sys.exit()

engine = setup_database()
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# ==============================================================================
# MODELOS
# ==============================================================================
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    attempts = relationship("UserQuestionAttempt", back_populates="user")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    difficulty = Column(String(50))
    question_text = Column(Text, nullable=False)
    correct_answer = Column(String(255), nullable=False)
    incorrect_answers = Column(Text, nullable=False)

class UserQuestionAttempt(Base):
    __tablename__ = 'attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    is_correct = Column(Integer)
    category = Column(String(100))
    user = relationship("User", back_populates="attempts") 
    question = relationship("Question")

Base.metadata.create_all(engine)

# ==============================================================================
# INTERFACE & UTILITÁRIOS
# ==============================================================================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear()
    print(f"{C_C}")
    print(r"""
  _______ ______ _____ _    _   ____  _    _ _____ ______ 
 |__   __|  ____/ ____| |  | | / __ \| |  | |_   _|___  / 
    | |  | |__ | |    | |__| || |  | | |  | | | |    / /  
    | |  |  __|| |    |  __  || |  | | |  | | | |   / /   
    | |  | |___| |____| |  | || |__| | |__| |_| |_ / /__  
    |_|  |______\_____|_|  |_| \___\_\\____/|_____/_____| 
                                      SENAI EDITION v2.0
    """)
    print(f"{C_R}" + "="*60 + "\n")

def loading(text):
    sys.stdout.write(text)
    for _ in range(3):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.3)
    print("")

def seed_database():
    filename = 'questoes.json'
    if not os.path.exists(filename): return

    try:
        # Se o banco já tem questões, não faz nada para não pesar a rede
        if session.query(Question).count() > 0: return

        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        loading(f"{C_Y}🔄 Sincronizando banco de dados")
        for item in data:
            exists = session.query(Question).filter(Question.question_text == item['question_text']).first()
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
        if count > 0: print(f"{C_G}✅ {count} novas questões adicionadas!{C_R}")
            
    except Exception:
        session.rollback()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ==============================================================================
# LÓGICA
# ==============================================================================
def register():
    header()
    print(f"{C_B}>>> CRIAÇÃO DE CONTA{C_R}")
    username = input("👤 Usuário: ").strip()
    
    if session.query(User).filter_by(username=username).first():
        print(f"\n{C_E}⚠️  Usuário já existe.{C_R}")
        time.sleep(2)
        return None
    
    password = input("🔒 Senha: ").strip()
    new_user = User(username=username, password_hash=hash_password(password))
    session.add(new_user)
    session.commit()
    print(f"\n{C_G}✅ Conta criada com sucesso!{C_R}")
    time.sleep(2)
    return new_user

def login():
    header()
    print(f"{C_B}>>> LOGIN{C_R}")
    username = input("👤 Usuário: ").strip()
    password = input("🔒 Senha: ").strip()
    
    user = session.query(User).filter_by(username=username, password_hash=hash_password(password)).first()
    if user:
        return user
    else:
        print(f"\n{C_E}❌ Credenciais inválidas.{C_R}")
        time.sleep(2)
        return None

def play_game(user):
    loading(f"\n{C_Y}🎲 Sorteando questões")
    try:
        questions = session.query(Question).order_by(func.random()).limit(5).all()
    except:
        print(f"{C_E}Erro de conexão.{C_R}")
        return

    if not questions:
        print(f"{C_E}⚠️ Banco de questões vazio.{C_R}")
        time.sleep(2)
        return

    score = 0
    for i, q in enumerate(questions):
        header()
        print(f"{C_B}QUESTÃO {i+1} de 5{C_R}")
        print(f"{C_C}[{q.category} | {q.difficulty}]{C_R}")
        print(f"\n{C_B}{q.question_text}{C_R}\n")
        
        options = json.loads(q.incorrect_answers)
        options.append(q.correct_answer)
        random.shuffle(options)
        
        for idx, opt in enumerate(options):
            print(f" {C_Y}{idx + 1}.{C_R} {opt}")
            
        try:
            answ = int(input(f"\n{C_C}➤ Sua resposta:{C_R} "))
            if options[answ - 1] == q.correct_answer:
                print(f"\n{C_G}✅ CORRETO!{C_R}")
                score += 1
                correct = 1
            else:
                print(f"\n{C_E}❌ ERRADO! Era: {q.correct_answer}{C_R}")
                correct = 0
            
            session.add(UserQuestionAttempt(
                user_id=user.id, question_id=q.id, is_correct=correct, category=q.category
            ))
            session.commit()
            time.sleep(1.5)
            
        except (ValueError, IndexError):
            print(f"\n{C_E}⚠️ Resposta inválida.{C_R}")
            time.sleep(1)

    header()
    print(f"{C_B}🏁 FIM DA RODADA{C_R}")
    print(f"Você acertou: {C_G}{score}/5{C_R}")
    input("\nPressione Enter para voltar...")

def show_analytics(user):
    header()
    total = session.query(UserQuestionAttempt).filter_by(user_id=user.id).count()
    correct = session.query(UserQuestionAttempt).filter_by(user_id=user.id, is_correct=1).count()
    
    print(f"{C_B}📊 ESTATÍSTICAS: {user.username.upper()}{C_R}")
    if total > 0:
        perc = (correct/total)*100
        color = C_G if perc >= 70 else (C_Y if perc >= 50 else C_E)
        print(f"\nTaxa de Acerto: {color}{perc:.1f}%{C_R} ({correct}/{total})")
        
        cats = session.query(
            UserQuestionAttempt.category, 
            func.count(UserQuestionAttempt.id), 
            func.sum(UserQuestionAttempt.is_correct)
        ).filter_by(user_id=user.id).group_by(UserQuestionAttempt.category).all()
        
        print("\nDesempenho por Matéria:")
        for cat, t, c in cats:
            c = int(c) if c else 0
            print(f" • {cat}: {c}/{t}")
    else:
        print("Nenhum dado encontrado.")
    input("\nEnter para voltar...")

def show_ranking():
    header()
    print(f"{C_Y}🏆 TOP 10 - RANKING GLOBAL{C_R}\n")
    ranking = session.query(
        User.username, 
        func.sum(UserQuestionAttempt.is_correct)
    ).join(UserQuestionAttempt).group_by(User.id).order_by(func.sum(UserQuestionAttempt.is_correct).desc()).limit(10).all()
    
    if not ranking:
        print("Ranking vazio.")
    
    for i, (name, pts) in enumerate(ranking):
        pts = int(pts) if pts else 0
        medal = "🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else f"{i+1}."))
        print(f" {medal} {name:<15} {C_G}{pts} pts{C_R}")
        
    input("\nEnter para voltar...")

def main_menu():
    seed_database()
    user = None
    
    while True:
        header()
        if user:
            print(f"Bem-vindo, {C_C}{user.username}{C_R}!\n")
            print(f"1. {C_G}🎮 Jogar Agora{C_R}")
            print(f"2. {C_C}📊 Minhas Estatísticas{C_R}")
            print(f"3. {C_Y}🏆 Ranking Global{C_R}")
            print(f"4. 🚪 Logout")
            print(f"0. ❌ Sair")
        else:
            print(f"1. 🔑 Login")
            print(f"2. 📝 Criar Conta")
            print(f"0. ❌ Sair")
            
        op = input(f"\n{C_B}Opção:{C_R} ")
        
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
