import sqlite3 as sq


async def db_start():
    global db, cur

    db = sq.connect('new.db')
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS profile(username_id TEXT PRIMARY KEY, "
                "username TEXT, "
                "cmex_id TEXT DEFAULT 'СмехоЖдун', "
                "cmex_IQ INT DEFAULT 0)")

    cur.execute("CREATE TABLE IF NOT EXISTS diary(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                "question TEXT, "
                "response TEXT, "
                "profile_id TEXT, "
                "FOREIGN KEY (profile_id) REFERENCES profile (username_id))")

    db.commit()


async def create_profile(user_id, username):
    try:
        user = cur.execute(f"SELECT * FROM profile WHERE username_id == {user_id}").fetchone()
    except:
        user = None
    if not user:
        cur.execute(f"INSERT INTO profile (username_id, username) VALUES ({user_id}, '{username}')")
        db.commit()


async def get_profile_by_username(username):
    user_id = cur.execute(f"SELECT username_id FROM profile WHERE username == '{username}'").fetchone()
    return user_id

async def edit_cmex_id(user_id):
    cur.execute(f"UPDATE profile SET cmex_id = 'СмехоПрактик' WHERE username_id == {user_id}")
    db.commit()


async def get_cmex_id_iq(user_id):
    cmex_id = cur.execute(f"SELECT cmex_id FROM profile WHERE username_id == {user_id}").fetchone()
    cmex_iq = cur.execute(f"SELECT cmex_iq FROM profile WHERE username_id == {user_id}").fetchone()
    return cmex_id, cmex_iq


async def edit_cmex_iq(user_id, to_add):
    current_cmex_iq = cur.execute(f"SELECT cmex_iq FROM profile WHERE username_id == {user_id}").fetchone()
    # print(current_cmex_iq)
    cmex_to_add = current_cmex_iq[0] + to_add
    cur.execute(f"UPDATE profile SET cmex_iq = {cmex_to_add} WHERE username_id == {user_id}")
    db.commit()


async def create_diary(question, response, profile_id):
    cur.execute(f"INSERT INTO diary (question, response, profile_id) VALUES('{question}', '{response}', {profile_id})")
    db.commit()

# async def create_diary(question, response, profile_id):
#     # cur.execute(f"INSERT INTO diary (question, response, profile_id) VALUES ({question}, {response}, {profile_id})")
#     print(question, response, profile_id)
#     cur.execute(f"INSERT INTO diary (question, response, profile_id) VALUES({question}, {response}, {profile_id})")
#     db.commit()


async def get_diary(profile_id):
    diary_list = cur.execute(f"SELECT * FROM diary WHERE profile_id == {profile_id}")
    return diary_list

