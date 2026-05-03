from flask import Flask, request, redirect, url_for, abort, g

from pathlib import Path
from http import HTTPStatus
from datetime import timedelta

from . extensions import db, bcrypt, mail, migrate, login_manager
from . blueprints.user import User
from . import blueprints


def create_app(test=False):
    app = Flask(__name__, instance_relative_config=True)
    if test:
        app.config.from_pyfile('test_config.py')
    else:
        app.config.from_pyfile('config.py')

    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

    instance_path = Path(app.instance_path)
    parent_directory = Path(instance_path.parent)
    if not parent_directory.is_dir():
        parent_directory.mkdir()
    
    if not instance_path.is_dir():
        instance_path.mkdir()
    
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.blueprint == 'api':
            abort(HTTPStatus.UNAUTHORIZED)
        return redirect(url_for('user.login'))
    
    
    # Register Blueprints
    modules = [
        getattr(blueprints, module) 
        for module in dir(blueprints) if hasattr(getattr(blueprints, module),"bp")
        ]

    menu_list = []
    for module in modules:
        app.register_blueprint(getattr(module, "bp"))
        if hasattr(module, "menu_label"):
            menu_list.append(getattr(module, "menu_label"))
        

    app.config['MENUS'] = menu_list

    # Initialize the database
    bcrypt.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app=app, db=db)
    
    return app
