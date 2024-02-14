from flask import Blueprint, render_template, redirect, url_for, request, abort, make_response
from flask_login import login_required, current_user

from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from anibase import db
from .model import engine, User, UserAnime, Anime, UserFollow

users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/')
def users_list():
    with Session(engine) as session:
        users_ = session.query(User).all()
    return render_template('users_list.html', users=users_)


@users.route('/<username>')
@login_required
def user_by_username(username):
    user_info = dict()
    with Session(engine) as session:
        u = session.query(User).where(User.username == username).first()
        user_id = u.id
        if u:
            user_info['user'] = u
        else:
            abort(404)
        user_anime_ids = session.execute(select(UserAnime.id_anime).
                                         where(UserAnime.id_user == user_id)).scalars()
        user_anime = session.query(Anime).where(Anime.mal_id.in_(user_anime_ids)).limit(20)
        user_info['user_anime'] = user_anime

        user_info['following'] = db.user_followings(u)

        if u.id != current_user.id:
            is_follow = session.query(UserFollow.id_user_follow).where(and_(UserFollow.id_user == current_user.id,
                                                                            UserFollow.id_user_follow == u.id)).scalar()
            print(is_follow)
            if is_follow:
                user_info['is_follow'] = True
            else:
                user_info['is_follow'] = False

    return render_template('user.html', **user_info)


@users.route('<username>/following', methods=['PATCH'])
@login_required
def follow_user(username):
    data = request.get_json()

    follow_id = data.get('follow_id')
    action = data.get('action')

    with Session(engine) as session:
        uf = session.query(UserFollow).where(and_(UserFollow.id_user == current_user.id,
                                                  UserFollow.id_user_follow == follow_id)
                                             ).first()
        if action == 'follow':
            session.add(UserFollow(id_user=current_user.id, id_user_follow=follow_id))
            session.commit()
        elif action == 'unfollow':
            session.delete(uf)
            session.commit()
        else:
            abort(500)

    return make_response('', 200)


@users.route('/<username>/animelist', methods=['POST'])
@login_required
def add_anime(username):
    id_anime = int(request.form.get('anime_id'))
    with Session(engine) as session:
        ua = session.query(UserAnime).where(and_(current_user.id == UserAnime.id_user,
                                                 UserAnime.id_anime == id_anime)).scalar()
        if not ua:
            session.add(UserAnime(id_user=current_user.id, id_anime=id_anime))
            session.commit()
    return redirect(url_for('anime.anime_by_id', id_=id_anime))
