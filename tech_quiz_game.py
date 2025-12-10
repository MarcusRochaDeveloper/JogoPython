import os
import sys
import random
import hashlib
import requests
import json
import html
import time
import re 
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from textwrap import dedent
from deep_translator import GoogleTranslator

# ==========================================
# 0. CONFIGURAÇÕES E GLOSSÁRIO
# ==========================================


PROTECTED_TERMS = [
    "String", "Integer", "Float", "Boolean", "Array", "List", "Tuple", "Dict", 
    "Object", "Class", "Method", "Function", "Loop", "While", "For", "If", "Else",
    "Framework", "Library", "API", "JSON", "XML", "HTML", "CSS", "SQL", "Database",
    "Query", "Select", "Insert", "Update", "Delete", "Commit", "Rollback",
    "Git", "GitHub", "Push", "Pull", "Merge", "Branch",
    "Server", "Client", "Host", "IP", "TCP", "UDP", "HTTP", "HTTPS", "DNS", "FTP",
    "Socket", "Port", "Firewall", "Router", "Switch", "Gateway",
    "Thread", "Process", "CPU", "RAM", "ROM", "BIOS", "Kernel", "Shell", "Bash",
    "Bug", "Debug", "Compiler", "Interpreter", "IDE", "SaaS", "PaaS", "IaaS",
    "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin",
    "Docker", "Kubernetes", "Container", "Linux", "Windows", "MacOS", "Android",
    "Backend", "Frontend", "Fullstack", "Scrum", "Agile", "Kanban", "Sprint",
    "Cache", "Cookie", "Token", "Hash", "Encryption", "Algorithm", "Null", "Void"
]


try:
    translator = GoogleTranslator(source='auto', target='pt')
except Exception as e:
    print(f"Erro ao iniciar tradutor: {e}")
    translator = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def translate_text(text):
    
    if not text:
        return ""
    
    clean_text = html.unescape(text)
    
    if not translator:
        return clean_text

   
    temp_map = {}
    protected_text = clean_text
    
  
    sorted_terms = sorted(PROTECTED_TERMS, key=len, reverse=True)
    
    for i, term in enumerate(sorted_terms):
    
        placeholder = f"__PROTECTED_{i}__"
        
        
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        
        if pattern.search(protected_text):
            temp_map[placeholder] = term 
            protected_text = pattern.sub(placeholder, protected_text)


    try:
        translated = translator.translate(protected_text)
        if not translated:
            return clean_text
    except Exception:
        return clean_text 

  
    final_text = translated
    for placeholder, original_term in temp_map.items():
      
        final_text = final_text.replace(placeholder, original_term)
        
    return final_text

# ==========================================
# 1. MODELAGEM DO BANCO DE DADOS (ORM)
# ==========================================
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

# ==========================================
# 2. POPULAÇÃO DO BANCO (SEEDER)
# ==========================================
def fetch_and_translate_questions(batch_size=50):
    url = f"https://opentdb.com/api.php?amount={batch_size}&category=18&type=multiple"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['response_code'] == 0:
            count = 0
            print("  > Baixando lote da API...")
            
            for i, item in enumerate(data['results']):
                print(f"    - Processando e traduzindo {i+1}/{len(data['results'])}...", end='\r')
                
                try:
            
                    q_text_final = translate_text(item['question'])
                    correct_final = translate_text(item['correct_answer'])
                    
                    if not q_text_final or not correct_final:
                        continue

                    inc_answers_final = []
                    valid_options = True
                    for inc in item['incorrect_answers']:
                        trad = translate_text(inc)
                        if not trad:
                            valid_options = False
                            break
                        inc_answers_final.append(trad)
                    
                    if not valid_options or not inc_answers_final:
                        continue

             
                    exists = session.query(Question).filter_by(question_text=q_text_final).first()
                    
                    if not exists:
                        q = Question(
                            category="Computação",
                            difficulty=item['difficulty'],
                            question_text=q_text_final,
                            correct_answer=correct_final,
                            incorrect_answers=json.dumps(inc_answers_final)
                        )
                        session.add(q)
                        count += 1
                
                except Exception as e_inner:
                 
                    continue
            
            try:
                session.commit()
                print(f"\n  [Sucesso] {count} novas questões salvas.")
            except Exception as e_db:
                session.rollback()
                print(f"\n  [Erro Banco] Rollback executado: {e_db}")
                
            return True
        else:
            print("  [Aviso] API retornou código de fim ou erro.")
            return False
            
    except Exception as e:
        print(f"  [Erro] Falha na conexão: {e}")
        return False

def seed_database():
    try:
        total = session.query(Question).count()
    except Exception:
        session.rollback()
        total = 0
        
    print(f"Questões atuais no banco: {total}")
    
    if total < 200:
        print("\n--- INICIANDO DOWNLOAD E TRADUÇÃO INTELIGENTE ---")
        for i in range(4): 
            print(f"\nLote {i+1} de 4...")
            success = fetch_and_translate_questions(50)
            if not success:
                break
            time.sleep(2) 
        print("\nCarga finalizada.")

# ==========================================
# 3. AUTENTICAÇÃO
# ==========================================
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
    except Exception as e:
        session.rollback()
        print(f"Erro no cadastro: {e}")
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
    except Exception as e:
        session.rollback()
        print(f"Erro no login: {e}")
        input("Enter...")
        return None

# ==========================================
# 4. GAMEPLAY
# ==========================================
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
        print("Erro ao buscar questões.")
        return
    
    if not questions:
        print("⚠️ Banco vazio. Reinicie o jogo para baixar questões.")
        input("Enter...")
        return

    score = 0
    for i, q in enumerate(questions):
        print(f"\n--- PERGUNTA {i+1} ---")
        print(f"[Nível: {q.difficulty}]")
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

# ==========================================
# 5. ANALYTICS
# ==========================================
def show_analytics(user):
    clear_screen()
    try:
        total = session.query(UserQuestionAttempt).filter_by(user_id=user.id).count()
        correct = session.query(UserQuestionAttempt).filter_by(user_id=user.id, is_correct=1).count()
        
        print(f"📊 ESTATÍSTICAS DE {user.username.upper()}")
        if total > 0:
            print(f"Acertos: {correct}/{total} ({(correct/total)*100:.1f}%)")
        else:
            print("Nenhum jogo registrado.")
            
    except Exception as e:
        session.rollback()
        print(f"Erro ao buscar dados: {e}")
        
    input("\nEnter para voltar...")

def show_ranking():
    clear_screen()
    print("🏆 TOP 10 JOGADORES")
    try:
        ranking = session.query(User.username, func.sum(UserQuestionAttempt.is_correct)).join(UserQuestionAttempt).group_by(User.id).order_by(func.sum(UserQuestionAttempt.is_correct).desc()).limit(10).all()
        
        for i, (name, pts) in enumerate(ranking):
            pts = pts if pts else 0
            print(f"{i+1}. {name} - {pts} pts")
    except Exception as e:
        session.rollback()
        print(f"Erro no ranking: {e}")
        
    input("\nEnter para voltar...")

# ==========================================
# 6. MENU PRINCIPAL
# ==========================================
def main_menu():
    session.rollback()
    init_db()
    seed_database()
    
    user = None
    
    while True:
        clear_screen()
        print("=== 🚀 TECH QUIZ MASTER (PT-BR) ===")
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