from datetime import datetime
import google.oauth2.id_token
import random, imghdr
from flask import Flask, render_template, url_for, request, redirect
from google.cloud import datastore, storage
from google.auth.transport import requests
import local_constants

app = Flask(__name__)
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

#USER
def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity

def retrieveUserInfoByEmail(email):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('email', '=', email)
    result = list(query.fetch())
    return result[0]

def retrieveUserInfoByUsername(username):
    query = datastore_client.query(kind='UserInfo')
    query.add_filter('username', '=', username)
    result = list(query.fetch())
    return result[0]

def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'username': claims['email'].split("@")[0],
        'first_name': "",
        'last_name': "",
        'created_date': datetime.now(),
        'description': "",
        'avatar': "",
        'avatar_url': ""

    })
    datastore_client.put(entity)

def updateUserInfo(claims, first_name, last_name, created_date, description, avatar, avatar_url):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'email': claims['email'],
        'username': claims['email'].split("@")[0],
        'first_name': first_name,
        'last_name': last_name,
        'created_date': created_date,
        'description': description,
        'avatar': avatar,
        'avatar_url': avatar_url

    })
    datastore_client.put(entity)

#POST
def retrievePost(id):
    entity_key = datastore_client.key('PostInfo', id)
    entity = datastore_client.get(entity_key)
    return entity

def createPost(caption, image, user_info, created_date, like_count):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('PostInfo', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'caption': caption,
        'image': image,
        'image_url': "",
        'createdByUserEmail': user_info['email'],
        'createdByUserName': user_info['first_name'] + user_info['last_name'],
        'created_date': created_date,
        'like_count': like_count,
        'comments': []
    })
    datastore_client.put(entity)
    return entity

def updatePostImageUrl(post_entity, post_blob):
    post_entity.update({
        'image_url': post_blob
    })
    datastore_client.put(post_entity)

def getAllPostsForUser(user_email):
    query = datastore_client.query(kind='PostInfo')
    query.add_filter('createdByUserEmail', '=', user_email)
    result = list(query.fetch())
    return result

def getAllPostsFromDatastore():
    query = datastore_client.query(kind='PostInfo')
    result = list(query.fetch())
    return result

#FOLLOW
def addFollowProcess(followingUser, followedUser, followingDate):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('FollowInfo', id)
    entity = datastore.Entity(key = entity_key)

    entity.update({
        'followingUser': followingUser['email'],
        'followedUser': followedUser['email'],
        'followingDate': followingDate
    })
    datastore_client.put(entity)

def removeFollowProcess(user_info, followedUserEmail):
    query = datastore_client.query(kind='FollowInfo')
    query.add_filter('followingUser', '=', user_info['email'])
    result = list(query.fetch())

    for follow_info in result:
        if follow_info['followedUser'] == followedUserEmail:
            follow_info_key = datastore_client.key('FollowInfo', follow_info.id)
            datastore_client.delete(follow_info_key)


def getUsersFollowingList(claims):
    followingList = []
    query = datastore_client.query(kind='FollowInfo')
    query.add_filter('followingUser', '=', claims['email'])
    result = list(query.fetch())

    for value in result:
        followingList.append(value['followedUser'])

    return followingList

def getUsersFollowerList(claims):
    query = datastore_client.query(kind='FollowInfo')
    query.add_filter('followedUser', '=', claims['email'])
    result = list(query.fetch())
    return result

def getUsersFollowingFollowInfo(claims):
    query = datastore_client.query(kind='FollowInfo')
    query.add_filter('followingUser', '=', claims['email'])
    result = list(query.fetch())
    return result

def getUsersFollowerFollowInfo(claims):
    query = datastore_client.query(kind='FollowInfo')
    query.add_filter('followedUser', '=', claims['email'])
    result = list(query.fetch())
    return result

#COMMENTS
def createComment(postId, email, text, commentDate):
    id = random.getrandbits(63)
    entity_key = datastore_client.key('CommentInfo', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'postId': postId,
        'user': email,
        'text': text,
        'commentDate': commentDate
    })
    datastore_client.put(entity)
    return entity

def retrieveCommentByText(commentStr):
    query = datastore_client.query(kind='CommentInfo')
    query.add_filter('text', '=', commentStr)
    result = list(query.fetch())
    return result[0]

def addCommentToPost(post_entity, user_info, commentStr):
    userCommentDicList = post_entity['comments']
    userCommentDic = {}

    comment_entity = retrieveCommentByText(commentStr)
    username = user_info['username']
    userCommentDic[username] = comment_entity

    userCommentDicList.append(userCommentDic)

    post_entity.update({
        'comments': userCommentDicList
    })
    datastore_client.put(post_entity)

def updateLikesOfPost(postId):
    post = retrievePost(postId)
    like_count = int(post['like_count'])
    like = like_count + 1
    post.update({
        'like_count': like
    })
    datastore_client.put(post)

@app.route("/profile/<string:username>")
def profile(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    postUserDic = {}
    post_card = []
    sorted_post_card = []

    profile_user = retrieveUserInfoByUsername(username)
    allPostList = getAllPostsForUser(profile_user['email'])
    profile_user_following_numbers = len(getUsersFollowingList(profile_user))
    profile_user_follower_numbers = len(getUsersFollowerList(profile_user))

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            for post in allPostList:
                user_shares_post = retrieveUserInfoByEmail(post['createdByUserEmail'])
                postUserDic['user_info'] = user_shares_post
                postUserDic['post_info'] = post
                post_card.append(postUserDic)
                postUserDic = {}

            sorted_post_card = sorted(post_card, key=lambda x: x['post_info']['created_date'], reverse=True)

            usersFollowLists = getUsersFollowingList(user_info)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('profile.html', post_card = sorted_post_card, profile_user = profile_user, usersFollowLists = usersFollowLists, followings = profile_user_following_numbers, followers = profile_user_follower_numbers, user_info = user_info,  error_message=error_message)

@app.route("/create_user_info", methods = ['POST'])
def create_user_info():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            email_username = user_info['email'].split("@")[0]

            first_name = request.form['first_name']
            last_name = request.form['last_name']
            created_date = datetime.now()
            description = request.form['description']
            avatar = request.files.get('avatar')

            if not avatar or imghdr.what(avatar) not in ['png', 'jpeg', 'jpg']:
                return 'Please choose an avatar with valid format!'

            storage_client = storage.Client(project=local_constants.PROJECT_NAME)
            bucket = storage_client.get_bucket(local_constants.PROJECT_STORAGE_BUCKET)
            blob = bucket.blob(f"user/avatar/{email_username}/{avatar.filename}")
            blob.upload_from_file(avatar)

            avatar_blob = bucket.blob('user/avatar/{}/{}'.format(user_info['username'], avatar.filename))

            updateUserInfo(claims, first_name, last_name, created_date, description, avatar.filename, avatar_blob.public_url)

            return redirect('/')
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_info = user_info, error_message=error_message)


@app.route("/add_post", methods=['GET', 'POST'])
def add_post():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        if request.method == "POST":
            try:
                claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
                user_info = retrieveUserInfo(claims)
                email_username = user_info['email'].split("@")[0]

                caption = request.form['caption']
                postImage = request.files.get('postImage')

                if not postImage or imghdr.what(postImage) not in ['png', 'jpeg', 'jpg']:
                    return 'Please choose image for the post with valid format!'

                post = createPost(caption, postImage.filename, user_info, datetime.now(), 0)

                storage_client = storage.Client(project=local_constants.PROJECT_NAME)
                bucket = storage_client.get_bucket(local_constants.PROJECT_STORAGE_BUCKET)
                blob = bucket.blob(f"post/{post.id}/{postImage.filename}")
                blob.upload_from_file(postImage)

                post_blob = bucket.blob(f'post/{post.id}/{{}}'.format(post['image']))
                updatePostImageUrl(post, post_blob.public_url)

                return redirect(url_for('profile', username = user_info['username']))
            except ValueError as exc:
                error_message = str(exc)
        else:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            return render_template('add_post.html', user_info = user_info, error_message=error_message)

    return render_template('index.html', user_info = user_info, error_message=error_message)


@app.route("/increaseLikeCount/<int:postId>", methods=['POST'])
def increaseLikeCount(postId):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            updateLikesOfPost(postId)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

@app.route("/following_list/<string:username>")
def following_list(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    followingUsernames = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfoByUsername(username)

            followingList = getUsersFollowingFollowInfo(user_info)
            sorted_followingList = sorted(followingList, key=lambda x: x['followingDate'], reverse=True)

            for item in sorted_followingList:
                followingUsernames.append(item['followedUser'].split("@")[0])

        except ValueError as exc:
            error_message = str(exc)
    return render_template('following_list.html', followingUsernames = followingUsernames, user_info = user_info, error_message=error_message)

@app.route("/follower_list/<string:username>")
def follower_list(username):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    followerUsernames = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfoByUsername(username)

            followerList = getUsersFollowerList(user_info)
            sorted_followerList = sorted(followerList, key=lambda x: x['followingDate'], reverse=True)

            for item in sorted_followerList:
                followerUsernames.append(item['followingUser'].split("@")[0])

        except ValueError as exc:
            error_message = str(exc)
    return render_template('follower_list.html', followerUsernames = followerUsernames, user_info = user_info, error_message=error_message)

@app.route("/follow_user/<string:email>", methods=['POST'])
def follow_user(email):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            followed_user = retrieveUserInfoByEmail(email)

            addFollowProcess(user_info, followed_user, datetime.now())
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for('profile', username = followed_user['username']))


@app.route("/unfollow_user/<string:email>", methods=['POST'])
def unfollow_user(email):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            followed_user = retrieveUserInfoByEmail(email)

            addFollowProcess(user_info, followed_user, datetime.now())
            removeFollowProcess(user_info, email)
        except ValueError as exc:
            error_message = str(exc)
    return redirect(url_for('profile', username = followed_user['username']))


@app.route("/user_list", methods=['GET', 'POST'])
def user_list():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            query = datastore_client.query(kind='UserInfo')
            if request.form['name']:
                query.add_filter('first_name', '=', request.form['name'])

            result = list(query.fetch())

        except ValueError as exc:
            error_message = str(exc)
    return render_template('user_list.html', userList = result, user_info = user_info, error_message=error_message)


@app.route("/make_comment/<int:postId>", methods = ["POST"])
def make_comment(postId):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            post_entity = retrievePost(postId)
            commentStr = request.form['comment']

            comment_entity = createComment(post_entity.id, user_info['email'], commentStr, datetime.now())
            addCommentToPost(post_entity, user_info, commentStr)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    user_info = None
    postUserDic = {}
    post_card = []
    sorted_post_card = []
    allPostList = getAllPostsFromDatastore()

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            if user_info is None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)

            for post in allPostList:
                if (post['createdByUserEmail'] == user_info['email']) or (post['createdByUserEmail'] in getUsersFollowingList(user_info)):
                    user_shares_post = retrieveUserInfoByEmail(post['createdByUserEmail'])
                    postUserDic['user_info'] = user_shares_post
                    postUserDic['post_info'] = post
                    post_card.append(postUserDic)
                    postUserDic = {}


            sorted_post_card = sorted(post_card, key=lambda x: x['post_info']['created_date'], reverse=True)



        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', post_card = sorted_post_card, user_info = user_info, error_message=error_message)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
