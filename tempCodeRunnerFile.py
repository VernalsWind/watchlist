for i in range(1,n):
        name.append(User.query.get(i).username)