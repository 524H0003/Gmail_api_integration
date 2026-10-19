from backend.app.utils.Auth import auth
from backend.app.repositories.UserRepo import UserRepository
from backend.app.db.session import get_db_session


def create_user(username: str, email: str, password: str, name: str) -> None:
    hashed_password = auth.hash_password(password)

    # Get the actual session from the generator
    session = next(get_db_session())
    user_repo = UserRepository(session)

    user_repo.create(username, name, email, hashed_password)

    print(f"User {username} created successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create users or start Gmail watch.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create user command
    create_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_parser.add_argument("--username", required=True, help="Username")
    create_parser.add_argument("--name", required=True, help="Name")
    create_parser.add_argument("--email", required=True, help="Email")
    create_parser.add_argument("--password", required=True, help="Password")

    # Start watch command
    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.username, args.email, args.password, args.name)
