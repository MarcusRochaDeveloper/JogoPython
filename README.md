# 🚀 Tech Quiz Master | SENAI Edition

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Database](https://img.shields.io/badge/SQLite-Local-green?style=for-the-badge&logo=sqlite)
![Context](https://img.shields.io/badge/SENAI-Dev%20Systems-red?style=for-the-badge)

> **Um jogo de perguntas e respostas via Terminal (CLI) desenvolvido para testar conhecimentos, desafiar colegas e descontrair nos laboratórios do SENAI.**
> <img width="771" height="574" alt="image" src="https://github.com/user-attachments/assets/ee79452f-a1d6-40ab-8e44-b317123fff7c" />


---

## 📖 Sobre o Projeto

O **Tech Quiz Master** nasceu da necessidade de criar uma dinâmica de aprendizado divertida e offline. Focado em alunos do curso Técnico em Desenvolvimento de Sistemas, ele permite que os jogadores testem seus conhecimentos em Lógica, POO, Banco de Dados, Redes, Hardware e muito mais.

O sistema roda localmente, utiliza um banco de dados SQLite para persistência e carrega questões personalizadas de um arquivo JSON, garantindo que o conteúdo esteja sempre alinhado com a grade curricular.

## ⚙️ Funcionalidades

* **🎮 Interface CLI Limpa:** Menus interativos, limpeza de tela automática e feedback visual.
* **🔒 Sistema de Login:** Criação de conta e autenticação de usuários (com hash de senha).
* **📊 Analytics:** Acompanhe seu desempenho com estatísticas de acertos e erros por matéria.
* **🏆 Ranking Global:** Veja quem são os Top 10 melhores alunos da turma.
* **📂 Banco de Questões Flexível:** As perguntas são carregadas de um arquivo `questoes.json`, facilitando a edição e adição de novos desafios.
* **💾 Persistência de Dados:** Histórico de tentativas salvo automaticamente via SQLAlchemy.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **ORM:** SQLAlchemy (Gerenciamento do Banco de Dados)
* **Banco de Dados:** SQLite (Arquivo `tech_quiz.db`)
* **Formato de Dados:** JSON

---

## 🚀 Como Rodar o Jogo

Siga os passos abaixo para executar o jogo no terminal:

### 1. Pré-requisitos
Certifique-se de ter o Python instalado. Você precisará instalar a biblioteca `SQLAlchemy`.

```bash
pip install sqlalchemy
