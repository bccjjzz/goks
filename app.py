from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # 데이터베이스 설정
db = SQLAlchemy(app)

# 데이터 : 정보
school_info = {
    "name": "광성고등학교",
}


food_prices = [
    {"name": "", "price": 3000},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500},
    {"name": "떡볶이", "price": 4000},
    {"name": "튀김", "price": 2500}
]

# 로그인 관리 설정
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# 데이터베이스 모델 : 사용자 정보
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Integer, default=1)  # 1: 일반 유저, 2: 어드민
    ip_address = db.Column(db.String(15))  # IP 주소 저장

# 데이터베이스 모델 : 축제 정보
class Festival(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)  # 날짜와 시간을 datetime 타입으로 저장

# 데이터베이스 모델 : 공지사항 정보
class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    read_count = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='notices')


# 데이터베이스 모델 : 부스 정보
class Booth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(50), nullable=False)


# 라우트 설정
@app.route('/')
def index():
    return render_template('index.html', school=school_info)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('로그인되었습니다.', 'success')
            return redirect(url_for('user'))
        else:
            flash('로그인 실패. 사용자 정보를 확인하세요.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        ip_address = request.remote_addr  # 클라이언트의 IP 주소 가져오기
        new_user = User(username=username, password=hashed_password, ip_address=ip_address)  # IP 주소 저장
        db.session.add(new_user)
        db.session.commit()
        flash('회원가입이 완료되었습니다. 로그인하세요.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 2:  # 어드민 역할인지 확인
        return "관리자만 접근할 수 있습니다."

    if request.method == 'POST':
        category = request.form.get('category')
        if category == 'notice':
            notice_title = request.form.get('title')
            notice_content = request.form.get('content')
            new_notice = Notice(title=notice_title, content=notice_content, author_id=current_user.id)  # author_id 설정
            db.session.add(new_notice)
            db.session.commit()
            flash('공지사항이 추가되었습니다.', 'success')
        elif category == 'booth':
            booth_name = request.form.get('name')
            booth_location = request.form.get('location')
            new_booth = Booth(name=booth_name, location=booth_location)
            db.session.add(new_booth)
            db.session.commit()
            flash('부스 정보가 추가되었습니다.', 'success')
        elif category == 'festival':
            festival_name = request.form.get('name')
            festival_datetime = request.form.get('datetime')  # 폼으로부터 날짜와 시간 정보 가져옴
            new_festival = Festival(name=festival_name, date=datetime.strptime(festival_datetime, '%Y-%m-%dT%H:%M'))
            db.session.add(new_festival)
            db.session.commit()
            flash('축제 정보가 추가되었습니다.', 'success')
        
        
        return redirect(url_for('admin'))

    notices = Notice.query.all()  # 모든 공지사항 정보를 가져옴

    # 유저 검색 및 권한 관리
    searched_user = None
    if request.method == 'POST':
        search_username = request.form.get('search_username')
        if search_username:
            searched_user = User.query.filter_by(username=search_username).first()

    return render_template('admin.html', notices=notices, searched_user=searched_user)


@app.route('/admin_change_role/<int:user_id>', methods=['POST'])
@login_required
def admin_change_role(user_id):
    if current_user.role != 2:
        return "관리자만 접근할 수 있습니다."
    
    new_role = int(request.form.get('new_role'))
    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()
    flash('사용자 권한이 변경되었습니다.', 'success')
    return redirect(url_for('admin'))


# 라우트 설정: 사용자 페이지
@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    if current_user.is_authenticated:
        notices = Notice.query.all()
        booths = [
            {"donga": "경제경영부", "name": "OX퀴즈", "location": "5-1 강의실"},
            {"donga": "공학연구부", "name": "공학 결과물 전시, RC카 체험", "location": "공학연구실"},
            {"donga": "과학의정석", "name": "타이다이 티셔츠", "location": "종합과학실1"},
            {"donga": "농구부", "name": "3x3 농구대회", "location": "체육관"},
            {"donga": "댄스부", "name": "댄스공연", "location": "대강당 (3부에)"},
            {"donga": "도서부", "name": "북카페", "location": "도서관"},
            {"donga": "또래상담부", "name": "wee카페", "location": "wee클래스"},
            {"donga": "만화애니메이션연구부", "name": "만화애니 전시", "location": "4-2 강의실"},
            {"donga": "문예부", "name": "삼행시 대회, 인생 문장 대회", "location": "도서관 앞 복도"},
            {"donga": "미디어컨텐츠부", "name": "인생광성컷", "location": "교수법연구실"},
            {"donga": "미술부", "name": "타투, 페이스페인팅", "location": "2층 로비"},
            {"donga": "수학부", "name": "암산왕", "location": "1-9반"},
            {"donga": "스포츠클라이밍부", "name": "맨몸운동 경진대회", "location": "운동장 철봉 앞"},
            {"donga": "시스템소프트웨어개발부", "name": "반응형 홈페이지 & 게임", "location": "공학연구실"},
            {"donga": "신문부", "name": "신문 퀴즈", "location": "1-10반"},
            {"donga": "아키텍처부", "name": "건축 모형 전시 및 퀴즈", "location": "2층 복도"},
            {"donga": "연극부", "name": "종이비행기", "location": "2층 복도"},
            {"donga": "영자신문부", "name": "하와이 보이즈", "location": "대회의실"},
            {"donga": "정치외교부", "name": "도전 골든벨", "location": "1-3반"},
            {"donga": "지구우주과학부", "name": "우리은하", "location": "종합과학실2"},
            {"donga": "피포페인팅부", "name": "피포페인팅 전시", "location": "4-1 강의실"},
            {"donga": "하리스뮤지컬중창단", "name": "뮤지컬 '영웅'", "location": "대강당 (3부에)"},
            {"donga": "하리스찬양단", "name": "밴드공연", "location": "대강당 (3부에)"},
            {"donga": "학교대표축구부", "name": "구속테스트와 축구 다트", "location": "운동장"},
        ]

        Fes = [
            {"name": "", "time": ""}
        ]
        
        read_notice_ids = session.get('read_notice_ids', [])  # 읽은 공지사항 ID 리스트

        if request.method == 'POST':
            update_notice_data(request.form, read_notice_ids)
        
        return render_template('user.html', user=current_user, notices=notices, food_prices=food_prices, booths=booths)
    return redirect(url_for('index'))

def update_notice_data(form_data, read_notice_ids):
    for notice in notices:
        read_count_field_name = f'notice-{notice.id}-read-count'
        new_read_count = int(form_data.get(read_count_field_name))
        if new_read_count > notice.read_count:  # 읽음 표시 업데이트
            notice.read_count = new_read_count
            if notice.id not in read_notice_ids:
                read_notice_ids.append(notice.id)
        
    session['read_notice_ids'] = read_notice_ids  # 세션에 읽은 공지사항 ID 리스트 저장
    db.session.commit()

# 라우트 설정: 사용자 정보 페이지
@app.route('/user_info', methods=['GET', 'POST'])
@login_required
def user_info():
    if current_user.is_authenticated:
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            hashed_password = generate_password_hash(new_password)
            current_user.password = hashed_password
            db.session.commit()
            flash('비밀번호가 변경되었습니다.', 'success')

        return render_template('user_info.html', user=current_user)
    return redirect(url_for('index'))



@app.route('/read_notice/<int:notice_id>', methods=['POST'])
@login_required
def read_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    notice.read_count += 1
    db.session.commit()
    return redirect(url_for('user'))


@app.route('/notice_detail/<int:notice_id>')
@login_required
def notice_detail(notice_id):
    selected_notice = Notice.query.get_or_404(notice_id)
    return render_template('notice_detail.html', selected_notice=selected_notice)


@app.route('/update_food_prices', methods=['POST'])
@login_required
def update_food_prices():
    if current_user.role == 2:  # 어드민 역할인지 확인
        for i in range(1, 4):  # 1부터 3까지
            field_name = f'food-{i}'
            new_price = int(request.form.get(field_name))
            food_prices[i - 1]['price'] = new_price

        flash('음식 가격이 업데이트되었습니다.', 'success')
    return redirect(url_for('user'))


@app.route('/update_booths', methods=['POST'])
@login_required
def update_booths():
    if current_user.role == 2:  # 어드민 역할인지 확인
        booths = Booth.query.all()
        for booth in booths:
            booth_name_field = f'booth-{booth.id}-name'
            booth_location_field = f'booth-{booth.id}-location'
            new_name = request.form.get(booth_name_field)
            new_location = request.form.get(booth_location_field)
            booth.name = new_name
            booth.location = new_location
        
        db.session.commit()
        flash('부스 정보가 업데이트되었습니다.', 'success')
    return redirect(url_for('admin'))


@app.route('/update_notice', methods=['POST'])
@login_required
def update_notice():
    if current_user.role == 2:  # 어드민 역할인지 확인
        for notice in notices:
            field_name = f'notice-{notice.id}-author'
            new_author = request.form.get(field_name)
            notice.author = new_author
            
            field_name = f'notice-{notice.id}-read-count'
            new_read_count = int(request.form.get(field_name))
            notice.read_count = new_read_count

        flash('공지사항이 업데이트되었습니다.', 'success')
    return redirect(url_for('user'))


@app.route('/edit_notice', methods=['POST'])
@login_required
def edit_notice():
    if current_user.role == 2:  # 어드민 역할인지 확인
        notice_id = int(request.form.get('notice_id'))
        new_title = request.form.get('title')
        new_content = request.form.get('content')
        notice = Notice.query.get(notice_id)
        if notice:
            notice.title = new_title
            notice.content = new_content
            db.session.commit()
            flash('공지사항이 수정되었습니다.', 'success')
        else:
            flash('공지사항을 찾을 수 없습니다.', 'danger')
    return redirect(url_for('admin'))  # 수정 후 관리자 페이지로 리디렉션


@app.route('/admin/search_user', methods=['POST'])
def admin_search_user():
    # 검색 기능 구현 및 처리
    return render_template('admin.html', searched_user=searched_user)


@app.route('/download/<filename>')
def download(filename):
    # 실제 파일 경로를 지정해주세요.
    file_path = '/home/ubuntu/goks/instance' + filename  # 예: 'static/downloads/' + filename
    
    try:
        # 파일을 읽어서 Response로 반환하면 다운로드 됩니다.
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found."


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html")


# 앱 실행
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 데이터베이스 테이블 생성
    app.run(host="0.0.0.0", port=80)

