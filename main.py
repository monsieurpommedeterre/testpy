import os
import logging
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
from bson import ObjectId  # Add this to work with MongoDB ObjectIds

# Charger les variables depuis le fichier .env
load_dotenv()

# Configurer le module logging
logging.basicConfig(level=logging.DEBUG)

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG")

# Utiliser logging pour afficher les informations
logging.debug(f"MONGO_URI: {MONGO_URI}")
logging.debug(f"SECRET_KEY: {SECRET_KEY}")
logging.debug(f"DEBUG: {DEBUG}")

# Création de l'application FastAPI
app = FastAPI()

# # Connexion à MongoDB Atlas
# MONGO_URI = "mongodb+srv://admin:<db_password>@cluster0.rz7pv.mongodb.net/mydatabase?retryWrites=true&w=majority"
# MONGO_URI = MONGO_URI.replace("<db_password>", "admin")  # Remplace "TonMotDePasse" par ton mot de passe

client = AsyncIOMotorClient(MONGO_URI)
db = client.mydatabase  # Remplace "mydatabase" par le nom de ta base de données MongoDB

# Définir les résolveurs pour les types et les requêtes
query = QueryType()
mutation = MutationType()

@query.field("hello")
def resolve_hello(_, info):
    return "Hello, World!"

@query.field("getUser")
async def resolve_get_user(_, info, id):
    # Wrap the id as ObjectId before querying MongoDB
    user = await db.users.find_one({"_id": ObjectId(id)})
    if user:
        return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
    return None

@mutation.field("addUser")
async def resolve_add_user(_, info, name, email):
    try:
        # Créer un nouveau document utilisateur
        new_user = {"name": name, "email": email}
        result = await db.users.insert_one(new_user)

        # Récupérer l'utilisateur nouvellement créé avec son _id
        created_user = await db.users.find_one({"_id": result.inserted_id})
        if created_user:
            return {
                "id": str(created_user["_id"]),
                "name": created_user["name"],
                "email": created_user["email"],
            }
        else:
            raise Exception("Failed to retrieve the created user from the database.")
    except Exception as e:
        # Log the error and return a more detailed message if needed
        print(f"Error creating user: {str(e)}")
        raise Exception("Error while adding user to the database.")

# Schéma GraphQL
type_defs = """
    type Query {
        hello: String
        getUser(id: ID!): User
    }
    type User {
        id: ID!
        name: String!
        email: String!
    }
    type Mutation {
        addUser(name: String!, email: String!): User!
    }
"""

# IMPORTANT: Include both `query` and `mutation` in the schema
schema = make_executable_schema(type_defs, query, mutation)

# Ajout de la route GraphQL à FastAPI
app.add_route("/graphql", GraphQL(schema, debug=True if DEBUG == "True" else False))
