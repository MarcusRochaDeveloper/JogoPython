import os
import time
import sys
import random
import hashlib
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ============================================================================== 
# CONFIGURAÇÃO
# ============================================================================== 
HOST_SERVIDOR = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "tech_quiz"
DB_PORT = 5506  

# Cores ANSI
C_R = "\033[0m"      # Reset
C_C = "\033[96m"     # Ciano
C_G = "\033[92m"     # Verde
C_Y = "\033[93m"     # Amarelo
C_E = "\033[91m"     # Vermelho
C_M = "\033[95m"     # Magenta
C_B = "\033[1m"      # Bold

# ============================================================================== 
# SETUP DO BANCO
# ============================================================================== 
def setup_database():
    print(f"{C_Y}📡 Conectando ao servidor...{C_R}")
    try:
        root_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{HOST_SERVIDOR}:{DB_PORT}"
        root_engine = create_engine(root_url, echo=False)

        with root_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))

        db_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{HOST_SERVIDOR}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url, echo=False, pool_recycle=3600)
        return engine

    except Exception as e:
        print(f"{C_E}❌ ERRO: Não foi possível conectar ao banco.{C_R}")
        print(e)
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
    username = Column(String(50), unique=True)
    password_hash = Column(String(255))
    attempts = relationship("UserQuestionAttempt", back_populates="user")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    category = Column(String(100))
    difficulty = Column(String(50))
    question_text = Column(Text)
    correct_answer = Column(String(255))
    incorrect_answers = Column(Text)

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
# INTERFACE / VISUAL
# ============================================================================== 
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear()
    print(f"{C_M}{C_B}")
    print(r"""   
                                                                                                                                                                                                                                                                                                                                                  
████████╗███████╗ ██████╗██╗  ██╗ ██████╗ ██╗   ██╗██╗███████╗
╚══██╔══╝██╔════╝██╔════╝██║  ██║██╔═══██╗██║   ██║██║╚══███╔╝
   ██║   █████╗  ██║     ███████║██║   ██║██║   ██║██║  ███╔╝ 
   ██║   ██╔══╝  ██║     ██╔══██║██║▄▄ ██║██║   ██║██║ ███╔╝  
   ██║   ███████╗╚██████╗██║  ██║╚██████╔╝╚██████╔╝██║███████╗
   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝    
                                                                                                                                                                                                                                                                                                                                                                                                     
    """)
    print(C_R)

def loading(msg):
    print(C_Y + msg + C_R, end="")
    for _ in range(3):
        print(".", end="")
        sys.stdout.flush()
        time.sleep(0.25)
    print()

# ============================================================================== 
# JSON SYNC
# ============================================================================== 
def export_questions_to_json():
    data = []
    questions = session.query(Question).all()

    for q in questions:
        data.append({
            "category": q.category,
            "difficulty": q.difficulty,
            "question_text": q.question_text,
            "correct_answer": q.correct_answer,
            "incorrect_answers": json.loads(q.incorrect_answers)
        })

    with open("questoes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def seed_database():
    if not os.path.exists("questoes.json"):
        return
    if session.query(Question).count() > 0:
        return

    with open("questoes.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        q = Question(
            category=item["category"],
            difficulty=item["difficulty"],
            question_text=item["question_text"],
            correct_answer=item["correct_answer"],
            incorrect_answers=json.dumps(item["incorrect_answers"])
        )
        session.add(q)

    session.commit()

# ============================================================================== 
# LOGIN, REGISTRO
# ============================================================================== 
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register():
    header()
    print(C_B + "📝 CRIAR CONTA\n" + C_R)

    user = input("Usuário: ")
    if session.query(User).filter_by(username=user).first():
        print(C_E + "⚠ Usuário já existe!" + C_R)
        time.sleep(2)
        return None

    pwd = input("Senha: ")

    u = User(username=user, password_hash=hash_password(pwd))
    session.add(u)
    session.commit()

    print(C_G + "✔ Conta criada!" + C_R)
    time.sleep(1.5)
    return u

def login():
    header()
    print(C_B + "🔑 LOGIN\n" + C_R)

    user = input("Usuário: ")
    pwd = input("Senha: ")

    u = session.query(User).filter_by(
        username=user,
        password_hash=hash_password(pwd)
    ).first()

    if u:
        return u

    print(C_E + "❌ Credenciais inválidas" + C_R)
    time.sleep(2)
    return None

# ============================================================================== 
# LOGIN DO PROFESSOR
# ============================================================================== 
def admin_login():
    header()
    print(C_B + "🛠 LOGIN DO PROFESSOR\n" + C_R)

    user = input("Usuário: ")
    pwd = input("Senha: ")

    if user == "Professor" and pwd == "Administrador":
        print(C_G + "✅ Acesso liberado!" + C_R)
        time.sleep(1)
        return True

    print(C_E + "❌ Credenciais incorretas!" + C_R)
    time.sleep(2)
    return False

# ============================================================================== 
# JOGO  
# ============================================================================== 
def play_game(user):
    loading("Sorteando questões")
    questions = session.query(Question).order_by(func.random()).limit(10).all()

    if not questions:
        print(C_E + "Sem questões no banco!" + C_R)
        return

    score = 0

    for i, q in enumerate(questions):
        opts = json.loads(q.incorrect_answers)
        opts.append(q.correct_answer)
        random.shuffle(opts)

        while True:
            header()
            print(f"{C_B}QUESTÃO {i+1}/10{C_R}")
            print(f"{C_C}[{q.category} - {q.difficulty}]{C_R}\n")
            print(q.question_text + "\n")

            for idx, op in enumerate(opts):
                print(f"{C_Y}{idx+1}.{C_R} {op}")

            ans = input("\nResposta (1-4): ").strip()

            if ans == "":
                print(f"{C_E}⚠ Você precisa escolher uma alternativa!{C_R}")
                time.sleep(3)
                continue
            if not ans.isdigit() or int(ans) < 1 or int(ans) > len(opts):
                print(f"{C_E}⚠ Opção inválida!{C_R}")
                time.sleep(3)
                continue

            ans = int(ans)
            break

        correct = (opts[ans-1] == q.correct_answer)

        header()
        print(f"{C_B}QUESTÃO {i+1}/10{C_R}")
        print(f"{C_C}[{q.category} - {q.difficulty}]{C_R}\n")
        print(q.question_text + "\n")
        for idx, op in enumerate(opts):
            mark = ""
            if op == q.correct_answer:
                mark = f" {C_G}✔ CORRETA{C_R}" if correct else f" {C_G}✔ CORRETA{C_R}"
            elif idx+1 == ans and not correct:
                mark = f" {C_E}✘ SUA RESPOSTA{C_R}"
            print(f"{C_Y}{idx+1}.{C_R} {op}{mark}")

        if correct:
            print(C_G + "\n✔ Correto!" + C_R)
            score += 1
        else:
            print(C_E + "\n✘ Errado!" + C_R)
            print(f"{C_C}A resposta correta era: {q.correct_answer}{C_R}")

        session.add(UserQuestionAttempt(
            user_id=user.id,
            question_id=q.id,
            is_correct=1 if correct else 0,
            category=q.category
        ))
        session.commit()
        time.sleep(5)

    header()
    print(f"🔥 Resultado final: {C_G}{score}/10{C_R}")
    input("\nEnter para voltar...")

# ============================================================================== 
# ESTATÍSTICAS
# ============================================================================== 
def show_analytics(user):
    header()
    print(f"{C_B}📊 Suas estatísticas{C_R}")

    total = session.query(UserQuestionAttempt).filter_by(user_id=user.id).count()
    correct = session.query(UserQuestionAttempt).filter_by(user_id=user.id, is_correct=1).count()

    if total == 0:
        print("Sem dados ainda...")
        input("Enter...")
        return

    print(f"\nTaxa de acerto: {C_G}{(correct/total)*100:.1f}%{C_R}")

    input("\nEnter para voltar...")

# ============================================================================== 
# RANKING
# ============================================================================== 
def show_ranking():
    header()
    print(f"{C_Y}🏆 RANKING GLOBAL\n{C_R}")

    ranking = session.query(
        User.username, func.sum(UserQuestionAttempt.is_correct)
    ).join(UserQuestionAttempt).group_by(User.id).order_by(func.sum(UserQuestionAttempt.is_correct).desc()).limit(10).all()

    if not ranking:
        print("Ranking vazio.")
        input("Enter...")
        return

    for i, (name, pts) in enumerate(ranking, 1):
        print(f"{i}. {name} — {pts} pts")

    input("\nEnter para voltar...")

# ============================================================================== 
# MENU DO PROFESSOR
# ============================================================================== 
def admin_menu():
    while True:
        header()
        print(f"{C_B}🛠 MENU DO PROFESSOR{C_R}\n")
        print("1. ➕ Adicionar questão")
        print("2. ✏ Editar questão")
        print("3. ❌ Remover questão")
        print("4. 📋 Listar questões")
        print("0. 🔙 Voltar")

        op = input("\nOpção: ")

        if op == "1": admin_add_question()
        elif op == "2": admin_edit_question()
        elif op == "3": admin_remove_question()
        elif op == "4": admin_list_questions()
        elif op == "0": return

def admin_list_questions():
    header()
    print(f"{C_B}📋 QUESTÕES REGISTRADAS\n{C_R}")
    qs = session.query(Question).all()

    for q in qs:
        print(f"{q.id}. [{q.category}] {q.question_text[:60]}...")

    input("\nEnter para voltar...")

def admin_add_question():
    header()
    print(f"{C_B}➕ NOVA QUESTÃO{C_R}")

    cat = input("Categoria: ")
    diff = input("Dificuldade: ")
    text = input("Pergunta: ")
    correct = input("Resposta correta: ")

    print("\n3 respostas incorretas:")
    inc = [input(f"- {i+1}: ") for i in range(3)]

    q = Question(
        category=cat, difficulty=diff,
        question_text=text,
        correct_answer=correct,
        incorrect_answers=json.dumps(inc)
    )
    session.add(q)
    session.commit()
    export_questions_to_json()

    print(C_G + "✔ Questão adicionada!" + C_R)
    input("Enter...")

def admin_edit_question():
    admin_list_questions()
    try:
        qid = int(input("ID da questão: "))
    except:
        return

    q = session.query(Question).filter_by(id=qid).first()
    if not q:
        print(C_E + "Questão não encontrada!" + C_R)
        time.sleep(2)
        return

    header()
    print(f"{C_B}✏ EDITAR — ID {q.id}{C_R}\n")

    q.category = input(f"Categoria [{q.category}]: ") or q.category
    q.difficulty = input(f"Dificuldade [{q.difficulty}]: ") or q.difficulty
    q.question_text = input(f"Pergunta [{q.question_text}]: ") or q.question_text
    q.correct_answer = input(f"Resposta correta [{q.correct_answer}]: ") or q.correct_answer

    old_inc = json.loads(q.incorrect_answers)
    new_inc = []
    for i in range(3):
        v = input(f"Incorreta {i+1} [{old_inc[i]}]: ")
        new_inc.append(v if v else old_inc[i])

    q.incorrect_answers = json.dumps(new_inc)
    session.commit()
    export_questions_to_json()

    print(C_G + "✔ Atualizada!" + C_R)
    input("Enter...")

def admin_remove_question():
    admin_list_questions()
    try:
        qid = int(input("ID da questão: "))
    except:
        return

    q = session.query(Question).filter_by(id=qid).first()
    if not q:
        print(C_E + "Questão não encontrada!" + C_R)
        time.sleep(2)
        return

    session.delete(q)
    session.commit()
    export_questions_to_json()

    print(C_G + "✔ Removida!" + C_R)
    input("Enter...")

# ============================================================================== 
# MENU PRINCIPAL
# ============================================================================== 
def main_menu():
    seed_database()
    user = None
    
    while True:
        header()
        print(f"{C_B}MENU PRINCIPAL{C_R}\n")

        if user:
            print("1. 🎮 Jogar")
            print("2. 📊 Minhas Estatísticas")
            print("3. 🏆 Ranking")
            print("4. 🚪 Logout")
            print("0. ❌ Sair")
        else:
            print("1. 🔑 Login")
            print("2. 📝 Criar Conta")
            print("3. 🛠 Login do Professor")
            print("0. ❌ Sair")

        op = input("\nOpção: ")

        if not user:
            if op == "1": user = login()
            elif op == "2": user = register()
            elif op == "3":
                if admin_login():
                    admin_menu()
            elif op == "0": sys.exit()
        else:
            if op == "1": play_game(user)
            elif op == "2": show_analytics(user)
            elif op == "3": show_ranking()
            elif op == "4": user = None
            elif op == "0": sys.exit()

# ============================================================================== 
# START
# ============================================================================== 
if __name__ == "__main__":
    main_menu()
