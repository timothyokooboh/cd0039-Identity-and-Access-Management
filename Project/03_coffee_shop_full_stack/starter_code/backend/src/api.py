import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES

@app.route("/drinks", methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    for item in drinks:
        item.recipe = item.recipe.replace("\'", "\"")
    drinks = [Drink.short(drink) for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drinks,
        "status": 200
    })


@app.route("/drinks-detail", methods=["GET"])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    for item in drinks:
        item.recipe = item.recipe.replace("\'", "\"")
    drinks = [Drink.long(drink) for drink in drinks]

    return jsonify({
        "status": 200,
        "drinks": drinks,
        "success": True
    })


@app.route("/drinks", methods=["POST"])
@requires_auth(permission="post:drinks")
def post_drinks(payload):
    error = False
    try:
        req_title = request.get_json()['title']
        req_recipe = request.get_json()['recipe']

        drink = Drink(title=req_title, recipe=str(req_recipe))
        drink.insert()
        drinks = Drink.query.filter_by(id = drink.id).all()
       
        for item in drinks:
            item.recipe = item.recipe.replace("\'", "\"")

        drinks = [Drink.long(drink) for drink in drinks]
        
        return jsonify({
            "status": 200,
            "success": True,
            "drinks": drinks
        })
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
        if (error):
            abort(422)
    



@app.route("/drinks/<id>", methods=["PATCH"])
@requires_auth(permission="patch:drinks")
def update_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)

    request_body = request.get_json()
    if ('title' in request_body):
        drink.title = request_body['title']
    
    if ('recipe' in request_body):
        drink.recipe = str(request_body['recipe'])

    drink.recipe = drink.recipe.replace("\'", "\"")
    drink.update()

    return jsonify({
        "success": True,
        "drinks": [drink.long()],
        "status": 200
    })


@app.route("/drinks/<id>", methods=["Delete"])
@requires_auth(permission="delete:drinks")
def delete_drinks(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    drink.delete()

    return jsonify({
        "status": 200,
        "success": True,
        "delete": drink.id
    })

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422



@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response