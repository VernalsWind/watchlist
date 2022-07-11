import imp
from itertools import count
from plistlib import UID
from pydoc import cli
from turtle import title
from unicodedata import name
from flask import Flask, render_template,request
from flask import redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
import os
from flask_admin import Admin,expose,BaseView
from flask_login import login_required, logout_user,current_user
from flask_login import UserMixin,login_user
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import click

from flask_admin.contrib.sqla import ModelView
app=Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

login_manager = LoginManager(app)  # 实例化扩展类
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'




app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

db=SQLAlchemy(app)

 

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值

class Movie(db.Model):
  id=db.Column(db.Integer,primary_key=True)
  title=db.Column(db.String(60))
  year = db.Column(db.String(4))  # 电影年份
class Subscribe(db.Model):
  id=db.Column(db.Integer,primary_key=True)
  uid=db.Column(db.Integer)
  mid =db.Column(db.Integer)



admin=Admin(app, name='后台管理界面', template_mode='bootstrap3')

class myAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return url_for('admin')     


admin.add_view(myAdminView(User, db.session))
admin.add_view(myAdminView(Movie, db.session))
admin.add_view(myAdminView(Subscribe, db.session))   
#主页，是查询全部电影和增加电影
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':  # 判断是否是 POST 请求
        # 获取表单数据
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)  # 创建记录
        db.session.add(movie)  # 添加到数据库会话
        db.session.commit()  # 提交数据库会话
        flash('Item created.')  # 显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页
    movies=Movie.query.all()
    return render_template('index.html',movies=movies)

#所有用户的查询
@app.route('/allUser')

def allUser():
    name=[]
    n=User.query.count()
    for i in range(1,n+1):
        a=User.query.get(i)
        name.append(a.username)
    
    return render_template('allUser.html',name=name)  
    






@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required 
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required 
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    subscribe=Subscribe.query.filter(Subscribe.mid==movie_id).all()
   
    db.session.delete(movie)  # 删除对应的记录
   
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页  

@app.route('/user/delete/<user_name>',methods=['POST'])
@login_required
def deleteuser(user_name):
    user=User.query.filter(User.username==user_name).first()
    
    subscribe=Subscribe.query.filter(Subscribe.uid==user.id).all()
    db.session.delete(user)
   
    db.session.commit()
    flash('Item deleted.')
   
    return redirect(url_for('allUser'))
    

@app.cli.command()
@click.option('--drop',is_flag=True)
def initdb(drop):
  if drop:
    db.drop_all()
  db.create_all()  
  click.echo('initiate successfully!')

@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    users=[{'username':'Grey Li','password_hash':generate_password_hash('dog')},
    {'username':'Derly Qi','password_hash':generate_password_hash('cat')}
    ]
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    subscribe=[
    {'uid':1,'mid':1},
    {'uid':1,'mid':2},
    {'uid':1,'mid':3},
    {'uid':2,'mid':3},
    {'uid':2,'mid':4},
    {'uid':2,'mid':5},
    {'uid':3,'mid':5},
    {'uid':3,'mid':6},
    {'uid':3,'mid':7},
    {'uid':4,'mid':7},
    {'uid':4,'mid':8},
    {'uid':4,'mid':9},
    {'uid':4,'mid':10},
    ]
    for u in users:
        user=User(username=u['username'],password_hash=u['password_hash'])
        db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    for s in subscribe:
       subscribe=Subscribe(uid=s['uid'],mid=s['mid'])
       db.session.add(subscribe)
    db.session.commit()
    click.echo('Done.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')    



@app.route('/register',methods=['GET','POST'])
def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user=User(username=username,password_hash=generate_password_hash    (password))
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))
            
        return render_template('login.html')
        
    
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.filter(User.username==username).first()
        # 验证用户名和密码是否一致
        if  user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('selflist',username=current_user.username))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')

#个人主页
@app.route('/login/<username>',methods=['GET', 'POST'])

def selflist(username):
    #根据传入的用户名进行搜索用户UID，进而搜索订阅SID，得到某用户的订阅电影列表
    #查询功能
    user=User.query.filter_by(username=username).first()
    subscribe=Subscribe.query.filter(Subscribe.uid==user.id).all()
    countsub=Subscribe.query.filter(Subscribe.uid==user.id).count()
    movies=[]
    for i in range(countsub):
        if Movie.query.filter(Movie.id==subscribe[i].mid).first():#一定记得判断！
            movies.append(Movie.query.filter(Movie.id==subscribe[i].mid).first())
       
    if request.method == 'POST':  # 判断是否是 POST 请求
        # 获取表单数据
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        user=User.query.filter_by(username=username).first()
        movie = Movie(title=title, year=year)  # 创建记录
        db.session.add(movie)  # 添加到数据库会话
        db.session.commit() 

        movie_current=Movie.query.filter(Movie.title==title).first()
        subself=Subscribe(mid=movie_current.id,uid=user.id)
        
        
        db.session.add(subself)#insert 功能，用户订阅电影
        db.session.commit() 
        flash('Item created.')  # 显示成功创建的提示
        #第二遍写，为了更新页面，是增加之后的再次查询，不是写错了
        user=User.query.filter_by(username=username).first()
        subscribe=Subscribe.query.filter(Subscribe.uid==user.id).all()
        countsub=Subscribe.query.filter(Subscribe.uid==user.id).count()
        movies=[]
        for i in range(countsub):
            if Movie.query.filter(Movie.id==subscribe[i].mid).first():
                movies.append(Movie.query.filter(Movie.id==subscribe[i].mid).first())
        return render_template('selflist.html',name=user.username,movies=movies)
    return render_template('selflist.html',name=user.username,movies=movies)

#登出
@app.route('/logout')
@login_required  # 用于视图保护
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页

#设置可以改用户名
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.username = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html') 






if __name__=='__main__':
  app.run()  
 