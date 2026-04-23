from app.services.usuario_service import *

if __name__ == "__main__":
    service = UsuarioService()
    
    # Test creating a user
    print("Creating a new user...")
    new_user = service.criar_usuario("Gabrielzão", "gabzão@example.com","12345")
    print(f"User created: {new_user.nome}, Email: {new_user.email}, Senha: {new_user.senha}, ID: {new_user.id}")