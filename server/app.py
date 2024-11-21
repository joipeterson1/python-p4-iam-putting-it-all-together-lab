#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        json = request.get_json()

        # Check for required fields
        required_fields = ['username', 'password', 'image_url', 'bio']
        missing_fields = [field for field in required_fields if field not in json]

        if missing_fields:
            return {'error': f"Missing fields: {', '.join(missing_fields)}"}, 422

        try:
            user = User(username=json['username'])
            user.password_hash = json['password']
            user.image_url = json['image_url']
            user.bio = json['bio']

            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id

            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return {'error': 'User could not be created.'}, 422

class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get('user_id')).first()
        if user:
            return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401
    
class Login(Resource):
    def post(self):
        username = request.get_json()['username']
        user = User.query.filter(User.username == username).first()
        password = request.get_json()['password']
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session['user_id']:
            session['user_id'] = None
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        if session['user_id']:
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        return {'error': 'Unauthorized'}, 401

    def post(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401

        json = request.get_json()
        required_fields = ['title', 'instructions', 'minutes_to_complete']

        missing_fields = [field for field in required_fields if field not in json]
        if missing_fields:
            return {'errors': {field: 'This field is required.' for field in missing_fields}}, 422

        user_id = session['user_id']
        try:
            recipe = Recipe(
                title=json['title'],
                instructions=json['instructions'],
                minutes_to_complete=json['minutes_to_complete'],
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)